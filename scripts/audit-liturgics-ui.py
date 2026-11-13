#!/usr/bin/env python3
"""Read-only audit of Liturgics public UI: wording, 61 exercises, local links."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "subjects/liturgics/2027"
DATA = ROOT / "_data/liturgics_trainers_2027.json"
WORD = re.compile(r"(?<![А-Яа-яЁё])[Ии]гр[а-яё]*(?![А-Яа-яЁё])")
MD_LINK = re.compile(r"\]\(([^)]+)\)")
HTML_LINK = re.compile(r'href=["\']([^"\']+)["\']')
problems = []
scanned = 0

def fail(message):
    problems.append(message)

def check_href(file, href):
    if not href or href.startswith("#") or "{{" in href or "{%" in href":
        return
    u = urlsplit(href)
    if u.scheme or u.netloc or href.startswith("//"):
        return
    p = unquote(u.path)
    if not p:
        return
    dest = ((ROOT / p.lstrip("/")) if p.startswith("/") else file.parent / p).resolve()
    if not dest.is_relative_to(ROOT.resolve()):
        fail("Link outside repository: " + str(file) + " -> " + href)
        return
    candidates = [dest]
    if dest.suffix == ".html":
        candidates.append(dest.with_suffix(".md"))
    if not dest.suffix:
        candidates.extend([dest / "index.html", dest / "index.md"])
    if not any(v.is_file() for v in candidates):
        fail("Broken local link: " + str(file.relative_to(ROOT)) + " -> " + href)

def check_page(file):
    global scanned
    scanned += 1
    text = file.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        plain = re.sub(r"{[%{].*?[%}]}", "", line)
        plain = re.sub(r"https?://[^\s)]+", "", plain)
        plain = re.sub(r"\x60[^\x60]*\x60", "", plain)
        match = WORD.search(plain)
        if match:
            fail(f"Visible word {match.group(0)}: {file.relative_to(ROOT)}:{number}: {line[:150]}")
    if file.suffix == ".md":
        links = MD_LINK.findall(text)
    else:
        links = HTML_LINK.findall(text)
    for link in links:
        check_href(file, link.split(" ", 1)[0])

def check_json_strings(file, obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k not in {"case_id","id","path","source","l3","mode","status","schema"}:
                check_json_strings(file,v)
    elif isinstance(obj,list):
        for v in obj:
            check_json_strings(file,v)
    elif isinstance(obj,str):
        match=WORD.search(obj)
        if match:
            fail(f"Visible JSON word {match.group(0)}: {file.relative_to(ROOT)}: {obj[:130]}")

def main():
    manifest=json.loads(DATA.read_text(encoding="utf-8"))
    questions=manifest["questions"]
    if len(questions)!=15 or [q["number"] for q in questions]!=list(range(1,16)):
        fail("Wrong number/order of FOS questions")
    if len(manifest["variant_slots"])!=45:
        fail("Expected 45 A/B/V slots")
    cases=[c for q in questions for c in q["cases"]]
    if len(cases)!=61:
        fail(f"Expected 61 exercises, got {len(cases)}")
    paths=set()
    for q in questions:
        variants={c.get("variant") for c in q["cases"]}
        if not {"А","Б","В"}.issubset(variants):
            fail(f"Missing A/B/V variant for FOS {q['number']}")
        for c in q["cases"]:
            rel=c["path"]
            page=BASE / rel
            if rel in paths:
                fail("Repeated path " + rel)
            paths.add(rel)
            if not page.is_file():
                fail("Missing trainer page " + rel)
                continue
            content=page.read_text(encoding="utf-8")
            token='{% include liturgics-trainer-nav.html case_path="'+rel+'" %}'
            if content.count(token)!=1:
                fail("Missing or repeated contextual navigation in " + rel)
            if 'style="font-size:12px;margin:9px 0"' in content:
                fail("Legacy ad-hoc links in " + rel)
            m=re.search(r'data-case="data/([^"]+\.json)"',content)
            if not m:
                fail("Missing data-case in " + rel)
            else:
                file=BASE / "sandbox-pyramid/data" / m.group(1)
                if not file.is_file():
                    fail("Missing case JSON " + rel)
                else:
                    payload=json.loads(file.read_text(encoding="utf-8"))
                    if payload.get("case_id")!=c["case_id"] or payload.get("mode")!=c["mode"]:
                        fail("Registry / case JSON mismatch in " + rel)
            check_page(page)
    actual={p.relative_to(BASE).as_posix() for p in (BASE/"sandbox-pyramid").glob("*.html")}
    if paths!=actual:
        fail(f"HTML set mismatch: missing {sorted(paths-actual)}, extra {sorted(actual-paths)}")
    for page in BASE.rglob("*.md"):
        check_page(page)
    for relative in [
       "subjects/liturgics/2027/trainers/sequence.html",
       "_includes/liturgics-game-links.html",
       "_includes/liturgics-trainer-nav.html",
       "_includes/global-navigation.html",
       "assets/js/liturgics-pyramid.js",
       "assets/js/liturgics-sequence.js",
    ]:
        check_page(ROOT/relative)
    for file in (BASE/"sandbox-pyramid/data").glob("*.json"):
        check_json_strings(file,json.loads(file.read_text(encoding="utf-8")))
    check_json_strings(DATA,manifest)
    catalog=(BASE/"trainers/index.md").read_text(encoding="utf-8")
    home=(BASE/"index.md").read_text(encoding="utf-8")
    if 'data-question="{{ question.id }}"' not in catalog:
        fail("Missing 15-question HTML audit attribute")
    if "practicum/index.html" not in home or "trainers/index.html" not in home:
        fail("Subject landing page lacks course or trainers")
    for n in ("01","02","03","04"):
        if f"lesson-{n}.html" not in catalog:
            fail("First-round materials not in catalogue: "+n)
    if problems:
        print(f"FAILED: {len(problems)} issues; {scanned} text pages scanned.")
        for item in problems[:150]:
            print("FAIL",item)
        sys.exit(1)
    print(f"PASS: {scanned} text pages, 61 trainer pages, 61 JSON datasets, 15 FOS, 45 variants; wording and links checked.")

if __name__=="__main__":
    main()
