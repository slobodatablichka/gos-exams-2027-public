#!/usr/bin/env python3
"""Check REAL GitHub Pages responses after subject-release publication."""
import argparse
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://slobodatablichka.github.io/gos-exams-2027-public/"
HTML = {
    "index.html": ("Учебные материалы по предметам",),
    "materials/index.html": ("По предметам",),
    "subjects/index.html": ("Новый Завет — экзамен 2027", "Новый Завет — прежний вопросник", "Догматика — новый экзамен 2027", "Священное Писание Ветхого Завета", "Общецерковная история", "История Русской Православной Церкви", "Литургика"),
    "subjects/nt/index.html": ("Смысловой порядок", 'id="meaning-q12"', 'id="number-q12"'),
    "subjects/ot/index.html": ("Смысловой порядок", 'id="meaning-q05"', 'id="number-q14"'),
    "subjects/dogmatics/index.html": ("Смысловой порядок", 'id="meaning-q06"', 'id="number-q16"'),
    "subjects/nt/numbers.html": ('id="number-q25"',),
    "subjects/ot/numbers.html": ('id="number-q14"',),
    "subjects/dogmatics/numbers.html": ('id="number-q07"',),
    "subjects/oi/index.html": ("Смысловой порядок", 'id="meaning-q09"', 'id="number-q09"'),
    "subjects/rpc/index.html": ("Смысловой порядок", 'id="meaning-q01"', 'id="number-q17"', "Рабочая редакция"),
    "subjects/liturgics/index.html": ("Смысловой порядок", 'id="meaning-q01"', 'id="number-q24"', "Рабочая редакция"),
    "subjects/oi/numbers.html": ('id="number-q25"',),
    "subjects/rpc/numbers.html": ('id="number-q17"',),
    "subjects/liturgics/numbers.html": ('id="number-q24"',),
    "sessions/21/q18-l3.html": ("exam-subject-nav", "subjects/oi/index.html"),
    "sessions/22/q17-l3.html": ("exam-subject-nav", "subjects/rpc/index.html"),
    "sessions/18/q13-l3.html": ("exam-subject-nav", "subjects/liturgics/index.html"),
    "sessions/23/q24-l3.html": ("exam-subject-nav", "subjects/liturgics/index.html"),
    "sessions/01/q12-l3.html": ("exam-subject-nav", "subjects/nt/index.html"),
    "sessions/02/q05-l3.html": ("exam-subject-nav", "subjects/ot/index.html"),
    "sessions/19/q23-nt-l3.html": ("exam-subject-nav", "subjects/nt/index.html"),
    "sessions/19/q23-dogmatics-l3.html": ("exam-subject-nav", "subjects/dogmatics/index.html"),
    "sessions/14/index.html": ("Священное Писание Ветхого Завета",),
    "sessions/01/l3-complete.html": ("Сборник",),
}
PDFS = [
    "subjects/nt/pdf/l3.pdf",
    "subjects/nt/pdf/q12-l3.pdf",
    "subjects/ot/pdf/l2.pdf",
    "subjects/ot/pdf/q05-l3.pdf",
    "subjects/dogmatics/pdf/l1.pdf",
    "subjects/dogmatics/pdf/q06-l3.pdf",
    "subjects/oi/pdf/l3.pdf",
    "subjects/oi/pdf/l2.pdf",
    "subjects/oi/pdf/l1.pdf",
    "subjects/oi/pdf/q09-l3.pdf",
    "subjects/rpc/pdf/l3.pdf",
    "subjects/rpc/pdf/l2.pdf",
    "subjects/rpc/pdf/l1.pdf",
    "subjects/rpc/pdf/q17-l3.pdf",
    "subjects/liturgics/pdf/l3.pdf",
    "subjects/liturgics/pdf/l2.pdf",
    "subjects/liturgics/pdf/l1.pdf",
    "subjects/liturgics/pdf/q24-l3.pdf",
]


def get(path):
    request = Request(BASE + path, headers={"User-Agent": "GosExams2027-ReleaseAudit/1.0",
                                            "Accept": "text/html,application/pdf,*/*"})
    with urlopen(request, timeout=22) as resp:
        status = resp.status
        if status != 200:
            raise ValueError("%s returned HTTP %s" % (path, status))
        body = resp.read()
        if not body:
            raise ValueError("Empty HTTP response: " + path)
        return body, resp.headers


def audit():
    for path, expected in HTML.items():
        data, headers = get(path)
        contents = data.decode("utf-8", errors="replace")
        for needle in expected:
            if needle not in contents:
                raise ValueError("HTML content missing on %s: %s" % (path, needle))
        print("LIVE HTML PASS", path, len(data))
    for path in PDFS:
        data, headers = get(path)
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Invalid live PDF: " + path)
        print("LIVE PDF PASS", path, len(data))
    # The new 2027 catalog is separate from the previously published Liturgics question bank.
    fresh = [
        ("subjects/liturgics/2027/index.html", "Литургика — официальный экзамен 2027"),
        ("subjects/liturgics/2027/numbers.html", "Литургика — официальные билеты 2027"),
        ("subjects/liturgics/2027/practice/q01.html", "Литургика"),
        ("subjects/liturgics/2027/examples/q15.html", "Литургика"),
        ("subjects/liturgics/2027/examples/full/q07.html", "храм"),
    ]
    for path, marker in fresh:
        data, _ = get(path)
        if marker not in data.decode("utf-8", errors="replace"):
            raise ValueError("New 2027 page missing expected text: " + path)
        print("LIVE 2027 PAGE PASS", path, len(data))
    for n in range(1,26):
        for level in ("l3","l2","l1"):
            path = "subjects/liturgics/2027/q%02d-%s.html" % (n, level)
            data, _ = get(path)
            page = data.decode("utf-8", errors="replace")
            if "Официальный вопрос:" not in page or "Литургика" not in page:
                raise ValueError("No 2027 article text at " + path)
            print("LIVE 2027 ARTICLE PASS", path, len(data))
    for name in ["l3.pdf","l2.pdf","l1.pdf"] + [
        "q%02d-%s.pdf" % (n, level)
        for n in range(1,26) for level in ("l3","l2","l1")
    ]:
        path = "subjects/liturgics/2027/pdf/" + name
        data, _ = get(path)
        if not data.startswith(b"%PDF-") or len(data)<1500:
            raise ValueError("Invalid new 2027 PDF: " + path)
        print("LIVE 2027 PDF PASS", path, len(data))
    print("LIVE NEW 2027 PASS: 75 article HTML, 5 additional pages, 78 PDFs")

    # New 2027 Dogmatics question bank; distinct from the legacy subject URLs.
    dogmatics_pages = [
        ("subjects/dogmatics/2027/index.html", "Догматическое богословие"),
        ("subjects/dogmatics/2027/numbers.html", "Догматика"),
        ("subjects/dogmatics/2027/source-status.html", "review_pending"),
        ("subjects/dogmatics/2027/practice/methodology.html", "методика"),
        ("subjects/dogmatics/2027/practice/heresy-comparison.html", "ерес"),
        ("subjects/dogmatics/2027/practice/practicum-01.html", "Практикум"),
        ("subjects/dogmatics/2027/practice/practicum-08.html", "сложная"),
    ]
    for path, marker in dogmatics_pages:
        data, _ = get(path)
        if marker.casefold() not in data.decode("utf-8", errors="replace").casefold():
            raise ValueError("Dogmatics 2027 content missing: " + path)
        print("LIVE DOGMATICS PAGE PASS", path, len(data))
    for n in range(1, 26):
        for level in ("l3", "l2", "l1"):
            path = "subjects/dogmatics/2027/q%02d-%s.html" % (n, level)
            data, _ = get(path)
            body = data.decode("utf-8", errors="replace")
            if "Догматика" not in body:
                raise ValueError("Dogmatics 2027 article missing: " + path)
            if n == 23 and "review_pending" not in body:
                raise ValueError("Working status missing on " + path)
            if n >= 16 and "Официальный" not in body:
                raise ValueError("Original task missing on " + path)
            print("LIVE DOGMATICS ARTICLE PASS", path, len(data))
    for n in range(1, 11):
        path = "subjects/dogmatics/2027/practice/practicum-%02d.html" % n
        data, _ = get(path)
        if "Вариант 3" not in data.decode("utf-8", errors="replace"):
            raise ValueError("Practice variants missing at " + path)
        print("LIVE DOGMATICS PRACTICE PASS", path, len(data))
    for name in ["l3.pdf", "l2.pdf", "l1.pdf"] + [
        "q%02d-%s.pdf" % (n, level)
        for n in range(1, 26) for level in ("l3", "l2", "l1")
    ]:
        path = "subjects/dogmatics/2027/pdf/" + name
        data, _ = get(path)
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Invalid Dogmatics 2027 PDF: " + path)
        print("LIVE DOGMATICS PDF PASS", path, len(data))
    print("LIVE DOGMATICS 2027 PASS: 75 article HTML, 12 practice pages, 78 PDFs, legacy URLs also tested")


    # Separate approved official Church History 2027 release; old OI URLs remain.
    for path, marker in [
        ("subjects/oi/2027/index.html", "Общецерковная история"),
        ("subjects/oi/2027/numbers.html", "Общецерковная история"),
    ]:
        data, _ = get(path)
        if marker not in data.decode("utf-8", errors="replace"):
            raise ValueError("Church History 2027 catalog missing: " + path)
        print("LIVE OI 2027 CATALOG PASS", path, len(data))
    for n in range(1, 26):
        for level in ("l3", "l2", "l1"):
            path = "subjects/oi/2027/q%02d-%s.html" % (n, level)
            data, _ = get(path)
            page = data.decode("utf-8", errors="replace")
            if "Официальный вопрос." not in page or "Общецерковная история" not in page:
                raise ValueError("Church History 2027 article missing: " + path)
            print("LIVE OI 2027 ARTICLE PASS", path, len(data))
    for name in ["l3.pdf", "l2.pdf", "l1.pdf"] + [
        "q%02d-%s.pdf" % (n, level)
        for n in range(1, 26) for level in ("l3", "l2", "l1")
    ]:
        path = "subjects/oi/2027/pdf/" + name
        data, _ = get(path)
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Invalid Church History 2027 PDF: " + path)
        print("LIVE OI 2027 PDF PASS", path, len(data))
    print("LIVE OI 2027 PASS: 75 article HTML, 2 catalog pages, 78 actual PDFs")

    # Russian Orthodox Church History — distinct official 2027 question bank.
    for page in ("index.html", "numbers.html"):
        path = "subjects/rpc/2027/" + page
        data, _ = get(path)
        text = data.decode("utf-8", errors="replace")
        if "История Русской Православной Церкви" not in text:
            raise ValueError("New RPC 2027 catalog missing: " + path)
        print("LIVE RPC 2027 CATALOG PASS", path, len(data))
    for n in range(1, 26):
        for level in ("l3", "l2", "l1"):
            path = "subjects/rpc/2027/q%02d-%s.html" % (n, level)
            data, _ = get(path)
            page = data.decode("utf-8", errors="replace")
            if "Официальная формулировка:" not in page or "История Русской Православной Церкви" not in page:
                raise ValueError("RPC 2027 article missing: " + path)
            print("LIVE RPC 2027 ARTICLE PASS", path, len(data))
    for name in ["l3.pdf", "l2.pdf", "l1.pdf"] + [
        "q%02d-%s.pdf" % (n, level)
        for n in range(1, 26) for level in ("l3", "l2", "l1")
    ]:
        path = "subjects/rpc/2027/pdf/" + name
        data, _ = get(path)
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Invalid RPC 2027 PDF: " + path)
        print("LIVE RPC 2027 PDF PASS", path, len(data))
    print("LIVE RPC 2027 PASS: 75 article HTML, 2 catalog pages, 78 actual PDFs")

    # Separate New Testament question bank approved for 2027; all legacy NT URLs remain.
    for name in ("index.html", "numbers.html"):
        path = "subjects/nt/2027/" + name
        data, _ = get(path)
        body = data.decode("utf-8", errors="replace")
        if "Новый Завет" not in body or "2027" not in body:
            raise ValueError("NT 2027 catalog missing: " + path)
        print("LIVE NT 2027 CATALOG PASS", path, len(data))
    for n in range(1, 26):
        for level in ("l3", "l2", "l1"):
            path = "subjects/nt/2027/q%02d-%s.html" % (n, level)
            data, _ = get(path)
            body = data.decode("utf-8", errors="replace")
            if "Официальная формулировка:" not in body or "Новый Завет" not in body:
                raise ValueError("NT 2027 article missing: " + path)
            print("LIVE NT 2027 ARTICLE PASS", path, len(data))
    for name in ["l3.pdf", "l2.pdf", "l1.pdf"] + [
        "q%02d-%s.pdf" % (n, level)
        for n in range(1, 26) for level in ("l3", "l2", "l1")
    ]:
        path = "subjects/nt/2027/pdf/" + name
        data, _ = get(path)
        if not data.startswith(b"%PDF-") or len(data) < 1500:
            raise ValueError("Invalid NT 2027 PDF: " + path)
        print("LIVE NT 2027 PDF PASS", path, len(data))
    print("LIVE NT 2027 PASS: 75 article HTML, 2 catalog pages, 78 actual PDFs")

    print("LIVE PASS: %d actual HTML pages, %d actual downloadable PDFs" %
          (len(HTML), len(PDFS)))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--attempts", type=int, default=12)
    p.add_argument("--retry-seconds", type=int, default=12)
    args = p.parse_args()
    for attempt in range(1, args.attempts + 1):
        try:
            print("ATTEMPT %d/%d" % (attempt, args.attempts), flush=True)
            audit()
            sys.exit(0)
        except (ValueError, HTTPError, URLError, TimeoutError, OSError) as error:
            print("PUBLIC SITE NOT VERIFIED:", str(error), flush=True)
            if attempt < args.attempts:
                time.sleep(args.retry_seconds)
    sys.exit(1)
