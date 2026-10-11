import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synthetic  # noqa: E402
from sot_save_converter.cli import collect_switch_saves  # noqa: E402
from sot_save_converter.convert import convert_save, convert_state, pc_name_for, rgba_to_png  # noqa: E402
from sot_save_converter.formats import (PcSave, SaveFormatError, STATS_BLOCK, SwitchSave,  # noqa: E402
                                    detect_platform, read_switch_stats, walk_state)


class LayoutTests(unittest.TestCase):
    def test_walk_switch_and_pc(self):
        sw = walk_state(synthetic.switch_stream(), "switch")
        pc = walk_state(synthetic.pc_stream(), "pc")
        self.assertEqual(sw.variable_count, 3)
        self.assertEqual(sw.item_count, 2)
        self.assertEqual(sw.npc_count, 1)
        self.assertEqual(pc.statlist_count, 3)
        self.assertEqual(pc.statlist_end, len(synthetic.pc_stream()))

    def test_switch_stats_are_readable(self):
        stream = synthetic.switch_stream(stats=[float(i) for i in range(15)])
        stats = read_switch_stats(stream, walk_state(stream, "switch"))
        self.assertEqual(stats[0], ("damage_received", 0.0))
        self.assertEqual(stats[-1], ("time_spent_in_game", 14.0))

    def test_rejects_garbage(self):
        with self.assertRaises(SaveFormatError):
            walk_state(b"\0" * 1024, "pc")
        self.assertIsNone(detect_platform(b"hello world"))


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.sw_stream = synthetic.switch_stream()
        self.tpl_stream = synthetic.pc_stream()
        self.out, self.report = convert_state(self.sw_stream, self.tpl_stream)
        self.sw = walk_state(self.sw_stream, "switch")
        self.pc = walk_state(self.out, "pc")
        self.tpl = walk_state(self.tpl_stream, "pc")

    def test_header_drops_switch_field(self):
        self.assertEqual(self.out[:4], self.sw_stream[:4])
        self.assertEqual(self.out[4:0x108], self.sw_stream[8:0x10C])

    def test_variables_are_repacked(self):
        for i, (name, value, vtype) in enumerate(synthetic.VARIABLES):
            rec = self.out[self.pc.variables + 8 + i * 56:self.pc.variables + 8 + (i + 1) * 56]
            self.assertEqual(rec[:4], synthetic.PC_VTABLE)
            self.assertEqual(rec[16:16 + len(name)], name.encode())
            self.assertEqual(struct.unpack_from("<fI", rec, 48), (value, vtype))

    def test_identical_sections_are_copied(self):
        self.assertEqual(self.out[self.pc.table:self.pc.variables],
                         self.sw_stream[self.sw.table:self.sw.variables])
        self.assertEqual(self.out[self.pc.rec28:self.pc.stats],
                         self.sw_stream[self.sw.rec28:self.sw.stats])

    def test_stats_block_comes_from_template(self):
        self.assertEqual(self.out[self.pc.stats:self.pc.stats + STATS_BLOCK],
                         self.tpl_stream[self.tpl.stats:self.tpl.stats + STATS_BLOCK])

    def test_switch_only_bytes_are_dropped(self):
        self.assertEqual(self.report.switch_only_bytes_dropped, len(synthetic.SWITCH_EXTRA))
        self.assertEqual(self.pc.statlist_end, len(self.out))

    def test_full_file_round_trip(self):
        sw_file = synthetic.switch_file(self.sw_stream, "LV 9, 09:09:09, Somewhere")
        out, report = convert_save(sw_file, synthetic.pc_file(self.tpl_stream), save_type=1)
        pc = PcSave.parse(out)
        self.assertEqual(pc.description, "LV 9, 09:09:09, Somewhere")
        self.assertEqual(pc.save_type, 1)
        self.assertEqual(pc.svei_extra, b"\x01\x02\x03\x04")
        self.assertEqual(pc.stream, self.out)
        self.assertTrue(pc.png.startswith(b"\x89PNG"))
        self.assertEqual(SwitchSave.parse(sw_file).description, "LV 9, 09:09:09, Somewhere")

    def test_pc_save_rejected_as_switch_input(self):
        with self.assertRaises(SaveFormatError):
            convert_save(synthetic.pc_file(self.tpl_stream), synthetic.pc_file(self.tpl_stream), 0)


class HelperTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(pc_name_for("SP-Sav-M-Save-Slot-002"), ("Save Slot 002.sav", 0))
        self.assertEqual(pc_name_for("JKSV/x/SP-Sav-A-Checkpoint-3"), ("Checkpoint 3.sav", 1))
        self.assertEqual(pc_name_for("whatever"), ("whatever.sav", 0))

    def test_png(self):
        png = rgba_to_png(bytes(range(256)) * 5, 16, 20)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", png[16:24])
        self.assertEqual((w, h), (16, 20))
        idat_len = struct.unpack(">I", png[33:37])[0]
        raw = zlib.decompress(png[41:41 + idat_len])
        self.assertEqual(len(raw), 20 * (1 + 16 * 3))

    def test_collect_from_folder_and_zip(self):
        sw_file = synthetic.switch_file(synthetic.switch_stream())
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "dump").mkdir()
            (d / "dump" / "SP-Sav-M-Save-Slot-001").write_bytes(sw_file)
            (d / "dump" / "SP-Opt").write_bytes(b"OPF_\x01\x02\x10\x00" + b"\0" * 40)
            (d / "dump" / ".nx_save_meta.bin").write_bytes(b"JKSV")
            with zipfile.ZipFile(d / "dump.zip", "w") as z:
                z.writestr("SP-Sav-A-Checkpoint-1", sw_file)
                z.writestr("SP-Opt", b"x")
            self.assertEqual([n for n, _ in collect_switch_saves([str(d / "dump")])],
                             ["SP-Sav-M-Save-Slot-001"])
            self.assertEqual([n for n, _ in collect_switch_saves([str(d / "dump.zip")])],
                             ["SP-Sav-A-Checkpoint-1"])


class CliTests(unittest.TestCase):
    def test_convert_command(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "SP-Sav-M-Save-Slot-001").write_bytes(synthetic.switch_file(synthetic.switch_stream()))
            (d / "Save Slot 001.sav").write_bytes(synthetic.pc_file(synthetic.pc_stream()))
            res = subprocess.run(
                [sys.executable, "-m", "sot_save_converter", "convert", str(d / "SP-Sav-M-Save-Slot-001"),
                 "--template", str(d / "Save Slot 001.sav"), "--output", str(d / "out")],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)
            out = d / "out" / "Save Slot 001.sav"
            self.assertTrue(out.exists())
            self.assertEqual(detect_platform(out.read_bytes()), "pc")

            info = subprocess.run([sys.executable, "-m", "sot_save_converter", "info", str(out)],
                                  cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(info.returncode, 0)
            self.assertIn("LV 3, 01:02:03, Example", info.stdout)


if __name__ == "__main__":
    unittest.main()
