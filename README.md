# South Park: The Stick of Truth — Switch to PC Save Converter

**Move your *South Park: The Stick of Truth* (*South Park: La Vara de la Verdad*) progress from
Nintendo Switch to PC (Steam / Steam Deck).**

*Español: [README.es.md](README.es.md)*

The game has no cross-save, and copying a Switch save into the PC save folder does nothing:
the PC game simply ignores it. Stick of Truth Save Converter translates the Switch save into the PC format so
you can keep playing where you left off.

```
SP-Sav-M-Save-Slot-002   ──►   Save Slot 002.sav
(Nintendo Switch)               (PC / Steam / Steam Deck)
```

## What gets transferred

| Transferred | Not transferred |
|---|---|
| Story and quest progress, choices | The **statistics screen** (damage dealt, money collected, time played…). On PC this block is encrypted with a key we don't have, so it keeps the values of your PC save. |
| Level, class, abilities, perks | Switch-only settings |
| Inventory, equipment, patches, artifacts, collectibles | |
| Friends, character appearance | |
| Location, NPC states, save thumbnail and description | |

Only **Switch → PC** is supported. PC → Switch is not implemented yet.

## Status

Early but working: a real mid-game Switch save was converted, loaded and played on the Steam
version. Please [report](../../issues) whether it worked for you, good or bad.

## What you need

1. **Your Switch save as files.** The Switch doesn't let you copy saves to a PC on its own, so you
   need a save manager such as **JKSV** or **Checkpoint**. Those apps only run on a Switch with
   custom firmware, but there's a way around that if yours isn't modded. See the
   [step-by-step guide](docs/GUIDE.md#1-get-your-save-off-the-switch).
2. **The game on PC**, started at least once, with **one save made on PC** (a new game that
   reaches the first checkpoint is enough). The converter copies a few PC-specific values from it.
3. Either the **Windows executable** from the [Releases](../../releases) page, or **Python 3.8+**.
   There are no other dependencies.

## Quick start

### Windows, no Python

1. Download `StickOfTruth-SaveConverter.exe` from [Releases](../../releases).
2. Drag the folder with your Switch save files (or the `.zip` JKSV made) **onto the exe**.
3. The converted saves are written to a `PC saves` folder next to it. Copy them into
   `Documents\My Games\South Park - The Stick of Truth\save`.
4. **Turn off Steam Cloud for the game first**: Steam › right-click the game › Properties ›
   General. Otherwise Steam may restore your old saves.

### With Python (Windows, macOS, Linux, Steam Deck)

```bash
git clone <this repository> && cd south-park-stick-of-truth-switch-to-pc-save-converter

# convert into ./PC saves (uses your newest PC save as template)
python -m sot_save_converter convert path/to/JKSV/backup

# …or convert and install directly (your current PC saves are zipped first)
python -m sot_save_converter convert path/to/JKSV/backup --install
```

The other commands:

```bash
python -m sot_save_converter info "Save Slot 002.sav" SP-Sav-M-Save-Slot-002   # inspect saves
python -m sot_save_converter where                                              # find the PC save folder
python -m sot_save_converter convert --help
```

| Option | Meaning |
|---|---|
| `-t, --template FILE` | PC save to take the PC-only values from (default: the newest PC save found) |
| `-o, --output DIR` | where to write the converted saves (default: `PC saves` next to the input) |
| `--install` | write straight into the PC save folder, after zipping its current content |
| `--clean` | with `--install`: delete the old `.sav` files (they are in the backup zip) |
| `--save-dir DIR` | PC save folder, if it isn't detected automatically |

Switch file names map to PC names: `SP-Sav-M-Save-Slot-NNN` → `Save Slot NNN.sav`,
`SP-Sav-A-Checkpoint-N` → `Checkpoint N.sav`. `SP-Opt` (settings) and `.nx_save_meta.bin` are ignored.

## How it works

Both versions store the game state as a raw dump of the game's memory, and most of it is
byte-for-byte identical. The differences come from the Switch being a 64-bit platform and the PC
build being 32-bit. The tool rewrites the affected structures, re-encodes the thumbnail as PNG and
adds the PC file header. The full format description is in [docs/FORMAT.md](docs/FORMAT.md).

## FAQ

**Will this get my Switch banned?** The converter only runs on your computer and never touches
the console. *Getting* the save off the Switch requires homebrew, which is against Nintendo's
terms. Read the [guide](docs/GUIDE.md) for ways to keep the risk low.

**Can I use someone else's PC save as template?** Use your own. The template must come from
the same PC game version you are going to play.

**The statistics screen shows wrong numbers.** That's expected (see the table above).
`sot-save-converter info SP-Sav-M-Save-Slot-NNN` prints your Switch statistics so you at least know
them.

**Does it work with The Fractured But Whole?** No. That's a different game with a different
engine.

## Contributing

Bug reports, test results and research are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
Please don't attach save files to public issues unless you are fine with them being public.

## Legal notes

- This is an **unofficial, non-commercial fan project**. It is not affiliated with, endorsed by or
  supported by Ubisoft, South Park Digital Studios, Obsidian Entertainment, Comedy Partners /
  Paramount, Nintendo or Valve. *South Park*, *The Stick of Truth* and the other names are
  trademarks of their owners, used here only to say which game the tool works with.
- It **is not a mod**: it does not modify, patch or redistribute the game, its executable or any
  of its assets, and it contains no game files. It only converts **save files that you created
  yourself** from one platform's format to the other's, for a game you own on both.
- The format was worked out by comparing save files. The game's program was not decompiled.
- Getting a save off a Switch requires homebrew, which goes against Nintendo's user agreement.
  That step is your decision and your responsibility; see the [guide](docs/GUIDE.md).
- No warranty (see the [license](LICENSE)). Keep backups of your saves.

## License

[MIT](LICENSE)
