"""
Readers, writers and layout walkers for South Park: The Stick of Truth save files.

Two platforms are supported:

* **Nintendo Switch** - files named ``SP-Sav-M-Save-Slot-NNN`` / ``SP-Sav-A-Checkpoint-N``
  as dumped by JKSV or Checkpoint. 64-bit memory layout.
* **PC (Steam / Windows)** - files named ``Save Slot NNN.sav`` / ``Checkpoint N.sav`` in
  ``Documents/My Games/South Park - The Stick of Truth/save``. 32-bit memory layout.

See ``docs/FORMAT.md`` for a full description of the formats.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- constants

OPF_MAGIC = b"OPF_"
OPF_VERSION_SWITCH = bytes([1, 2, 0x10, 0])
OPF_VERSION_PC = bytes([1, 2, 0x04, 0])
SAVE_MAGIC = b"SAVE"
SAVE_HEADER_VERSION = 5
SAVE_HEADER_SIZE = 0x98
SAVE_DESC_SIZE = SAVE_HEADER_SIZE - 0x14

SVSY_TYPEHASH = 0xB3CCA06A          # type hash at the start of every SVSY chunk
GAMESTATE_VERSION = 0x34            # first u32 of the game state stream
EMPTY_HASH = 0xDEADBF19             # "no entry" sentinel used all over the game state

STATE_TABLE_ENTRIES = 4096
STATE_TABLE_ENTRY = 72
VAR_RECORD_SWITCH = 64
VAR_RECORD_PC = 56
REC28_COUNT = 128
REC28_SIZE = 28
NPC_RECORD = 72
ITEM_RECORD = 416

STATS_COUNT = 15
STATS_RECORD = 36                                  # char name[32] + float value
STATS_BLOCK = 4 + STATS_COUNT * STATS_RECORD       # 0x220, 34 AES blocks on PC
STATS_PLAIN_PREFIX = struct.pack("<I", STATS_COUNT) + b"damage_recei"
STATS_END_MARK = bytes.fromhex("000000000a01000007676858")
STATLIST_FIRST_HASH = bytes.fromhex("97df9c1f")

THUMB_WIDTH = 320

HEADER_SIZE_PC = 0x108
HEADER_SIZE_SWITCH = 0x10C


class SaveFormatError(ValueError):
    """Raised when a file does not look like a Stick of Truth save."""


# --------------------------------------------------------------------------- helpers

def u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SaveFormatError(msg)


# --------------------------------------------------------------------------- OPF container

@dataclass
class Chunk:
    tag: bytes
    offset: int          # absolute offset of the chunk tag in the file
    size: int            # value of the size field
    body: bytes          # size + 4 bytes following the size field


def read_opf(data: bytes, base: int) -> Tuple[bytes, Dict[bytes, Chunk]]:
    """Return (version, chunks) of the OPF container starting at ``base``."""
    _require(data[base:base + 4] == OPF_MAGIC, "OPF_ container not found")
    version = data[base + 4:base + 8]
    count = u32(data, base + 12)
    _require(1 <= count <= 16, "implausible OPF chunk count")
    chunks: Dict[bytes, Chunk] = {}
    for i in range(count):
        tag, rel = struct.unpack_from("<4sI", data, base + 16 + 8 * i)
        off = base + rel
        _require(data[off:off + 4] == tag, f"chunk {tag!r} not at its table offset")
        size = u32(data, off + 4)
        body = data[off + 8:off + 8 + size + 4]
        _require(len(body) == size + 4, f"chunk {tag!r} is truncated")
        chunks[tag] = Chunk(tag, off, size, body)
    _require(b"SVEI" in chunks and b"SVSY" in chunks, "SVEI/SVSY chunks missing")
    return version, chunks


def svsy_stream(chunk: Chunk) -> bytes:
    """Game state stream of an SVSY chunk (declared length + 4 trailing bytes)."""
    _ver, _pad, typehash, length = struct.unpack_from("<HHII", chunk.body, 0)
    _require(typehash == SVSY_TYPEHASH, "unexpected SVSY type hash")
    stream = chunk.body[12:12 + length + 4]
    _require(len(stream) == length + 4, "SVSY stream truncated")
    return stream


# --------------------------------------------------------------------------- save files

@dataclass
class SwitchSave:
    stream: bytes
    thumb_rgba: bytes
    thumb_size: Tuple[int, int]
    unix_time: int
    description: str

    @classmethod
    def parse(cls, data: bytes) -> "SwitchSave":
        version, chunks = read_opf(data, 0)
        _require(version == OPF_VERSION_SWITCH, "not a Nintendo Switch save (OPF version)")
        svei = chunks[b"SVEI"].body
        npx = u32(svei, 4)
        _require(npx % (THUMB_WIDTH * 4) == 0 and npx <= len(svei), "unexpected thumbnail size")
        pixels = svei[len(svei) - npx:]
        size = (THUMB_WIDTH, npx // (THUMB_WIDTH * 4))
        svsy = chunks[b"SVSY"]
        end = svsy.offset + 8 + svsy.size + 4
        unix_time = struct.unpack_from("<Q", data, end)[0] if len(data) >= end + 8 else 0
        desc = data[end + 8:].split(b"\0", 1)[0].decode("utf-8", "replace") if len(data) > end + 8 else ""
        return cls(svsy_stream(svsy), pixels, size, unix_time, desc)


@dataclass
class PcSave:
    stream: bytes
    png: bytes
    svei_extra: bytes        # 4 opaque bytes stored before the PNG
    filetime: int
    save_type: int           # 0 = manual save, 1 = checkpoint
    description: str

    @classmethod
    def parse(cls, data: bytes) -> "PcSave":
        _require(data[:4] == SAVE_MAGIC, "not a PC save (SAVE header missing)")
        version, ftime, stype = struct.unpack_from("<IQI", data, 4)
        _require(version == SAVE_HEADER_VERSION, f"unsupported PC save header version {version}")
        desc = data[0x14:SAVE_HEADER_SIZE].split(b"\0", 1)[0].decode("utf-8", "replace")
        opf_version, chunks = read_opf(data, SAVE_HEADER_SIZE)
        _require(opf_version == OPF_VERSION_PC, "unexpected OPF version for a PC save")
        svei = chunks[b"SVEI"].body
        png_len = u32(svei, 4)
        return cls(svsy_stream(chunks[b"SVSY"]), svei[12:12 + png_len], svei[8:12],
                   ftime, stype, desc)


def detect_platform(data: bytes) -> Optional[str]:
    if data[:4] == SAVE_MAGIC:
        return "pc"
    if data[:4] == OPF_MAGIC and data[4:8] == OPF_VERSION_SWITCH:
        return "switch"
    return None


# --------------------------------------------------------------------------- game state layout

@dataclass
class StateLayout:
    """Offsets of every section of a game state stream."""
    platform: str
    header: int = 0
    table: int = 0
    table_used: int = 0
    variables: int = 0
    variable_count: int = 0
    rec28: int = 0
    npcs: int = 0
    npc_count: int = 0
    items: int = 0
    item_count: int = 0
    tail: int = 0
    stats: int = 0               # offset (in stream) of the 0x220-byte statistics block
    statlist: int = 0            # offset of the (count, entries...) list after the stats
    statlist_count: int = 0
    statlist_end: int = 0        # first byte after the list
    extra: Dict[str, int] = field(default_factory=dict)


def walk_state(stream: bytes, platform: str) -> StateLayout:
    """Locate every section of a game state stream. Raises SaveFormatError on mismatch."""
    sw = platform == "switch"
    L = StateLayout(platform)
    _require(u32(stream, 0) == GAMESTATE_VERSION, "unknown game state version")
    o = HEADER_SIZE_SWITCH if sw else HEADER_SIZE_PC

    L.table = o
    L.table_used = u32(stream, o + 4)
    _require(L.table_used <= STATE_TABLE_ENTRIES, "state table corrupt")
    o += 8 + STATE_TABLE_ENTRIES * STATE_TABLE_ENTRY

    L.variables = o
    L.variable_count = u32(stream, o + 4)
    _require(0 < L.variable_count < 20000, "variable table corrupt")
    o += 8 + L.variable_count * (VAR_RECORD_SWITCH if sw else VAR_RECORD_PC)

    L.rec28 = o
    o += REC28_COUNT * REC28_SIZE

    L.npcs = o
    L.npc_count = u32(stream, o)
    _require(L.npc_count < 4096, "NPC table corrupt")
    o += 4 + L.npc_count * NPC_RECORD

    L.items = o
    _require(u32(stream, o + 4) == EMPTY_HASH, "inventory header not found")
    L.item_count = u32(stream, o + 12)
    _require(L.item_count < 10000, "inventory corrupt")
    o += 16 + L.item_count * ITEM_RECORD
    _require(o < len(stream), "stream ends inside the inventory")

    L.tail = o
    tail = stream[o:]
    mark = tail.find(STATS_END_MARK)
    _require(mark > STATS_BLOCK, "statistics block not found")
    L.stats = o + mark - STATS_BLOCK
    _require(u32(stream, L.stats - 4) == 1, "statistics block header not found")
    if sw:
        _require(stream[L.stats:L.stats + len(STATS_PLAIN_PREFIX)] == STATS_PLAIN_PREFIX,
                 "Switch statistics block is not plain text")

    # (count, [hash, value, type] * count) list that closes the PC stream
    best = None
    start = L.stats + STATS_BLOCK
    pos = stream.find(STATLIST_FIRST_HASH, start)
    while pos != -1:
        cnt = u32(stream, pos - 4)
        end = pos + cnt * 12
        if 0 < cnt < 1024 and end <= len(stream):
            best = (pos - 4, cnt, end)
        pos = stream.find(STATLIST_FIRST_HASH, pos + 1)
    _require(best is not None, "closing statistics list not found")
    L.statlist, L.statlist_count, L.statlist_end = best
    return L


def read_switch_stats(stream: bytes, layout: StateLayout) -> List[Tuple[str, float]]:
    """Plain-text statistics stored in a Switch save (encrypted on PC)."""
    out = []
    base = layout.stats + 4
    for i in range(STATS_COUNT):
        rec = stream[base + i * STATS_RECORD:base + (i + 1) * STATS_RECORD]
        name = rec[:32].split(b"\0", 1)[0].decode("ascii", "replace")
        out.append((name, struct.unpack_from("<f", rec, 32)[0]))
    return out


def pc_variable_vtable(stream: bytes, layout: StateLayout) -> bytes:
    """The 32-bit vtable pointer written in front of every PC variable record."""
    first = stream[layout.variables + 8:layout.variables + 12]
    for i in range(layout.variable_count):
        off = layout.variables + 8 + i * VAR_RECORD_PC
        _require(stream[off:off + 4] == first, "template variable records are inconsistent")
    return first
