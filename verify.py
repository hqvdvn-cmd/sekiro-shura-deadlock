import argparse,hashlib,json,re,struct,zlib
from pathlib import Path

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().lower()

def check_native_abilities(game, manifest, resource="scripts/abilities.vdata_c"):
    """Read the stock VPK directly; addon search paths cannot shadow this check."""
    if resource not in {"scripts/abilities.vdata_c", "models/heroes_wip/yamato/clips/ui_hero_select.vnmclip_c"}:
        raise RuntimeError("Unexpected native resource")
    expected = manifest.get("compatibility_checks", {}).get(resource, {}).get("sha256")
    if expected is None:
        raise RuntimeError("Missing native checksum: " + resource)
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise RuntimeError("Invalid native abilities checksum in manifest")
    try:
        directory = game / "pak01_dir.vpk"
        if directory.is_symlink():
            raise ValueError("Stock VPK is a symlink")
        with directory.open("rb") as stream:
            signature, version, tree_size = struct.unpack("<III", stream.read(12))
            if signature != 0x55AA1234 or version not in (1, 2) or tree_size > 64 * 1024 * 1024:
                raise ValueError("Unsupported stock VPK header")
            header_size = 12 if version == 1 else 28
            stream.seek(header_size)
            tree = stream.read(tree_size)
        if len(tree) != tree_size:
            raise ValueError("Truncated stock VPK tree")
        cursor = 0
        def string():
            nonlocal cursor
            end = tree.index(b"\0", cursor)
            value = tree[cursor:end].decode("utf-8")
            cursor = end + 1
            return value
        found = None
        while extension := string():
            while folder := string():
                while name := string():
                    crc, preload_size, archive, offset, length, end = struct.unpack_from("<IHHIIH", tree, cursor)
                    cursor += 18
                    preload = tree[cursor:cursor + preload_size]
                    cursor += preload_size
                    if end != 0xFFFF or len(preload) != preload_size:
                        raise ValueError("Invalid stock VPK entry")
                    target_folder, target_file = resource.rsplit("/", 1)
                    target_name, target_extension = target_file.rsplit(".", 1)
                    if (extension, folder, name) == (target_extension, target_folder, target_name):
                        if found is not None:
                            raise ValueError("Duplicate native abilities resource")
                        found = (crc, preload, archive, offset, length)
        if cursor != len(tree) or found is None:
            raise ValueError("Native abilities resource not found")
        crc, preload, archive, offset, length = found
        if length > 64 * 1024 * 1024:
            raise ValueError("Unexpected native abilities size")
        payload_file = directory if archive == 0x7FFF else game / f"pak01_{archive:03d}.vpk"
        if payload_file.is_symlink():
            raise ValueError("Stock payload is a symlink")
        with payload_file.open("rb") as stream:
            stream.seek(offset + (header_size + tree_size if archive == 0x7FFF else 0))
            data = preload + stream.read(length)
        if len(data) != len(preload) + length or zlib.crc32(data) & 0xFFFFFFFF != crc:
            raise ValueError("Native abilities CRC or size mismatch")
        actual = hashlib.sha256(data).hexdigest()
    except (OSError, ValueError, struct.error) as exc:
        raise RuntimeError("Cannot verify native " + resource + ": " + str(exc)) from exc
    if actual != expected.lower():
        raise RuntimeError("Native " + resource + " changed after a game update. Rebuild before loading this mod.")
    return {"resource": resource, "sha256": actual, "status": "matches reference; runtime not tested"}

def check_selection_base(game, manifest):
    report = [check_native_abilities(game, manifest, resource) for resource in (
        "scripts/abilities.vdata_c", "models/heroes_wip/yamato/clips/ui_hero_select.vnmclip_c")]
    expected_paths = {f"resource/localization/{group}/{group}_{language}.txt"
        for group in ("citadel_heroes", "citadel_gc_hero_names") for language in ("english", "russian")}
    checks = manifest.get("native_localization_checks", {})
    if set(checks) != expected_paths:
        raise RuntimeError("Expected the four selection localization references")
    for name, expected in checks.items():
        path = game / name
        if path.is_symlink() or not re.fullmatch(r"[0-9a-f]{64}", expected) or sha(path) != expected:
            raise RuntimeError("Native localization changed: " + name)
        report.append({"resource": name, "sha256": expected, "status": "matches native file"})
    return report

def main():
    parser=argparse.ArgumentParser(description="Read-only package and native-resource verification")
    parser.add_argument('--game-dir',required=True,type=Path)
    args=parser.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'manifest.json').read_text())
    packages=manifest['packages']
    if len(packages)!=3 or {p['file'] for p in packages}!={'pak13_dir.vpk','pak14_dir.vpk','pak16_dir.vpk'}:
        raise RuntimeError('Expected exactly the three Shura components')
    for row in packages:
        path=root/row['file']
        if path.is_symlink() or not re.fullmatch('[0-9a-f]{64}',row['sha256']) or sha(path)!=row['sha256']:
            raise RuntimeError('Package differs: '+row['file'])
    print(json.dumps({'packages':'PASS','native':check_selection_base(args.game_dir.resolve(strict=True),manifest)},indent=2))

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,KeyError) as error:raise SystemExit('Refused: '+str(error))
