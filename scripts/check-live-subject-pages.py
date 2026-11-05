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
    "subjects/index.html": ("Священное Писание Нового Завета", "Догматическое богословие", "Священное Писание Ветхого Завета"),
    "subjects/nt/index.html": ("Смысловой порядок", 'id="meaning-q12"', 'id="number-q12"'),
    "subjects/ot/index.html": ("Смысловой порядок", 'id="meaning-q05"', 'id="number-q14"'),
    "subjects/dogmatics/index.html": ("Смысловой порядок", 'id="meaning-q06"', 'id="number-q16"'),
    "subjects/nt/numbers.html": ('id="number-q25"',),
    "subjects/ot/numbers.html": ('id="number-q14"',),
    "subjects/dogmatics/numbers.html": ('id="number-q07"',),
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
