# Save file format

How *South Park: The Stick of Truth* (Obsidian's Onyx engine) stores saves on Nintendo Switch
and on PC, and what has to change to go from one to the other. Everything here was worked out
by comparing real saves from both platforms. All integers are little-endian. "Pad" fields contain
uninitialised memory: their values are meaningless and can be written as zero.

## 1. Files

| | Nintendo Switch | PC (Steam) |
|---|---|---|
| Manual saves | `SP-Sav-M-Save-Slot-NNN` | `Save Slot NNN.sav` |
| Autosaves | `SP-Sav-A-Checkpoint-N` | `Checkpoint N.sav` |
| Settings | `SP-Opt` (OPF with an `SVOP` chunk) | `user.ini` (next to the `save` folder) |
| Location | console storage (dump with JKSV/Checkpoint) | `Documents/My Games/South Park - The Stick of Truth/save` |

## 2. File layout

```
PC:      [SAVE header 0x98] [OPF container]
Switch:  [OPF container] [u64 unix time] [description, NUL-terminated] [zero padding]
```

### 2.1 PC `SAVE` header (0x98 bytes)

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | char[4] | `SAVE` |
| 0x04 | u32 | header version = 5 |
| 0x08 | u64 | save time, Windows FILETIME (UTC) |
| 0x10 | u32 | 0 = manual save, 1 = checkpoint |
| 0x14 | char[0x84] | description shown in the load menu, e.g. `LV 5, 02:10:33, Kupa Keep` (localised, NUL-terminated, rest is garbage) |

On Switch the same description and a Unix timestamp follow the OPF container instead.

### 2.2 OPF container

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | char[4] | `OPF_` |
| 0x04 | u8[4] | version: `01 02 10 00` on Switch, `01 02 04 00` on PC |
| 0x08 | u8[4] | pad |
| 0x0C | u32 | chunk count = 2 |
| 0x10 | {char[4] tag, u32 offset}[n] | `SVEI` at 0x20, `SVSY` after it (offsets relative to `OPF_`) |

Each chunk is `tag (4) | size (u32) | body (size + 4 bytes)`. The next chunk starts at
`offset + size + 12`.

### 2.3 `SVEI`: thumbnail

```
u16 version = 2 | u16 pad | u32 n | u32 x | data
```

* **PC:** `data` is a 320×176 RGB **PNG** of `n` bytes. `x` is 4 opaque bytes.
* **Switch:** `n` = 0x37000; `x` and 8 more bytes are followed by raw **RGBA** pixels
  (320×176×4 = `n` bytes, the last `n` bytes of the body).

### 2.4 `SVSY`: game state

```
u16 version = 1 | u16 pad | u32 type hash = 0xB3CCA06A | u32 len | stream (len + 4 bytes)
```

The stream is described below. Note that the declared `len` is 4 bytes shorter than the data.

## 3. Game state stream

Most of the stream is a raw memory dump of engine structures, which is why the Switch (64-bit,
AArch64) and PC (32-bit, x86) layouts differ. Sections, in order:

| # | Section | Switch | PC | Conversion |
|---|---|---|---|---|
| 1 | Header | 0x10C bytes | 0x108 bytes | drop the u32 at offset 4 |
| 2 | State table | `u32, u32 used`, 4096 × 72-byte entries | same | copy |
| 3 | Named variables | `u32 0, u32 n`, n × **64** bytes | n × **56** bytes | repack, see 3.1 |
| 4 | Small records | 128 × 28 bytes | same | copy |
| 5 | NPC records | `u32 n`, n × 72 bytes | same | copy |
| 6 | Inventory | `u32 1, u32 0xDEADBF19, u32 0, u32 n`, n × 416 bytes | same | copy |
| 7 | Serialized tail | byte-packed stream | same, except: | |
| 7a | · statistics | `u32 1` + 0x220 bytes **plain** | 0x220 bytes **encrypted** | see 3.2 |
| 7b | · closing list | `u32 n`, n × {u32 hash, u32 value, u32 type} | same | copy |
| 7c | · Switch extras | ~56 bytes after the list | — | drop |

`0xDEADBF19` is the engine's "empty hash" sentinel and shows up everywhere.

### 3.1 Named variables

Each record is a small-string object with a value: the story flags and counters (`0_b_…`,
`102_b_…`, quest scripts, etc.).

```
Switch (64 bytes)                         PC (56 bytes)
+00  void* vtable (8)                     +00  void* vtable (4)   ← constant per PC executable
+08  u32 hash                             +04  u32 hash
+0C  u32 length                           +08  u32 length
+10  u32 capacity (32)                    +0C  u32 capacity (32)
+14  u32 pad
+18  char name[32]                        +10  char name[32]
+38  f32 value                            +30  f32 value
+3C  u32 type                             +34  u32 type
```

The PC vtable pointer is copied from a PC save made with the same executable (it differs between game versions, e.g. `0x00B9F720` vs `0x00B9F750`).

### 3.2 Statistics block

15 records, `char name[32] + f32 value`, preceded by `u32 15`: `damage_received`,
`damage_given`, `damage_blocked`, `things_killed`, `players_killed`, `times_died`, `times_healed`,
`amount_healted`, `money_collected`, `money_from_sales`, `money_spent`, `quests_complete`,
`lore_found`, `time_spent_in_mp_session`, `time_spent_in_game`.

On PC the 0x220 bytes (34 blocks) are encrypted with a **16-byte block cipher in ECB mode**
(almost certainly AES): identical plaintext blocks give identical ciphertext, e.g. 16 zero bytes
→ `41c1a775831bd729b706d98129543322` and the first block (`0f000000` `damage_recei`) →
`c3838ac9c7693b814ca2fbee532bb0ac` in every PC save. The key is not known, and this project does
not analyse the game's executable to find it, so the converter copies this block from the PC
template.

The block is followed by `00000000 0a010000 07676858…`, which the converter uses to find it.

## 4. Things that are *not* checked by the game

* The pad bytes in the OPF header and chunk bodies (often called "checksums" at first sight)
  differ between otherwise identical saves and can be zero.
* There is no checksum over the file.

## 5. Unknowns

* The meaning of the extra Switch header field (values 1–2 seen) and of the ~56 trailing
  Switch-only bytes (they look like per-option flags).
* The PC statistics key (out of scope: see above).
* PC → Switch would need the reverse repacking plus a Switch vtable value and the plain
  statistics, which needs the key. Not implemented.
