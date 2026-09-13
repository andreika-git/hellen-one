"""Regression checks for mixed KiCad 8 and KiCad 10 inner-layer exports."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class KicadGerberTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kicad gerbers ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.gerber = self.project / "gerber"
        shutil.copytree(ROOT / "tests/gerber", self.gerber)

    def write_layers(self, version):
        for layer in (1, 2):
            extension = layer if version == 10 else layer + 1
            (self.gerber / ("hellen1test-In%d_Cu.g%d" % (layer, extension))).write_text(
                "KiCad %d layer %d" % (version, layer))

    def run_script(self, script, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / script), *map(str, args)],
            cwd=ROOT, capture_output=True, text=True)

    def copy_frame(self):
        return self.run_script("copy_from_Kicad.py", "frames:hellen", self.project,
                               "../../gerber", "1test", "a", "4")

    def assert_layers(self, version):
        result = self.copy_frame()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        frame = self.project / "boards/hellen1test-a/frame"
        for layer in (1, 2):
            self.assertEqual((frame / ("1test.G%d" % layer)).read_text(),
                             "KiCad %d layer %d" % (version, layer))

    def test_legacy_export(self):
        self.write_layers(8)
        self.assert_layers(8)

    def test_current_export(self):
        self.write_layers(10)
        self.assert_layers(10)

    def test_mixed_exports_prefer_current_in_either_creation_order(self):
        for versions in ((8, 10), (10, 8)):
            with self.subTest(versions=versions):
                for path in self.gerber.glob("*-In*_Cu.g*"):
                    path.unlink()
                for version in versions:
                    self.write_layers(version)
                self.assert_layers(10)

    def test_incomplete_current_export_does_not_mix_versions(self):
        self.write_layers(8)
        (self.gerber / "hellen1test-In1_Cu.g1").write_text("new layer 1")
        result = self.copy_frame()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Incomplete internal Gerber layer pair", result.stdout)

    def test_cleanup_is_scoped_and_repeatable(self):
        self.write_layers(8)
        self.write_layers(10)
        unrelated = self.gerber / "other-In1_Cu.g2"
        unrelated.write_text("another board")
        before = {p.name: p.read_bytes() for p in self.gerber.iterdir()}
        result = self.run_script("cleanup_kicad_gerbers.py", self.gerber,
                                 "hellen1test", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.gerber.iterdir()})
        for _ in range(2):
            result = self.run_script("cleanup_kicad_gerbers.py", self.gerber, "hellen1test")
            self.assertEqual(result.returncode, 0, result.stderr)
        for obsolete in ("hellen1test-In1_Cu.g2", "hellen1test-In2_Cu.g3"):
            del before[obsolete]
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.gerber.iterdir()})
        self.assert_layers(10)

    def test_cleanup_preserves_legacy_only_export(self):
        self.write_layers(8)
        result = self.run_script("cleanup_kicad_gerbers.py", self.gerber, "hellen1test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_layers(8)


if __name__ == "__main__":
    unittest.main()
