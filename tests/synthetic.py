"""Builders for small *synthetic* save files used by the tests.

No real save data is shipped with this repository: these helpers produce files with the
same layout as the game's saves but with made-up contents.
"""
import random
import zlib
import struct

from sot_save_converter.convert import build_pc_save
from sot_save_converter.formats import (EMPTY_HASH, GAMESTATE_VERSION, ITEM_RECORD, NPC_RECORD,
                                    OPF_VERSION_SWITCH, REC28_COUNT, REC28_SIZE, STATE_TABLE_ENTRIES,
                                    STATE_TABLE_ENTRY, STATLIST_FIRST_HASH, STATS_COUNT,
                                    STATS_END_MARK, SVSY_TYPEHASH)

PC_VTABLE = struct.pack("<I", 0x00ABCDEF)
STAT_NAMES = ["damage_received", "damage_given", "damage_blocked", "things_killed",
              "players_killed", "times_died", "times_healed", "amount_healted",
              "money_collected", "money_from_sales", "money_spent", "quests_complete",
              "lore_found", "time_spent_in_mp_session", "time_spent_in_game"]
VARIABLES = [("0_b_example_flag", 1.0, 0), ("102_b_example_quest", 0.0, 0), ("example_counter", 7.0, 2)]


def _rng(seed):
    return random.Random(seed)


def _header(switch):
    h = struct.pack("<I", GAMESTATE_VERSION)
    if switch:
        h += struct.pack("<I", 2)
    h += struct.pack("<I", 0) + struct.pack("<I", 0x12345678) + b"example_level.opf".ljust(36, b"\0")
    size = 0x10C if switch else 0x108
    return h.ljust(size, b"\0")


def _table(rng):
    out = struct.pack("<II", 1, 2)
    for i in range(STATE_TABLE_ENTRIES):
        if i < 2:
            out += struct.pack("<II", rng.getrandbits(32), 0x524BBB87)
            out += struct.pack("<II", 5, 1) + b"\xff\xff\xff\xff\0\0\0\0" * 7
        else:
            out += b"\0" * STATE_TABLE_ENTRY
    return out


def _variables(switch):
    out = struct.pack("<II", 0, len(VARIABLES))
    for name, value, vtype in VARIABLES:
        raw = name.encode()
        fields = struct.pack("<III", zlib.crc32(name.encode()), len(raw), 32)
        body = raw.ljust(32, b"\0") + struct.pack("<fI", value, vtype)
        if switch:
            out += b"\x11\x22\x33\x44\x17\0\0\0" + fields + b"\0\0\x80\x3f" + body
        else:
            out += PC_VTABLE + fields + body
    return out


def _middle(rng):
    out = (b"\xff" * 16 + b"\0" * 12) * REC28_COUNT
    assert len(out) == REC28_COUNT * REC28_SIZE
    out += struct.pack("<I", 1) + bytes(rng.getrandbits(8) for _ in range(NPC_RECORD))
    out += struct.pack("<IIII", 1, EMPTY_HASH, 0, 2)
    out += bytes(rng.getrandbits(8) for _ in range(2 * ITEM_RECORD))
    return out


def _stats_plain(values):
    out = struct.pack("<I", STATS_COUNT)
    for name, v in zip(STAT_NAMES, values):
        out += name.encode().ljust(32, b"\0") + struct.pack("<f", v)
    return out


def _tail(rng, stats_block):
    out = b"\0\0\0\0\x02\0\0\0\0\0\x80\x3f\x0f\0\0\0player_created\0" + bytes(range(40))
    out += struct.pack("<I", 1) + stats_block + STATS_END_MARK + b"\x01" * 9
    entries = [STATLIST_FIRST_HASH + struct.pack("<II", 5, 1),
               struct.pack("<III", 0xCAFEBABE, 3, 3), struct.pack("<III", 0x0BADF00D, 0, 1)]
    out += struct.pack("<I", len(entries)) + b"".join(entries)
    return out


SWITCH_EXTRA = b"\x01" * 8 + b"\0" * 44 + b"\x0b\0\0\0"


def switch_stream(seed=1, stats=None):
    rng = _rng(seed)
    stats = stats or [float(i * 10) for i in range(STATS_COUNT)]
    return (_header(True) + _table(rng) + _variables(True) + _middle(rng)
            + _tail(rng, _stats_plain(stats)) + SWITCH_EXTRA)


def pc_stream(seed=2):
    rng = _rng(seed)
    encrypted = bytes(rng.getrandbits(8) for _ in range(4 + STATS_COUNT * 36))
    return _header(False) + _table(rng) + _variables(False) + _middle(rng) + _tail(rng, encrypted)


def switch_file(stream, description="LV 3, 01:02:03, Example", unix_time=1700000000):
    w, h = 320, 176
    pixels = bytes((x * 7 + y) & 0xFF for y in range(h) for x in range(w * 4))
    svei_body = struct.pack("<HHII", 2, 0, len(pixels), 0) + b"\0" * 8 + pixels
    svei = b"SVEI" + struct.pack("<I", len(svei_body) - 4) + svei_body
    length = len(stream) - 4
    svsy = b"SVSY" + struct.pack("<I", length + 12) + struct.pack("<HHII", 1, 0, SVSY_TYPEHASH, length) + stream
    opf = (b"OPF_" + OPF_VERSION_SWITCH + b"\0" * 4 + struct.pack("<I", 2)
           + b"SVEI" + struct.pack("<I", 0x20) + b"SVSY" + struct.pack("<I", 0x20 + len(svei)))
    data = opf + svei + svsy + struct.pack("<Q", unix_time) + description.encode() + b"\0"
    return data + b"\0" * 64


def pc_file(stream, description="LV 1, 00:00:07, Template"):
    png = b"\x89PNG\r\n\x1a\nnot-a-real-png"
    return build_pc_save(stream, png, b"\x01\x02\x03\x04", description, 1700000000, 0)
