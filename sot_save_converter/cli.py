"""Command line interface.

    sot-save-converter convert <switch saves...> [--template FILE] [--output DIR | --install]
    sot-save-converter info <files...>
    sot-save-converter where

Dragging a Switch save folder (or zip) onto the program runs ``convert`` with default options.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from . import __version__
from .convert import convert_save, is_switch_save_name, pc_name_for
from .formats import (PcSave, SaveFormatError, SwitchSave, detect_platform, read_switch_stats,
                      walk_state)

GAME_FOLDER = Path("My Games") / "South Park - The Stick of Truth" / "save"
STEAM_APP_ID = "213670"

STEAM_CLOUD_WARNING = (
    "IMPORTANT: Steam Cloud may put your old saves back. Before starting the game, open\n"
    "Steam > Library > right-click the game > Properties > General and turn off\n"
    "'Keep game saves in the Steam Cloud'. Turn it on again after you have saved in-game.")


# --------------------------------------------------------------------------- locating files

def _windows_documents() -> Optional[Path]:
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD),
                        ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]

        fid = GUID(0xFDD39AD0, 0x238F, 0x46AF,
                   (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
        p = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, None, ctypes.byref(p)) == 0:
            path = Path(p.value)
            ctypes.windll.ole32.CoTaskMemFree(p)
            return path
    except Exception:
        pass
    return None


def candidate_save_dirs() -> List[Path]:
    home = Path.home()
    docs = [_windows_documents(), home / "Documents", home / "OneDrive" / "Documents",
            home / "OneDrive" / "Documentos", home / "Documentos"]
    out = [d / GAME_FOLDER for d in docs if d]
    # Steam Deck / Linux (Proton)
    for steam in (home / ".steam" / "steam", home / ".local" / "share" / "Steam"):
        out.append(steam / "steamapps" / "compatdata" / STEAM_APP_ID / "pfx" / "drive_c" / "users"
                   / "steamuser" / "Documents" / GAME_FOLDER)
    seen, unique = set(), []
    for d in out:
        key = str(d).lower()
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def find_save_dir() -> Optional[Path]:
    for d in candidate_save_dirs():
        if d.is_dir():
            return d
    return None


def collect_switch_saves(sources: List[str]) -> List[Tuple[str, bytes]]:
    """Read Switch saves from files, folders (JKSV/Checkpoint dumps) and zip archives."""
    found: List[Tuple[str, bytes]] = []

    def consider(name: str, data: bytes, explicit: bool) -> None:
        if detect_platform(data) == "switch" and (explicit or is_switch_save_name(name)):
            found.append((name, data))

    for src in sources:
        p = Path(src)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() == ".zip":
                    found.extend(collect_switch_saves([str(f)]))
                elif f.is_file() and f.stat().st_size < 16 * 1024 * 1024:
                    consider(f.name, f.read_bytes(), False)
        elif p.is_file() and zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():
                    if not info.is_dir() and info.file_size < 16 * 1024 * 1024:
                        consider(info.filename, z.read(info), False)
        elif p.is_file():
            consider(p.name, p.read_bytes(), True)
        else:
            raise SystemExit(f"error: '{src}' does not exist")
    return found


def pick_template(explicit: Optional[str], save_dir: Optional[Path]) -> Tuple[Path, bytes]:
    if explicit:
        path = Path(explicit)
        data = path.read_bytes()
        if detect_platform(data) != "pc":
            raise SystemExit(f"error: template '{path}' is not a PC save")
        return path, data
    if save_dir and save_dir.is_dir():
        pcs = []
        for f in save_dir.glob("*.sav"):
            data = f.read_bytes()
            if detect_platform(data) == "pc":
                pcs.append((f.stat().st_mtime, f, data))
        if pcs:
            pcs.sort(key=lambda t: t[0], reverse=True)
            return pcs[0][1], pcs[0][2]
    raise SystemExit(
        "error: no PC save found to use as template.\n"
        "Start the game on PC, begin a new game, save once (or wait for the first checkpoint)\n"
        "and run this again, or pass one explicitly with --template \"path/to/Save Slot 001.sav\".")


def backup_folder(folder: Path) -> Optional[Path]:
    files = [f for f in folder.iterdir() if f.is_file()]
    if not files:
        return None
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = folder.parent / f"save_backup_{stamp}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    return target


# --------------------------------------------------------------------------- commands

def cmd_convert(args: argparse.Namespace) -> int:
    saves = collect_switch_saves(args.sources)
    if not saves:
        print("error: no Nintendo Switch saves found (expected files named "
              "SP-Sav-M-Save-Slot-NNN / SP-Sav-A-Checkpoint-N).", file=sys.stderr)
        return 2
    save_dir = Path(args.save_dir) if args.save_dir else find_save_dir()
    tpl_path, tpl_data = pick_template(args.template, save_dir)
    try:
        walk_state(PcSave.parse(tpl_data).stream, "pc")
    except SaveFormatError as e:
        raise SystemExit(f"error: template '{tpl_path}' could not be read: {e}")
    print(f"Template (PC save): {tpl_path}")

    if args.install:
        if not save_dir:
            raise SystemExit("error: PC save folder not found; use --save-dir or --output instead.")
        out_dir = save_dir
    else:
        out_dir = Path(args.output) if args.output else Path(args.sources[0]).resolve().parent / "PC saves"

    results = []
    for name, data in saves:
        pc_name, save_type = pc_name_for(name)
        try:
            out, report = convert_save(data, tpl_data, save_type)
        except SaveFormatError as e:
            print(f"  ! {name}: {e}", file=sys.stderr)
            continue
        results.append((pc_name, out, report))

    if not results:
        print("error: nothing could be converted.", file=sys.stderr)
        return 1
    names = [r[0] for r in results]
    if len(set(names)) != len(names):
        raise SystemExit("error: two inputs map to the same PC file name; convert them separately.")

    out_dir.mkdir(parents=True, exist_ok=True)
    if args.install:
        backup = backup_folder(out_dir)
        if backup:
            print(f"Backup of your current PC saves: {backup}")
        if args.clean:
            for f in out_dir.glob("*.sav"):
                f.unlink()
    for pc_name, out, report in results:
        target = out_dir / pc_name
        if target.exists() and not (args.install or args.force):
            raise SystemExit(f"error: '{target}' exists; use --force to overwrite.")
        target.write_bytes(out)
        print(f"  {pc_name:22} <- {report.description}  "
              f"({report.items} items, {report.variables} variables)")

    print(f"\n{len(results)} save(s) written to: {out_dir}")
    if not args.install:
        print("Copy them into your PC save folder"
              + (f":\n  {save_dir}" if save_dir else " (Documents/My Games/South Park - The Stick of Truth/save)."))
    print("\nNote: the in-game statistics screen (damage dealt, money collected, ...) is encrypted on PC,"
          "\nso it keeps the values of the template save. Story, quests, items, friends and level are converted.")
    print("\n" + STEAM_CLOUD_WARNING)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    rc = 0
    for f in args.files:
        data = Path(f).read_bytes()
        plat = detect_platform(data)
        print(f"{f}")
        try:
            if plat == "switch" and b"SVOP" in data[:0x20]:
                print("  Nintendo Switch settings file (SP-Opt) - not a save, not needed")
            elif plat == "switch":
                s = SwitchSave.parse(data)
                L = walk_state(s.stream, "switch")
                when = _dt.datetime.fromtimestamp(s.unix_time) if s.unix_time else "-"
                print(f"  platform     Nintendo Switch\n  description  {s.description}\n  saved        {when}")
                print(f"  items {L.item_count}, variables {L.variable_count}, NPC records {L.npc_count}")
                print("  statistics:")
                for name, val in read_switch_stats(s.stream, L):
                    print(f"    {name:26} {val:,.0f}")
            elif plat == "pc":
                s = PcSave.parse(data)
                L = walk_state(s.stream, "pc")
                when = (_dt.datetime(1601, 1, 1) + _dt.timedelta(microseconds=s.filetime // 10)
                        if s.filetime else "-")
                kind = "checkpoint" if s.save_type == 1 else "manual save"
                print(f"  platform     PC\n  description  {s.description}\n  saved        {when} UTC ({kind})")
                print(f"  items {L.item_count}, variables {L.variable_count}, NPC records {L.npc_count}")
            else:
                print("  not a Stick of Truth save")
                rc = 1
        except SaveFormatError as e:
            print(f"  could not be parsed: {e}")
            rc = 1
    return rc


def cmd_where(_args: argparse.Namespace) -> int:
    found = find_save_dir()
    print(f"PC save folder: {found}" if found else "PC save folder not found. Looked in:")
    if not found:
        for d in candidate_save_dirs():
            print(f"  {d}")
    return 0 if found else 1


# --------------------------------------------------------------------------- entry point

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sot-save-converter",
        description="Convert South Park: The Stick of Truth saves from Nintendo Switch to PC (Steam).")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("convert", help="convert Switch saves to PC saves")
    c.add_argument("sources", nargs="+", help="Switch save files, JKSV/Checkpoint folders or zip files")
    c.add_argument("-t", "--template", help="a PC save from your own game (default: newest PC save found)")
    c.add_argument("-o", "--output", help="output folder (default: 'PC saves' next to the input)")
    c.add_argument("--install", action="store_true",
                   help="write directly into the PC save folder (a backup zip is made first)")
    c.add_argument("--clean", action="store_true",
                   help="with --install: remove the existing .sav files (after the backup)")
    c.add_argument("--save-dir", help="PC save folder, if it is not detected automatically")
    c.add_argument("-f", "--force", action="store_true", help="overwrite files in --output")
    c.set_defaults(func=cmd_convert)

    i = sub.add_parser("info", help="show what a save contains")
    i.add_argument("files", nargs="+")
    i.set_defaults(func=cmd_info)

    w = sub.add_parser("where", help="show the detected PC save folder")
    w.set_defaults(func=cmd_where)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"convert", "info", "where", "-h", "--help", "--version"}
    drag_and_drop = bool(argv) and argv[0] not in commands
    if drag_and_drop:
        argv = ["convert"] + argv
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        rc = 0
    else:
        try:
            rc = args.func(args)
        except SystemExit as e:
            if isinstance(e.code, str):
                print(e.code, file=sys.stderr)
                rc = 1
            else:
                rc = e.code or 0
    if getattr(sys, "frozen", False) and (drag_and_drop or not argv):
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass
    return rc
