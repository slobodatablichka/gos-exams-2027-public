"""Regression tests for scripts/build-subjects.py; use synthetic source, no private data."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build-subjects.py"
spec = importlib.util.spec_from_file_location("subject_builder", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class SubjectGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.private = root / "private"
        self.public = root / "public"
        self.out = root / "output"
        (self.private / "planning").mkdir(parents=True)
        sections = [
            {"id": "intro", "title": "Введение", "official_numbers": list(range(1, 14))},
            {"id": "end", "title": "Продолжение", "official_numbers": list(range(14, 26))},
        ]
        self.topics = []
        for n in range(1, 26):
            c = {7: 1, 16: 6}.get(n, n)
            statement = "Официальная формулировка экзаменационного вопроса %s о Предании и Церкви." % c
            route_prefix = "sessions/19/q%02d" % c
            urlmap = {}
            for level in builder.LEVELS:
                # Simulate mixed lesson number q23 where canonical public file is qualified.
                actual = route_prefix + ("-dogmatics" if c == 23 else "") + "-" + level
                file = self.public / (actual + ".md")
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("# Публичная статья\nТекст ответа.", encoding="utf-8")
                urlmap[level] = route_prefix + "-" + level + ".html"
                manuscript = self.private / "materials" / "dogmatics" / level / ("q%02d.md" % c)
                manuscript.parent.mkdir(parents=True, exist_ok=True)
                manuscript.write_text(
                    "# Догматическое богословие\n\n"
                    "> Официальная формулировка вопроса.\n\n"
                    "Проверка русского текста: Церковь, Евхаристия и Пресвятая Троица.\n\n"
                    "## Подраздел\n\n**Вера** и жизнь.\n", encoding="utf-8")
            self.topics.append({
                "official_number": n,
                "official_question": statement,
                "semantic_rank": n,
                "section_id": "intro" if n <= 13 else "end",
                "canonical_question": c,
                "topic_id": "dogmatics-q%02d" % c,
                "session": 19,
                "quality": "approved",
                "site": "published",
                "level_urls": urlmap,
            })
        model = {
            "schema_version": 1, "slug": "dogmatics", "subject": "ДБ",
            "title": "Догматическое богословие", "sections": sections, "topics": self.topics,
        }
        self.config = self.private / "planning" / "subject-order-dogmatics.json"
        self.config.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")

    def test_25_positions_23_canonical_and_mixed_routes(self):
        model, urls = builder.read_model(self.private, self.public, "dogmatics")
        self.assertEqual(25, len(model["topics"]))
        self.assertEqual(23, len({r["canonical_question"] for r in model["topics"]}))
        self.assertEqual("sessions/19/q23-dogmatics-l3.html", urls[23]["l3"])
        self.assertEqual("sessions/19/q01-l3.html", urls[7]["l3"])
        html = builder.page_markdown(model, urls)
        self.assertIn('data-sort-panel="meaning"', html)
        self.assertIn('data-sort-panel="number"', html)
        self.assertIn("pdf/q01-l3.pdf", html)
        self.assertIn("subject-generator: managed", html)
        self.assertIn("25 официальных номеров", html)
        self.assertIn('id="meaning-q01"', html)
        self.assertIn('id="number-q25"', html)
        self.assertIn('href="#meaning-q02"', html)
        self.assertIn('href="../../sessions/19/index.html"', html)
        self.assertIn('href="numbers.html"', html)
        number_page = builder.numbers_markdown(model, urls)
        self.assertIn('id="number-q01"', number_page)
        self.assertIn('id="number-q25"', number_page)
        self.assertNotIn('data-sort-panel', number_page)


    def test_no_unapproved_or_missing_source(self):
        self.topics[0]["quality"] = "todo"
        self.config.write_text(json.dumps({
            "schema_version": 1, "slug": "dogmatics",
            "sections": [{"id": "intro", "title": "Введение", "official_numbers": list(range(1,14))},
                         {"id": "end", "title": "Продолжение", "official_numbers": list(range(14,26))}],
            "topics": self.topics
        }, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(ValueError):
            builder.read_model(self.private, self.public, "dogmatics")

    def test_real_pdf_build_and_cyrillic(self):
        builder.build(self.private, self.public, self.out, ["dogmatics"], True)
        folder = self.out / "subjects" / "dogmatics"
        self.assertTrue((folder / "index.md").is_file())
        self.assertTrue((folder / "numbers.md").is_file())
        import json
        manifest = json.loads((folder / "pdf-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(23, manifest["canonical_count"])
        self.assertEqual(72, manifest["pdf_count"])
        self.assertFalse((folder / "pdf" / "q07-l3.pdf").exists())
        self.assertFalse((folder / "pdf" / "q16-l2.pdf").exists())
        self.assertTrue((self.out / "subjects" / "index.md").is_file())
        for level in builder.LEVELS:
            whole = (folder / "pdf" / (level + ".pdf"))
            self.assertTrue(whole.is_file())
            self.assertGreater(whole.stat().st_size, 1000)
            self.assertTrue(whole.read_bytes().startswith(b"%PDF"))
            self.assertTrue((folder / "pdf" / ("q23-" + level + ".pdf")).is_file())
            from pypdf import PdfReader
            reader = PdfReader(str(whole))
            combined = " ".join((p.extract_text() or "") for p in reader.pages[:4])
            self.assertIn("Указатель официальных номеров", combined)
            self.assertIn("Оглавление", combined)
            self.assertGreater(len(reader.outline), 2)


    def test_historical_source_names_and_folders(self):
        """Old layouts remain valid; mixed RPC/Liturgics resolve explicitly."""
        row = dict(self.topics[0])
        row["source_folder"] = "irpc"
        row["source_file"] = "q01.md"
        self.assertEqual(
            self.private / "materials" / "irpc" / "l2" / "q01.md",
            builder.source_path(self.private, "rpc", row, "l2"))
        row["source_folder"] = "liturgics"
        row["source_file"] = "l-01.md"
        self.assertEqual(
            self.private / "materials" / "liturgics" / "l3" / "l-01.md",
            builder.source_path(self.private, "liturgics", row, "l3"))
        row["source_file"] = "../q01.md"
        with self.assertRaises(ValueError):
            builder.source_path(self.private, "liturgics", row, "l3")
        row["source_file"] = "l-02.md"
        with self.assertRaises(ValueError):
            builder.source_path(self.private, "liturgics", row, "l3")


if __name__ == "__main__":
    unittest.main()
