# Step-by-step guide: South Park: The Stick of Truth, Switch → PC

*Español: [GUIDE.es.md](GUIDE.es.md)*

1. [Get your save off the Switch](#1-get-your-save-off-the-switch)
2. [Prepare the PC game](#2-prepare-the-pc-game)
3. [Convert](#3-convert)
4. [Install and play](#4-install-and-play)
5. [Steam Deck / Linux](#5-steam-deck--linux)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Get your save off the Switch

The Switch keeps saves in its internal memory, and Nintendo provides no way to copy them to a
computer. Even the Save Data Cloud of Nintendo Switch Online can only be downloaded back to a
Switch. You need a homebrew **save manager**, which runs on consoles with custom firmware
(Atmosphère).

> ⚠️ Running homebrew breaks Nintendo's terms of service and can get a console banned from online
> services. To keep the risk low, use **emuMMC**, keep the console **offline (airplane mode)**
> while it runs custom firmware, and back everything up first. If you have Nintendo Switch Online,
> upload the save to the **Save Data Cloud** first, as a safety net.

### Option A: your Switch can run custom firmware

Follow the community guide <https://switch.hacks.guide> to find out whether your console is
supported, and to set it up. Then use one of these:

| App | How | Where the files end up |
|---|---|---|
| **JKSV** (recommended) | Open JKSV › your user › *South Park: The Stick of Truth* › *New backup* | `sd:/JKSV/South Park…/<backup name>/` (or a `.zip`) |
| **Checkpoint** | Select the game › *Backup* | `sd:/switch/Checkpoint/saves/<game>/<backup name>/` |
| **DBI** | *Run MTP responder*, then browse the saves from your PC over USB | copy them anywhere on your PC |

Copy that folder (or zip) to your computer. It contains files like these:

```
SP-Sav-M-Save-Slot-001     manual saves
SP-Sav-M-Save-Slot-002
SP-Sav-A-Checkpoint-1      autosaves
SP-Sav-A-Checkpoint-2
SP-Sav-A-Checkpoint-3
SP-Opt                     settings (not needed)
.nx_save_meta.bin          JKSV metadata (not needed)
```

### Option B: your Switch can't be modded (patched model, Lite, OLED, Switch 2)

Use the console's **built-in save transfer** to move the save to a console that *can* run
custom firmware (a friend's, or a cheap second-hand original 2017 unit), then do option A there:

1. On your console: **System Settings › Data Management › Transfer Your Save Data ›
   Send Save Data to Another Console**.
2. On the other console (on the official system, not custom firmware), receive it.
3. Boot that console into custom firmware and back the save up with JKSV.

The transfer **moves** the save; it is deleted from the sending console. Upload it to the Save
Data Cloud first if you can, or transfer it back afterwards the same way.

---

## 2. Prepare the PC game

The converter needs **one save written by your PC game** to copy a few PC-only values from. These
are a memory address that is different for each version of the executable, and the encrypted
statistics block.

1. Install the game on Steam and start it.
2. Start a **new game** and play until the first save or checkpoint is written (a few minutes).
3. Quit the game.

The PC saves are in:

```
%USERPROFILE%\Documents\My Games\South Park - The Stick of Truth\save
```

If your *Documents* folder is in OneDrive, they are under `OneDrive\Documents` (or
`OneDrive\Documentos`). `sot-save-converter where` tells you which folder it found.

---

## 3. Convert

### Windows executable

Download `StickOfTruth-SaveConverter.exe` from the [Releases](../../../releases) page and **drag the folder or
zip from step 1 onto it**. It finds your PC save folder, uses your newest PC save as template, and
writes the converted files into a `PC saves` folder next to the input.

### Python

Python 3.8 or newer, no extra packages:

```bash
python -m sot_save_converter convert "path/to/JKSV backup"
```

Useful options:

```bash
# choose the template yourself
python -m sot_save_converter convert backup.zip --template "…/save/Save Slot 001.sav"

# write straight into the game's save folder (current content is zipped first)
python -m sot_save_converter convert backup.zip --install

# same, and remove the old .sav files (they stay in the backup zip)
python -m sot_save_converter convert backup.zip --install --clean
```

To check what a save contains (description, item count, Switch statistics):

```bash
python -m sot_save_converter info SP-Sav-M-Save-Slot-002 "Save Slot 002.sav"
```

---

## 4. Install and play

1. **Turn off Steam Cloud for the game**: Steam › Library › right-click *South Park™: The Stick of
   Truth™* › Properties › General › untick *Keep game saves in the Steam Cloud*. Otherwise Steam
   may replace the new files with the old ones from the cloud.
2. Back up the PC `save` folder (`--install` does this for you as `save_backup_<date>.zip`).
3. Copy the converted `.sav` files into the `save` folder (`--install` does this too).
4. Start the game › *Load game*. Your Switch saves show up with their original description, for
   example `LV 5, 02:10:33, Kupa Keep`.
5. Once it loads, **make a new save on PC**, quit and load that one. From now on you are playing
   on a save written by the PC game itself.
6. Turn Steam Cloud back on if you want to.

What to check while you play: inventory and equipment, the friends count, the quest journal,
abilities and perks. If something is off, see below.

---

## 5. Steam Deck / Linux

The game runs through Proton. Its save folder is inside the Proton prefix:

```
~/.steam/steam/steamapps/compatdata/213670/pfx/drive_c/users/steamuser/Documents/My Games/South Park - The Stick of Truth/save
```

In Desktop Mode, open a terminal (Konsole). SteamOS already ships Python 3:

```bash
python3 -m sot_save_converter convert ~/Downloads/jksv-backup --install
```

---

## 6. Troubleshooting

| Problem | What to do |
|---|---|
| `no Nintendo Switch saves found` | The files must keep their original names (`SP-Sav-M-Save-Slot-NNN`, `SP-Sav-A-Checkpoint-N`). To convert a renamed file, pass it directly as a file instead of a folder. |
| `no PC save found to use as template` | Make a save on PC first (step 2), or point to one with `--template`. |
| The game doesn't list the converted saves | Check that they are in the folder `where` reports (OneDrive!). Check that Steam Cloud didn't restore the old ones. |
| The game crashes or hangs when loading | Try a checkpoint instead of the manual save. Run `info` on both the Switch file and the converted file and [open an issue](../../../issues) with the output. Don't attach the saves publicly unless you are fine with that. |
| Wrong numbers on the statistics screen | Expected. That block is encrypted on PC and cannot be converted yet. |
| Something specific is wrong in game (missing item, quest stuck…) | Please [open an issue](../../../issues) describing it. That is exactly the feedback this project needs. |
