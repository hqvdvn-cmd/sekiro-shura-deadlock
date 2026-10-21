[Русский](README.ru.md)

# Sekiro: Shura / Wolf for Yamato — beta

**Work in progress. This mod is not final and will be updated.**

Wolf in the Shura outfit replaces Yamato. The pack includes Kusabimaru, the red Mortal Blade, a black back-mounted sword, custom attack/ability effects and a Sekiro-inspired deflect. Shadow Transformation uses black hair and a glowing red eye. The selection name is Shura, with Shadows · Die · Twice tags.

[Download the beta](https://github.com/hqvdvn-cmd/sekiro-shura-deadlock/releases/tag/v29-beta)

## Install

Close Deadlock and your mod manager. Disable earlier Yamato replacements, then import `sekiro-shura-v29-beta-standalone-r2.zip` and enable its three components: model/UI/voices, Yamato effects and ultimate binding.

With **Dota 2 → Deadlock**, keep the model and effects enabled, disable Shura’s standalone ultimate-binding component, then import and enable `sekiro-shura-v29-beta-dota-patch-r2.zip`. Keep all five D2D components enabled. Use one Shura binding variant at a time.

For a manual install, copy the three VPK files into `game/citadel/addons`, preserving other mods. Enable `Game citadel/addons` above `Game citadel` in `gameinfo.gi` → `FileSystem` → `SearchPaths`; retain the game paths and explicit `Mod`/`Write` entries for both `citadel` and `core`. With D2D, replace only this pack’s `pak16_dir.vpk` and manifest with the compatibility ZIP version. Never overwrite an unrelated file with the same name.

To remove, disable this mod and its compatibility patch. Manual users should remove only files matching their downloaded manifest. Managers may renumber VPKs.

## Still being worked on

- Sword grip, selection pose and sheathing can still need adjustment.
- A brief blue flash can remain at parry startup. Shared movement/parry effects keep their native colors.
- The Japanese synthetic voices are a rough prototype; some clips sound choppy. Better voices are deferred.
- Names and tags cover English and Russian; other localization or Yamato mods can conflict.

Earlier combat, reload and ultimate checks were done in a combined local setup. V29’s hand and back-sword changes have compiled checks and are installed locally; fresh game acceptance and a clean standalone match are still pending.

![Selection screen from an earlier WIP build](assets/selection.png)
![Combat view from an earlier WIP build](assets/combat.png)

## After a game update

Extract the main ZIP and run `python verify.py --game-dir "YOUR_STEAM_PATH/Deadlock/game/citadel"` with Python 3.10+. The checker reads package hashes and selected native resources. It does not modify or launch the game. A pass does not cover every possible game change; managers do not run this checker automatically.

For reports, include a screenshot/clip, the action or pose, game build and other mods.

Original Sekiro assets: FromSoftware. Shura fixes: [sekijuan](https://www.nexusmods.com/sekiro/mods/1486). Deadlock: Valve. [Full credits](CREDITS.md).
