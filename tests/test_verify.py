import importlib.util,hashlib,struct,tempfile,unittest,zlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('shura_verify',Path(__file__).resolve().parents[1]/'verify.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
ABILITY='scripts/abilities.vdata_c';CLIP='models/heroes_wip/yamato/clips/ui_hero_select.vnmclip_c'

def fixture(game,payloads):
    tree=bytearray();body=bytearray()
    for path,payload in payloads.items():
        folder,file=path.rsplit('/',1);name,extension=file.rsplit('.',1)
        for value in (extension,folder,name):tree.extend(value.encode()+b'\0')
        preload=payload[:2];tail=payload[2:]
        tree.extend(struct.pack('<IHHIIH',zlib.crc32(payload),len(preload),0x7fff,len(body),len(tail),0xffff));tree.extend(preload)
        tree.extend(b'\0\0');body.extend(tail)
    tree.extend(b'\0');header=struct.pack('<7I',0x55aa1234,2,len(tree),len(body),0,0,0)
    (game/'pak01_dir.vpk').write_bytes(header+tree+body)

class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.game=Path(self.temp.name)
        self.data={ABILITY:b'fresh-native-abilities',CLIP:b'fresh-static-native-selection'};fixture(self.game,self.data)
        self.manifest={'compatibility_checks':{n:{'sha256':hashlib.sha256(b).hexdigest()} for n,b in self.data.items()},'native_localization_checks':{}}
        for group in ('citadel_heroes','citadel_gc_hero_names'):
            for lang in ('english','russian'):
                path=f'resource/localization/{group}/{group}_{lang}.txt';file=self.game/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes((group+lang).encode())
                self.manifest['native_localization_checks'][path]=verify.sha(file)
    def test_six_native_resources_with_preload(self):
        rows=verify.check_selection_base(self.game,self.manifest)
        self.assertEqual({x['resource'] for x in rows},set(self.manifest['native_localization_checks'])|set(self.data))
    def test_changed_selection_clip_rejected(self):
        fixture(self.game,{**self.data,CLIP:b'new-native-selection'})
        with self.assertRaisesRegex(RuntimeError,'ui_hero_select.*changed'):verify.check_selection_base(self.game,self.manifest)
    def test_changed_localization_rejected(self):
        (self.game/next(iter(self.manifest['native_localization_checks']))).write_bytes(b'updated')
        with self.assertRaisesRegex(RuntimeError,'localization changed'):verify.check_selection_base(self.game,self.manifest)
    def test_missing_reference_rejected(self):
        self.manifest['compatibility_checks'].pop(CLIP)
        with self.assertRaisesRegex(RuntimeError,'Missing native checksum'):verify.check_selection_base(self.game,self.manifest)
    def test_corrupted_selection_payload_rejected(self):
        file=self.game/'pak01_dir.vpk';b=bytearray(file.read_bytes());b[-1]^=1;file.write_bytes(b)
        with self.assertRaisesRegex(RuntimeError,'CRC'):verify.check_selection_base(self.game,self.manifest)
    def test_extra_localization_path_rejected(self):
        self.manifest['native_localization_checks']['../other.txt']='0'*64
        with self.assertRaisesRegex(RuntimeError,'four selection'):verify.check_selection_base(self.game,self.manifest)

    def v1_fixture(self):
        self.manifest['version']='v1.0'
        self.data.update({path:('native-'+path).encode() for path in verify.RELOAD_RESOURCES})
        self.manifest['compatibility_checks']={n:{'sha256':hashlib.sha256(b).hexdigest()} for n,b in self.data.items()}
        fixture(self.game,self.data)

    def test_v1_checks_sixteen_native_resources(self):
        self.v1_fixture()
        self.assertEqual(len(verify.check_selection_base(self.game,self.manifest)),16)

    def test_v1_changed_reload_rejected(self):
        self.v1_fixture()
        fixture(self.game,{**self.data,verify.RELOAD_RESOURCES[0]:b'updated-reload'})
        with self.assertRaisesRegex(RuntimeError,'reload_idle.*changed'):verify.check_selection_base(self.game,self.manifest)

    def test_v1_missing_reload_reference_rejected(self):
        self.v1_fixture()
        self.manifest['compatibility_checks'].pop(verify.RELOAD_RESOURCES[0])
        with self.assertRaisesRegex(RuntimeError,'all twelve'):verify.check_selection_base(self.game,self.manifest)

if __name__=='__main__':unittest.main()
