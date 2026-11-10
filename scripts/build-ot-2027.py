#!/usr/bin/env python3
"""Publish the *new* 2027 Old Testament set without touching the historic NT routes."""
import argparse, hashlib, json, posixpath, re, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("subjects/ot/2027")
LEVELS = ("l3", "l2", "l1")
NAMES = {"l3": "Полный ответ", "l2": "Устный ответ", "l1": "Тезисный план"}
FORM = re.compile(r"^\*\*Официальная формулировка:\*\*\s+(.+)$", re.M)
MDLINK = re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
GROUPS = [
    ("intro", "Канон, текст и происхождение Пятикнижия", range(1, 4)),
    ("pentateuch", "Пятикнижие и история Израиля", range(4, 9)),
    ("history", "Исторические книги и пророки Илия и Елисей", range(9, 14)),
    ("wisdom", "Учительные книги", range(14, 18)),
    ("prophets", "Пророческие книги", range(18, 24)),
    ("deuterocanon", "Неканонические книги и дополнения", range(24, 26)),
]

def front(title):
    return "---\nlayout: default\ntitle: " + json.dumps(title, ensure_ascii=False) + "\n---\n\n"

def linkify(text):
    """Retain citations, rewrite only links between the three *new* levels."""
    def sub(m):
        title, url = m.groups()
        hit = re.fullmatch(r"\.\./(l[123])/(q\d{2})\.md", url)
        if hit:
            return f"[{title}]({hit.group(2)}-{hit.group(1)}.html)"
        return m.group(0)
    return MDLINK.sub(sub, text)

def checked_sources(private):
    docs, questions = {}, {}
    for n in range(1, 26):
        docs[n] = {}
        for level in LEVELS:
            file = private / "materials/ot/2027" / level / f"q{n:02d}.md"
            if not file.is_file():
                raise ValueError("Missing manuscript: " + str(file))
            raw = file.read_text(encoding="utf-8")
            if len(raw.strip()) < 400:
                raise ValueError("Manuscript too short: " + str(file))
            match = FORM.search(raw)
            if match is None:
                raise ValueError("Missing official question: " + str(file))
            if n == 24:
                warning = ("**Источниковое замечание А-2027-ВЗ-24-01 (рабочая редакция):** "
                           "конкретные богослужебные паремии из книги Премудрости Иисуса, "
                           "сына Сирахова, пока не подтверждены по Минее/Паремийнику. "
                           "Сведения об их назначении требуют дополнительной проверки.\n\n")
                marker = "\n\n"
                pos = raw.find(marker)
                raw = raw[:pos + len(marker)] + warning + raw[pos + len(marker):] if pos >= 0 else warning + raw
            docs[n][level] = raw
            questions.setdefault(n, set()).add(match.group(1).strip())
            if level != "l3" and f"../l3/q{n:02d}.md" not in raw:
                raise ValueError("Broken private level backlink: " + str(file))
        if len(questions[n]) != 1:
            raise ValueError("Question differs among levels: " + str(n))
    return docs, {n: next(iter(items)) for n, items in questions.items()}

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def navreplace(path, old, new):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise ValueError("Navigation anchor missing in " + str(path))
    write(path, text.replace(old, new, 1))

def verify_legacy():
    old = ROOT / "subjects/ot/index.md"
    if not old.is_file() or "Священное Писание Ветхого Завета" not in old.read_text(encoding="utf-8"):
        raise ValueError("Historic OT landing page missing")
    for folder in ("subjects/dogmatics/2027", "subjects/oi/2027", "subjects/rpc/2027"):
        if not (ROOT / folder / "index.md").is_file():
            raise ValueError("Unrelated subject missing: " + folder)

def generate(private, source_sha):
    import subject_pdf
    from reportlab import rl_config
    rl_config.invariant = 1
    verify_legacy()
    docs, questions = checked_sources(private)
    sections = [dict(id=id, title=title, official_numbers=list(nums)) for id, title, nums in GROUPS]
    rows = []
    for n in range(1, 26):
        group = next(id for id, _, nums in GROUPS if n in nums)
        rows.append(dict(official_number=n, canonical_question=n,
                         topic_id=f"ot-2027-q{n:02d}", section_id=group,
                         official_question=questions[n], quality=("published_working" if n == 24 else "approved"), session=0,
                         source_folder="ot", source_file=f"q{n:02d}.md",
                         level_urls={lev:f"subjects/ot/2027/q{n:02d}-{lev}.html" for lev in LEVELS}))
    model = dict(title="Священное Писание Ветхого Завета — экзамен 2027",
                 sections=sections, topics=rows)
    dest = ROOT / BASE
    for n in range(1, 26):
        links = " · ".join(f"[{level.upper()}](q{n:02d}-{level}.html) · [PDF](pdf/q{n:02d}-{level}.pdf)" for level in LEVELS)
        for level in LEVELS:
            article = linkify(docs[n][level])
            head = front(f"Ветхий Завет 2027 №{n} {level.upper()}")
            head += "[Ветхий Завет — 2027](index.html) · [Вопросы по номерам](numbers.html) · [Прежний вопросник](../index.html)\n\n"
            head += f"**Билет №{n}** · {links}\n\n"
            write(dest / f"q{n:02d}-{level}.md", head + article)
    intro = ("# Священное Писание Ветхого Завета — экзамен 2027\n\n"
             "**Новый утверждённый перечень: 25 вопросов, 75 материалов L3/L2/L1.** №24 — рабочая редакция с источниковым замечанием о паремиях Сираха.\n\n"
             "[Билеты по номерам](numbers.html) · [Прежний вопросник и материалы](../index.html)\n\n"
             "**PDF-сборники:** [Полный L3](pdf/l3.pdf) · [Устный L2](pdf/l2.pdf) · [Планы L1](pdf/l1.pdf)\n\n")
    sem = [intro]
    numeric = ["# Ветхий Завет 2027 — вопросы по номерам\n\n[Смысловой порядок](index.html) · [Прежний вопросник](../index.html)\n\n"]
    def entry(n):
        links = " · ".join(f"[{level.upper()}](q{n:02d}-{level}.html) · [PDF](pdf/q{n:02d}-{level}.pdf)" for level in LEVELS)
        return f"**[№{n}. {questions[n]}](q{n:02d}-l3.html)**\n\n{links}\n\n"
    for id, title, nums in GROUPS:
        sem.append("## " + title + "\n\n")
        for n in nums:
            sem.append(entry(n))
    for n in range(1, 26):
        numeric.append(entry(n))
    write(dest / "index.md", front("Ветхий Завет — экзамен 2027") + "".join(sem))
    write(dest / "numbers.md", front("Ветхий Завет — номера 2027") + "".join(numeric))

    # subject_pdf uses its historical canonical folder, but only the temporary
    # source-root is changed; the actual old public and private files are untouched.
    subject_pdf._external_article_link = lambda row, level, slug: (
        "https://slobodatablichka.github.io/gos-exams-2027-public/"
        + row["level_urls"][level]
    )
    manifest = dict(source_sha=source_sha, pdfs=[])
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        for level in LEVELS:
            d = tmp / "materials/ot" / level
            d.mkdir(parents=True)
            for n in range(1, 26):
                write(d / f"q{n:02d}.md", linkify(docs[n][level]))
        for level in LEVELS:
            for n in range(1, 26):
                path = dest / "pdf" / f"q{n:02d}-{level}.pdf"
                subject_pdf.build_pdf(path, model, [rows[n-1]], tmp, "ot", level, source_ref=source_sha)
                manifest["pdfs"].append(dict(file=path.relative_to(dest).as_posix(),
                                              **subject_pdf.check_pdf(path)))
            path = dest / "pdf" / f"{level}.pdf"
            subject_pdf.build_pdf(path, model, rows, tmp, "ot", level,
                                  source_ref=source_sha, include_index=True)
            manifest["pdfs"].append(dict(file=path.relative_to(dest).as_posix(),
                                          **subject_pdf.check_pdf(path, full=True,
                                                                  expected_numbers=range(1,26))))
    assert len(manifest["pdfs"]) == 78
    write(dest / "pdf-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    navreplace(ROOT/"subjects/index.md",
        "- [Священное Писание Ветхого Завета](ot/index.html) — 25 вопросов, L3/L2/L1, PDF.",
        "- **[Ветхий Завет — экзамен 2027](ot/2027/index.html)** — 25 новых вопросов, L3/L2/L1, PDF; №24 — рабочая редакция.\n- [Ветхий Завет — прежний вопросник](ot/index.html) — архивные материалы.")
    navreplace(ROOT/"subjects/ot/index.md",
        "# Священное Писание Ветхого Завета\n",
        "# Священное Писание Ветхого Завета\n\n**[Новый утверждённый перечень 2027 — 25 вопросов](2027/index.html)** · [По номерам](2027/numbers.html).\n\n*Ниже сохранён прежний вопросник.*\n")
    navreplace(ROOT/"materials/index.md",
        "[Ветхий Завет](../subjects/ot/index.html)",
        "[Ветхий Завет 2027](../subjects/ot/2027/index.html) · [Ветхий Завет (архив)](../subjects/ot/index.html)")
    navreplace(ROOT/"index.md",
        "[Ветхий Завет](subjects/ot/index.html)",
        "[Ветхий Завет 2027](subjects/ot/2027/index.html) · [Ветхий Завет (архив)](subjects/ot/index.html)")
    print("PASS: 75 new pages, 78 PDFs, updated navigation; legacy paths retained")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--private-root", required=True)
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    private = Path(args.private_root)
    verify_legacy()
    docs, questions = checked_sources(private)
    if args.check:
        print("PASS: 25 complete matching triplets; 75 existing private manuscripts")
    else:
        generate(private, args.source_sha)

if __name__ == "__main__":
    main()
