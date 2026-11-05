"""Regression tests of stage-5 link resolution and legacy content protection."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts" / "check-subject-release.py"
spec = importlib.util.spec_from_file_location("release_gate", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ReleaseAcceptanceTests(unittest.TestCase):
    def test_original_text_is_unchanged_after_managed_insertion(self):
        previous = '# Question\n\n<nav class="exam-levels">L3 L2 L1</nav>\n'
        new = ('# Question\n\n' + mod.NAV_START + '\n'
               '<a href="../../subjects/nt/index.html#meaning-q01">По учебнику</a>\n'
               + mod.NAV_END + '\n\n'
               '<nav class="exam-levels">L3 L2 L1</nav>\n')
        mod.original_unchanged(previous, new, "sessions/01/q01-l3.md")
        with self.assertRaises(ValueError):
            mod.original_unchanged(previous, new + "\nAltered text", "sessions/01/q01-l3.md")

    def test_html_routes_use_markdown_sources_without_false_404(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("index.md", "subjects/nt/index.md", "subjects/nt/numbers.md",
                         "sessions/01/q01-l3.md", "subjects/nt/pdf/q01-l3.pdf"):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b"%PDF" if name.endswith("pdf") else b"Subject source")
            source = root / "subjects" / "nt" / "numbers.md"
            self.assertEqual("index.html", mod.resolve_link(source, "../../index.html", root))
            self.assertEqual("sessions/01/q01-l3.html",
                             mod.resolve_link(source, "../../sessions/01/q01-l3.html", root))
            self.assertEqual("subjects/nt/pdf/q01-l3.pdf",
                             mod.resolve_link(source, "pdf/q01-l3.pdf", root))
            self.assertIsNone(mod.resolve_link(source, "#number-q01", root))
            with self.assertRaises(ValueError):
                mod.resolve_link(source, "pdf/missing.pdf", root)


if __name__ == "__main__":
    unittest.main()
