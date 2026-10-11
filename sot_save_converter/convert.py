"""Nintendo Switch -> PC conversion."""
from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Tuple

from .formats import (
    SAVE_DESC_SIZE, SAVE_HEADER_SIZE, SAVE_HEADER_VERSION, SAVE_MAGIC, OPF_MAGIC,
    OPF_VERSION_PC, STATS_BLOCK, SVSY_TYPEHASH, VAR_RECORD_SWITCH, HEADER_SIZE_PC,
    HEADER_SIZE_SWITCH,
    PcSave, SaveFormatError, SwitchSave, pc_variable_vtable, read_switch_stats, walk_state,
)

FILETIME_UNIX_EPOCH = 11644473600


@dataclass
class ConversionReport:
    description: str
    variables: int
    npcs: int
    items: int
    switch_only_bytes_dropped: int
    switch_stats: List[Tuple[str, float]] = field(default_factory=list)


# --------------------------------------------------------------------------- game state

def convert_state(switch_stream: bytes, template_stream: bytes) -> Tuple[bytes, ConversionReport]:
    """Translate a Switch game state stream into the PC layout.

    ``template_stream`` is the game state of any save written by the PC game the result is
    meant for. It provides the PC vtable pointer and the encrypted statistics block.
    """
    sw = walk_state(switch_stream, "switch")
    pc = walk_state(template_stream, "pc")
    vtable = pc_variable_vtable(template_stream, pc)
    encrypted_stats = template_stream[pc.stats:pc.stats + STATS_BLOCK]
    s = switch_stream
    out = bytearray()

    # 1. header: the Switch build has one extra u32 at offset 4
    out += s[0:4] + s[8:HEADER_SIZE_SWITCH]
    assert len(out) == HEADER_SIZE_PC

    # 2. 4096-entry state table: identical layout
    out += s[sw.table:sw.variables]

    # 3. named variables: 64-byte records (8-byte pointer + padding) -> 56-byte records
    out += s[sw.variables:sw.variables + 8]
    for i in range(sw.variable_count):
        r = s[sw.variables + 8 + i * VAR_RECORD_SWITCH:sw.variables + 8 + (i + 1) * VAR_RECORD_SWITCH]
        #  switch: ptr64 | hash len cap | pad32 | char[32] value type
        #  pc:     ptr32 | hash len cap |         char[32] value type
        out += vtable + r[8:20] + r[24:64]

    # 4. 28-byte records, NPC records, inventory, serialized tail up to the statistics
    out += s[sw.rec28:sw.stats]

    # 5. statistics: plain text on Switch, encrypted with a key only the PC game knows.
    #    The template's (valid) encrypted block is reused.
    out += encrypted_stats

    # 6. rest of the tail up to the end of the closing list; the Switch-only bytes after
    #    it are dropped
    out += s[sw.stats + STATS_BLOCK:sw.statlist_end]

    result = bytes(out)
    walk_state(result, "pc")      # self check: the result must parse as a PC stream
    report = ConversionReport(
        description="",
        variables=sw.variable_count, npcs=sw.npc_count, items=sw.item_count,
        switch_only_bytes_dropped=len(s) - sw.statlist_end,
        switch_stats=read_switch_stats(s, sw),
    )
    return result, report


# --------------------------------------------------------------------------- thumbnail

def rgba_to_png(rgba: bytes, width: int, height: int) -> bytes:
    """Minimal RGB PNG encoder (standard library only)."""
    rows = bytearray()
    stride = width * 4
    for y in range(height):
        row = rgba[y * stride:(y + 1) * stride]
        rgb = bytearray(width * 3)
        rgb[0::3] = row[0::4]
        rgb[1::3] = row[1::4]
        rgb[2::3] = row[2::4]
        rows += b"\0" + rgb

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------- container

def build_pc_save(stream: bytes, png: bytes, svei_extra: bytes, description: str,
                  unix_time: float, save_type: int) -> bytes:
    """Assemble a complete PC ``.sav`` file."""
    length = len(stream) - 4
    svei = (b"SVEI" + struct.pack("<I", len(png) + 8)
            + struct.pack("<HHI", 2, 0, len(png)) + svei_extra + png)
    svsy = (b"SVSY" + struct.pack("<I", length + 12)
            + struct.pack("<HHII", 1, 0, SVSY_TYPEHASH, length) + stream)
    opf = (OPF_MAGIC + OPF_VERSION_PC + b"\0" * 4 + struct.pack("<I", 2)
           + b"SVEI" + struct.pack("<I", 0x20) + b"SVSY" + struct.pack("<I", 0x20 + len(svei)))
    filetime = int((unix_time + FILETIME_UNIX_EPOCH) * 10_000_000) if unix_time else 0
    desc = description.encode("utf-8")[:SAVE_DESC_SIZE - 1]
    header = (SAVE_MAGIC + struct.pack("<IQI", SAVE_HEADER_VERSION, filetime, save_type)
              + desc + b"\0" * (SAVE_DESC_SIZE - len(desc)))
    assert len(header) == SAVE_HEADER_SIZE
    return header + opf + svei + svsy


def convert_save(switch_data: bytes, template_data: bytes, save_type: int) -> Tuple[bytes, ConversionReport]:
    """Convert a complete Switch save file (bytes) into a PC save file (bytes)."""
    sw = SwitchSave.parse(switch_data)
    tpl = PcSave.parse(template_data)
    stream, report = convert_state(sw.stream, tpl.stream)
    png = rgba_to_png(sw.thumb_rgba, *sw.thumb_size)
    description = sw.description or "Switch save"
    out = build_pc_save(stream, png, tpl.svei_extra, description, sw.unix_time, save_type)
    report.description = description
    PcSave.parse(out)             # self check
    return out, report


# --------------------------------------------------------------------------- file names

_SLOT = re.compile(r"SP-Sav-M-Save-Slot-(\d+)$", re.I)
_CHECKPOINT = re.compile(r"SP-Sav-A-Checkpoint-(\d+)$", re.I)


def pc_name_for(switch_name: str) -> Tuple[str, int]:
    """Map a Switch save file name to (PC file name, save type)."""
    base = switch_name.replace("\\", "/").rsplit("/", 1)[-1]
    m = _SLOT.match(base)
    if m:
        return f"Save Slot {int(m.group(1)):03d}.sav", 0
    m = _CHECKPOINT.match(base)
    if m:
        return f"Checkpoint {int(m.group(1))}.sav", 1
    if base.lower().endswith(".sav"):
        base = base[:-4]
    return f"{base}.sav", 1 if "checkpoint" in base.lower() else 0


def is_switch_save_name(name: str) -> bool:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return bool(_SLOT.match(base) or _CHECKPOINT.match(base))


__all__ = ["convert_state", "convert_save", "build_pc_save", "rgba_to_png", "pc_name_for",
           "is_switch_save_name", "ConversionReport", "SaveFormatError"]
