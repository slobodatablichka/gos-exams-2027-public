#!/usr/bin/env python3
"""Prepare a complete new lesson from APPROVED private Markdown, then register all links.

Public repository layout must match the existing Jekyll pages.
Examples:
  python scripts/publish-lesson.py check
  python scripts/publish-lesson.py build 5 --private-root ../gos-exams-2027
  python scripts/publish-lesson.py build 5 --private-root ../gos-exams-2027 --apply

Without --apply nothing is changed. Never use this to overwrite published lessons.
The private quality gate is mandatory for new publications.
"""
import argparse
import csv
import html
import io
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path("_data/published_sessions.csv")
LEVELS = ("l3", "l2", "l1")
SUBJECTS = {
    "НЗ": ("nt", "Священное Писание Нового Завета"),
    "ВЗ": ("ot", "Священное Писание Ветхого Завета"),
    "ОИ": ("oi", "Общецерковная история"),
    "ИРПЦ": ("rpc", "История Русской Православной Церкви"),
    "ДБ": ("dogmatics", "Догматическое богословие"),
    "Л": ("liturgics", "Литургика"),
}
Q_RE = re.compile(r"^> \*\*Официальный (?:экзаменационный )?вопрос(?: \([^)]*\))?\.\*\* (.+)$", re.M)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def csv_rows(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def record_rows():
    return csv_rows("_data/roles_7.csv")


def meeting(number):
    matches = [r for r in csv_rows("_data/meetings.csv") if int(r["meeting"]) == number]
    if len(matches) != 1:
        raise ValueError(f"Missing or duplicate meeting {number}")
    return matches[0]


def topics(number):
    rows = [r for r in record_rows() if int(r["meeting"]) == number]
    if not rows or len({(r["subject"], r["question"]) for r in rows}) != len(rows):
        raise ValueError(f"Invalid topic set for meeting {number}")
    return rows


def code(row):
    return f'{int(row["question"]):02d}'


def display_subject(rows):
    types = {r["subject"] for r in rows}
    return SUBJECTS[next(iter(types))][1] if len(types) == 1 else "Несколько дисциплин"


def date_human(date):
    month = {1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая",
             6: "июня", 7: "июля", 8: "августа", 9: "сентября",
             10: "октября", 11: "ноября", 12: "декабря"}
    d = datetime.strptime(date, "%d.%m.%Y")
    return f"{d.day} {month[d.month]} {d.year} года"


def canonical_formula(markdown):
    m = Q_RE.search(markdown)
    if not m:
        raise ValueError("Official formula missing")
    return m.group(1)


def manuscript(private_root, row, level):
    directory = SUBJECTS[row["subject"]][0]
    folder = private_root / "materials" / directory / level
    canonical = folder / f'q{code(row)}.md'
    legacy = folder / f'l-{code(row)}.md'
    # Keep previously published subjects unchanged while accepting the
    # existing manuscript convention used for Liturgics session 06.
    path = canonical if canonical.is_file() else legacy
    if not path.is_file():
        raise ValueError(f"Required private manuscript missing: {canonical} or {legacy}")
    return path.read_text(encoding="utf-8")


def name_and_body(raw, level):
    h = re.search(r"^# (.+)$", raw, re.M)
    if not h:
        raise ValueError("L3/L2/L1 manuscript needs its own heading")
    main = raw.replace(h.group(0), "", 1)
    main = Q_RE.sub("", main, count=1).strip()
    # Editorial source-review notes are tracked in the private repository,
    # never published as if they were part of the study response.
    main = re.sub(r"(?m)^\*\*Статус:\*\*[^\n]*\n?", "", main).strip()
    main = re.sub(r"(?m)^\*\*Открыто:\*\*[^\n]*\n?", "", main).strip()
    main = re.sub(r"(?m)^\*\*Открытая проверка:\*\*[^\n]*\n?", "", main).strip()
    main = re.sub(r"(?m)^\*\*Источниковое разграничение:\*\*[^\n]*\n?", "", main).strip()
    main = re.sub(r"(?m)^\*Основа:[^\n]*\n?", "", main).strip()

    # Authoring metadata is private; public pages already link all three levels.
    main = re.sub(r"(?m)^\*(?:Основа ответа:|Составлено по)[^\n]*\*\s*$", "", main).strip()
    # Strip internal supplied-DOCX alignment notes from the PUBLIC reading copy.
    main = re.sub(r"\s*(?:Исходный ориентировочный ответ:|Ориентировочный исходный ответ:)[^\n]*", "", main).strip()
    if level != "l3":
        main = re.sub(r"^\*[^*\n]+\*\s*(?:\n+|$)", "", main)
    main = re.sub(r"\]\(\.\./l3/q(\d+)\.md\)", r"](q\1-l3.html)", main)
    if re.search(r"\]\([^)]*\.md\)", main):
        raise ValueError("Unresolved private Markdown link inside manuscript")
    return h.group(1), main


def topic_title(raw):
    h = re.search(r"^# (.+)$", raw, re.M)
    if not h:
        raise ValueError("Title missing from L3 manuscript")
    title = h.group(1)
    return re.sub(r"^.+?№\d+(?:\s+и\s+№\d+)?\.\s*", "", title).strip()


def render_page(number, rows, index, row, level, formulas, bodies, titles):
    ident = code(row)
    sub = row["subject"]
    title = titles[index]
    kind = {"l3": "Статья", "l2": "Устный ответ", "l1": "План"}
    b = bodies[(index, level)]
    switch = "".join(
        f'<a href="q{ident}-{l}.html"' + (' aria-current="page"' if l == level else "") +
        f'><strong>{l.upper()}</strong><span>{kind[l]}</span></a>' for l in LEVELS
    )
    others = "\n".join(
        (f"<li><strong>{r['subject']} №{int(r['question'])}. {titles[j]} — здесь</strong></li>"
         if j == index else
         f'<li><a href="q{code(r)}-{level}.html">{r["subject"]} №{int(r["question"])}. {titles[j]}</a></li>')
        for j, r in enumerate(rows)
    )
    prev = rows[index - 1] if index > 0 else None
    next_ = rows[index + 1] if index + 1 < len(rows) else None
    previous = (f'<a class="prev" href="q{code(prev)}-{level}.html">← Предыдущая тема'
                f'<strong>{titles[index - 1]}</strong></a>') if prev else "<span></span>"
    following = (f'<a class="next" href="q{code(next_)}-{level}.html">Следующая тема →'
                 f'<strong>{titles[index + 1]}</strong></a>') if next_ else "<span></span>"
    label = f'{sub} №{int(row["question"])}'
    if row["aliases"]:
        label += f'/{row["aliases"]}'
    return f'''---
layout: default
title: "{html.escape(label)}. {html.escape(title)} · {level.upper()}"
---

<div class="exam-breadcrumbs"><a href="../../index.html">Главная</a> › <a href="../../materials/index.html">Материалы</a> › <a href="index.html">Занятие №{number}</a> › {label}</div>

# {label}. {title} · {level.upper()}

<h4 class="exam-section-label">Официальная формулировка экзаменационного вопроса №{int(row["question"])}</h4>
<blockquote class="exam-official"><p>{html.escape(formulas[index], quote=False)}</p></blockquote>

{('<p class="exam-alias-note">Повтор официальной формулировки под №' + row["aliases"] + '. Изучаем одну тему и используем один комплект ответов.</p>') if row["aliases"] else ''}

<nav class="exam-levels" aria-label="Три уровня этого вопроса">{switch}</nav>
<details class="exam-questions"><summary>Другие темы занятия · {level.upper()}</summary><ol>{others}</ol></details>

{b}

<div class="exam-divider"></div>
<nav class="exam-prevnext">{previous}{following}</nav>
<div class="exam-footer-links"><a href="index.html">Все вопросы занятия</a> · <a href="l3-complete.html">Сборник L3</a> · <a href="../../schedule.html">Расписание</a> · <a href="https://library.logoscosmos.org/bpds/gos-exams-2027/">Библиотека БПДС</a></div>
'''


def render_index(number, rows, titles):
    m = meeting(number)
    subject = display_subject(rows)
    cards = "\n".join(
        f'<article class="lesson-card"><p class="lesson-number">Вопрос {i + 1} из {len(rows)} · '
        f'{r["subject"]} №{int(r["question"])}{("/" + r["aliases"]) if r["aliases"] else ""}</p>'
        f'<h3>{html.escape(titles[i])}</h3><div class="lesson-actions">'
        + "".join(f'<a href="q{code(r)}-{l}.html">{l.upper()} · {label}</a>' for l, label in
                  (("l3", "Статья"), ("l2", "Ответ"), ("l1", "План"))) + '</div></article>'
        for i, r in enumerate(rows)
    )
    return f'''---
layout: default
title: "Занятие №{number} — {subject}, {m["date"]}"
---

[Главная](../../index.html) › [Материалы](../../materials/index.html) › **Занятие №{number}**

# Занятие №{number}. {subject}

**{m["weekday"].capitalize()}, {date_human(m["date"])} · {m["start_time"]}**

[Общий сборник статей L3](l3-complete.html) · [План докладчиков](../../assignments.html)

**L3** — объясняющая статья; **L2** — устный экзаменационный ответ; **L1** — содержательный тезисный план.

<div class="lesson-cards">
{cards}
</div>

[Сборник L3](l3-complete.html) · [Расписание](../../schedule.html) · [Библиотека БПДС](https://library.logoscosmos.org/bpds/gos-exams-2027/)
'''


def render_reader(number, rows, titles, formulas, bodies):
    m = meeting(number)
    toc = "\n".join(
        f'- [{r["subject"]} №{int(r["question"])}{("/" + r["aliases"]) if r["aliases"] else ""}. {titles[i]}](#n{code(r)}) · '
        + " · ".join(f'[{l.upper()}](q{code(r)}-{l}.html)' for l in LEVELS)
        for i, r in enumerate(rows))
    sections = []
    for i, r in enumerate(rows):
        heading = f'{r["subject"]} №{int(r["question"])}{("/" + r["aliases"]) if r["aliases"] else ""}. {titles[i]}'
        body = re.sub(r"(?m)^(#{2,3}) ", lambda x: "#" + x.group(1) + " ", bodies[(i, "l3")])
        alias_note = (f'<p class="exam-alias-note">Эта же формулировка встречается под официальным №{r["aliases"]}. Ответ один.</p>\n\n' if r["aliases"] else "")
        sections.append(f'''---

<a id="n{code(r)}"></a>

## {heading}

<h4 class="exam-section-label">Официальная формулировка экзаменационного вопроса №{int(r["question"])}{("/" + r["aliases"]) if r["aliases"] else ""}</h4>
<blockquote class="exam-official"><p>{html.escape(formulas[i], quote=False)}</p></blockquote>

{alias_note}{body}

[К ответам L3 / L2 / L1](q{code(r)}-l3.html)
''')
    return f'''---
layout: default
title: "Сборник L3 занятия №{number} — {display_subject(rows)}"
---

[Главная](../../index.html) · [Материалы](../../materials/index.html) · [Занятие №{number}](index.html) · [Расписание](../../schedule.html)

# {display_subject(rows)} — сборник L3

**{len(rows)} объясняющих статей · {date_human(m["date"])}, {m["start_time"]}.**

## Содержание

{toc}

''' + "\n".join(sections)


def quality_gate(private_root, number, rows):
    progress = private_root / "planning" / "lesson-progress.csv"
    if not progress.is_file():
        raise ValueError(f"Missing quality gate: {progress}")
    with progress.open(encoding="utf-8-sig", newline="") as f:
        all_progress = list(csv.DictReader(f))
    for row in rows:
        found = [p for p in all_progress if int(p["meeting"]) == number
                 and p["subject"] == row["subject"] and
                 int(p["question"]) == int(row["question"])]
        if len(found) != 1 or not all(found[0][k] == "done" for k in
                                       ("sources", "l3", "l2", "l1")) or found[0]["quality"] != "approved":
            raise ValueError(f"Quality gate not approved: lesson {number}, {row['subject']} №{row['question']}")


def assemble(number, private_root):
    rows = topics(number)
    quality_gate(private_root, number, rows)
    formulas, bodies, titles = [], {}, []
    for i, row in enumerate(rows):
        source = {l: manuscript(private_root, row, l) for l in LEVELS}
        qs = [canonical_formula(source[l]) for l in LEVELS]
        if len(set(qs)) != 1:
            raise ValueError(f"Official wording differs between L3/L2/L1: {row}")
        formulas.append(qs[0])
        titles.append(topic_title(source["l3"]))
        for level in LEVELS:
            _, bodies[(i, level)] = name_and_body(source[level], level)
    results = {}
    dest = Path(f"sessions/{number:02d}")
    for i, row in enumerate(rows):
        for level in LEVELS:
            path = dest / f'q{code(row)}-{level}.md'
            if (ROOT / path).exists():
                raise ValueError(f"Existing URL cannot be overwritten: {path}")
            results[path] = render_page(number, rows, i, row, level, formulas, bodies, titles)
    for suffix, output in (("index.md", render_index(number, rows, titles)),
                           ("l3-complete.md", render_reader(number, rows, titles, formulas, bodies))):
        path = dest / suffix
        if (ROOT / path).exists():
            raise ValueError(f"Existing URL cannot be overwritten: {path}")
        results[path] = output
    return results


def schedule_section(markdown, n):
    pattern = re.compile(r"(?m)^## Занятие " + str(n) + r" —.*$")
    m = pattern.search(markdown)
    if not m:
        raise ValueError(f"Schedule section for meeting {n} not found")
    next_h = re.search(r"(?m)^## Занятие \d+ —", markdown[m.end():])
    end = m.end() + next_h.start() if next_h else len(markdown)
    return m.start(), end


def schedule_row(section, row):
    matches = []
    for line in section.splitlines():
        if not line.startswith("| ") or not line.endswith(" |"):
            continue
        cells = line[2:-2].split(" | ")
        if len(cells) != 5 or SUBJECTS[row["subject"]][1] not in cells[0]:
            continue
        nums = re.search(r"№ (\d+)(?:/(\d+))?", cells[0])
        if nums and int(nums.group(1)) == int(row["question"]):
            matches.append((line, cells))
    if len(matches) != 1:
        raise ValueError(f"Ambiguous schedule row {row}: {len(matches)}")
    return matches[0]


def add_navigation(number, generated):
    rows = topics(number)
    site_schedule = read("schedule.md")
    start, end = schedule_section(site_schedule, number)
    section = site_schedule[start:end]
    for row in rows:
        old, cells = schedule_row(section, row)
        target = f'sessions/{number:02d}/q{code(row)}-l3.html'
        if target in cells[0]:
            raise ValueError(f"Schedule URL already exists: {target}")
        cells[0] = f'[{cells[0]}]({target})'
        section = section.replace(old, "| " + " | ".join(cells) + " |", 1)
    generated[Path("schedule.md")] = site_schedule[:start] + section + site_schedule[end:]

    m = meeting(number)
    label = display_subject(rows)
    cat = read("materials/index.md")
    marker = "Последующие занятия будут добавляться сюда по мере подготовки."
    if cat.count(marker) != 1:
        raise ValueError("Catalog marker missing or duplicated")
    path = f'sessions/{number:02d}'
    section = (f'### [Занятие №{number}. {label}](../{path}/index.html)\n\n'
               f'**{date_human(m["date"])}, {m["start_time"]}.** '
               f'{len(rows)} самостоятельных тем; {len(rows)*3} материалов L3/L2/L1.\n\n'
               f'[Все вопросы](../{path}/index.html) · [Сборник L3](../{path}/l3-complete.html)\n\n')
    generated[Path("materials/index.md")] = cat.replace(marker, section + marker)

    homepage = read("index.md")
    anchor = "\n## Докладчики по группам"
    if homepage.count(anchor) != 1:
        raise ValueError("Homepage insertion point missing or duplicated")
    note = (f'\n**[Занятие №{number} — {label}, {date_human(m["date"])}]'
            f'({path}/index.html):** {len(rows)} комплектов L3/L2/L1; '
            f'[сборник L3]({path}/l3-complete.html).\n')
    first, sep, tail = homepage.partition("\n")
    if f'[Занятие №{number}]({path}/index.html)' not in first:
        first += f' · [Занятие №{number}]({path}/index.html)'
    generated[Path("index.md")] = first + sep + tail.replace(anchor, note + anchor, 1)

    ledger = read(LEDGER)
    if any(int(s["session"]) == number for s in csv_rows(LEDGER)):
        raise ValueError(f"Lesson {number} already registered")
    keys = ";".join(code(r) for r in rows)
    generated[LEDGER] = ledger.rstrip("\n") + f"\n{number},{keys}\n"


def validate():
    rows = csv_rows(LEDGER)
    ids = set()
    errors = []
    schedule = read("schedule.md")
    catalog = read("materials/index.md")
    homepage = read("index.md")
    for entry in rows:
        try:
            n = int(entry["session"])
            if n in ids:
                raise ValueError("Duplicate published session")
            ids.add(n)
            expected = [code(x) for x in topics(n)]
            if entry["topics"].split(";") != expected:
                raise ValueError(f"Wrong registered topic order in session {n}")
            prefix = Path(f"sessions/{n:02d}")
            for name in ("index.md", "l3-complete.md"):
                if not (ROOT / prefix / name).exists():
                    raise ValueError(f"Missing published page: {prefix/name}")
            part = schedule[schedule_section(schedule, n)[0]:schedule_section(schedule, n)[1]]
            for row in topics(n):
                ident = code(row)
                _, cells = schedule_row(part, row)
                route = f'sessions/{n:02d}/q{ident}-l3.html'
                if route not in cells[0]:
                    raise ValueError(f"Schedule lacks canonical link {route}")
                for level in LEVELS:
                    page = prefix / f'q{ident}-{level}.md'
                    if not (ROOT / page).exists():
                        raise ValueError(f"Missing published level {page}")
                    text = read(page)
                    if text.count('<blockquote class="exam-official">') != 1:
                        raise ValueError(f"Official question absent or duplicated: {page}")
                    for another in LEVELS:
                        if f'q{ident}-{another}.html' not in text:
                            raise ValueError(f"Broken level switch {page} → {another}")
            if f'sessions/{n:02d}/index.html' not in homepage:
                raise ValueError(f"Missing homepage entry for session {n}")
            if f'../sessions/{n:02d}/index.html' not in catalog:
                raise ValueError(f"Missing materials catalog entry for session {n}")
        except (ValueError, KeyError, OSError) as err:
            errors.append(str(err))
    if errors:
        raise SystemExit("\n".join("ERROR: " + e for e in errors))
    print(f"PASS: {len(rows)} published sessions, every topic has 3 canonical pages")
    print("PASS: stable schedule URLs, homepage and catalog entries")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "build"))
    parser.add_argument("session", nargs="?", type=int)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.action == "check":
        validate()
        return
    if args.session is None or not 1 <= args.session <= 23 or not args.private_root:
        parser.error("build requires a meeting number 1..23 and --private-root")
    private = args.private_root.resolve()
    output = assemble(args.session, private)
    add_navigation(args.session, output)
    print(f"PREPARED session {args.session}: {len(output)} files; published URLs preserved")
    for path in output:
        print(" ", path)
    if not args.apply:
        print("DRY RUN: no files changed. Add --apply only after verification.")
        return
    for path, content in output.items():
        dest = ROOT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    validate()
    print("APPLIED: review git diff; commit only after content and navigation review")


if __name__ == "__main__":
    main()
