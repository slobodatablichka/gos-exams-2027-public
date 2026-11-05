"""Subject navigation patch regression tests; no private material is embedded."""
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "link-subjects.py"
spec = importlib.util.spec_from_file_location("subject_navigation", MODULE)
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)


class SubjectNavigationTests(unittest.TestCase):
    def test_preserves_existing_article_text(self):
        old = '---\nlayout: default\n---\n\n# Article\n\n<nav class="exam-levels">Existing links</nav>\n'
        one = nav.replace_managed(
            old, nav.BEGIN, nav.END, "<nav>Return to subject</nav>",
            marker='<nav class="exam-levels"')
        self.assertIn(old.split('<nav class="exam-levels"')[0], one)
        self.assertIn("<nav>Return to subject</nav>", one)
        self.assertIn('<nav class="exam-levels">Existing links</nav>', one)
        twice = nav.replace_managed(
            one, nav.BEGIN, nav.END, "<nav>Return to subject</nav>",
            marker='<nav class="exam-levels"')
        self.assertEqual(one, twice)
        self.assertEqual(one.count(nav.BEGIN), 1)
        self.assertEqual(one.count(nav.END), 1)

    def test_rejects_unbalanced_or_missing_marker(self):
        with self.assertRaises(ValueError):
            nav.replace_managed(nav.BEGIN, nav.BEGIN, nav.END, "x", marker="missing")
        with self.assertRaises(ValueError):
            nav.replace_managed("article", nav.BEGIN, nav.END, "x", marker="missing")

    def test_cross_lesson_and_duplicate_semantics(self):
        model = {"slug": "ot", "title": "Священное Писание Ветхого Завета"}
        rows = [{"canonical_question": 5, "official_number": 5},
                {"canonical_question": 22, "official_number": 22}]
        routes = {
            5: {x: "sessions/02/q05-%s.html" % x for x in nav.LEVELS},
            22: {x: "sessions/08/q22-%s.html" % x for x in nav.LEVELS}
        }
        one = nav.subject_block(model, rows, 0, rows[0], "l3", routes, {5: [5, 14], 22: [22]})
        self.assertIn("№5/№14", one)
        self.assertIn("meaning-q05", one)
        self.assertIn("number-q05", one)
        self.assertIn("../../sessions/08/q22-l3.html", one)
        self.assertNotIn("← №", one)
        two = nav.subject_block(model, rows, 1, rows[1], "l2", routes, {5: [5, 14], 22: [22]})
        self.assertIn("../../sessions/02/q05-l2.html", two)
        self.assertNotIn("→</a>", two)

    def test_routes_are_relative_and_constrained(self):
        self.assertEqual("../../sessions/19/q23-nt-l1.html",
                         nav.link_from_session("sessions/19/q23-nt-l1.html"))
        with self.assertRaises(ValueError):
            nav.link_from_session("../secrets.txt")
        with self.assertRaises(ValueError):
            nav.link_from_session("https://example.org/a.html")


if __name__ == "__main__":
    unittest.main()
