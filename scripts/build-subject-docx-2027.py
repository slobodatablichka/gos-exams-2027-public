#!/usr/bin/env python3
"""Generate six editable exam DOCX collections from the published 2027 Markdown.

Per subject: question 01 L1,L2,L3 ... question 25 L1,L2,L3.
A clickable subject site link appears at the beginning of the document and
in the footer of every page. Do not change any existing PDF or question URL.
"""
import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from markdown import markdown

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://slobodatablichka.github.io/gos-exams-2027-public/subjects"
SUBJECTS = {
    "nt": "Священное Писание Нового Завета",
    "ot": "Священное Писание Ветхого Завета",
    "oi": "Общецерковная история",
    "rpc": "История Русской Православной Церкви",
    "dogmatics": "Догматическое богословие",
    "liturgics": "Литургика",
}
LEVELS = ("l1", "l2", "l3")
LEVEL_NAMES = {"l1": "Тезисный план", "l2": "Устный ответ", "l3": "Полный ответ"}
OUTPUT = "full-l1-l2-l3.docx"


def add_hyperlink(paragraph, label, address=None, anchor=None):
    part = paragraph.part
    h = OxmlElement("w:hyperlink")
    if address:
        relation = part.relate_to(
            address,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )
        h.set(qn("r:id"), relation)
    if anchor:
        h.set(qn("w:anchor"), anchor)
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "165A91")
    props.append(col)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    props.append(underline)
    run.append(props)
    t = OxmlElement("w:t")
    t.text = label
    run.append(t)
    h.append(run)
    paragraph._p.append(h)


def add_bookmark(paragraph, name, number):
    begin = OxmlElement("w:bookmarkStart")
    begin.set(qn("w:id"), str(number))
    begin.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(number))
    paragraph._p.insert(0, begin)
    paragraph._p.append(end)


def add_inline(paragraph, node, bold=False, italic=False):
    if isinstance(node, NavigableString):
        text = str(node)
        if text:
            run = paragraph.add_run(text)
            run.bold = bold
            run.italic = italic
        return
    if not isinstance(node, Tag):
        return
    if node.name == "a":
        url = node.get("href", "")
        # Internal source links are preserved as absolute live web links.
        if url and not url.startswith(("http:", "https:", "#")):
            url = BASE + "/" + CURRENT_SUBJECT + "/2027/" + url
        add_hyperlink(paragraph, node.get_text(" ", strip=True), address=url if url else None)
    elif node.name in ("br",):
        paragraph.add_run().add_break()
    elif node.name in ("code",):
        run = paragraph.add_run(node.get_text())
        run.font.name = "Consolas"
    else:
        for child in node.children:
            add_inline(paragraph, child, bold or node.name in ("b", "strong"), italic or node.name in ("i", "em"))


CURRENT_SUBJECT = ""


def render_blocks(document, container):
    for el in container.children:
        if not isinstance(el, Tag):
            continue
        if el.name in ("h1", "h2", "h3", "h4"):
            level = min(3, int(el.name[1]) + 1)
            p = document.add_paragraph(style="Heading " + str(level))
            for child in el.children:
                add_inline(p, child)
        elif el.name in ("p", "blockquote"):
            p = document.add_paragraph()
            if el.name == "blockquote":
                p.style = "Quote"
            for child in el.children:
                add_inline(p, child)
        elif el.name in ("ul", "ol"):
            for li in el.find_all("li", recursive=False):
                p = document.add_paragraph(style="List Number" if el.name == "ol" else "List Bullet")
                for child in li.children:
                    if isinstance(child, Tag) and child.name in ("ul", "ol"):
                        continue
                    add_inline(p, child)
                for nested in li.find_all(["ul", "ol"], recursive=False):
                    render_blocks(document, [nested])
        elif el.name == "table":
            rows = el.find_all("tr")
            if rows:
                cols = max(len(row.find_all(["th", "td"], recursive=False)) for row in rows)
                if cols == 0:
                    continue
                table = document.add_table(rows=len(rows), cols=cols)
                table.style = "Table Grid"
                for ri, row in enumerate(rows):
                    for ci, cell in enumerate(row.find_all(["th", "td"], recursive=False)):
                        if ci >= cols:
                            break
                        p = table.cell(ri, ci).paragraphs[0]
                        for child in cell.children:
                            add_inline(p, child)
        elif el.name in ("div", "section"):
            render_blocks(document, el)


def source_body(file):
    raw = file.read_text(encoding="utf-8-sig")
    raw = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", raw, flags=re.S)
    lines = raw.splitlines()
    # Drop navigation until the actual article heading.
    start = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if start is None:
        raise ValueError("Missing source heading: " + str(file))
    body = "\n".join(lines[start + 1:]).strip()
    if len(body) < 100:
        raise ValueError("Source appears empty: " + str(file))
    return BeautifulSoup(markdown(body, extensions=["tables", "fenced_code", "sane_lists"]), "html.parser")


def new_document(name, slug):
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2.1)
    section.left_margin = Cm(2.3)
    section.right_margin = Cm(2)
    section.footer_distance = Cm(0.9)
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)
    for i in range(1, 4):
        s = styles["Heading " + str(i)]
        s.font.name = "Arial"
        s.font.color.rgb = RGBColor(27, 64, 98)
    title = document.add_heading(name, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = document.add_paragraph("Государственный экзамен — 2027\n25 вопросов · L1 → L2 → L3")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    link = document.add_paragraph("Учебный сайт: ")
    add_hyperlink(link, "Материалы по предмету", BASE + "/" + slug + "/2027/")
    link.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_hyperlink(footer, "Госэкзамены — 2027 · " + name, BASE + "/" + slug + "/2027/")
    document.add_heading("Содержание", level=1)
    for question in range(1, 26):
        p = document.add_paragraph()
        add_hyperlink(p, f"Вопрос №{question}", anchor=f"q{question:02d}")
        p.add_run("   ·   ")
        for i, level in enumerate(LEVELS):
            if i:
                p.add_run("  |  ")
            add_hyperlink(p, level.upper(), anchor=f"q{question:02d}_{level}")
    return document


def build_one(root, slug, check=False):
    global CURRENT_SUBJECT
    CURRENT_SUBJECT = slug
    folder = root / "subjects" / slug / "2027"
    target = folder / "docx" / OUTPUT
    if check:
        from zipfile import ZipFile
        if not target.is_file():
            raise ValueError("DOCX missing: " + str(target))
        with ZipFile(target) as z:
            data = z.read("word/document.xml").decode()
            footer = z.read("word/footer1.xml").decode()
            rels = z.read("word/_rels/footer1.xml.rels").decode()
            if len(re.findall(r'w:name="q\d\d_l[123]"', data)) != 75:
                raise ValueError("Expected 75 level bookmarks: " + slug)
            if len(re.findall(r'w:name="q\d\d"', data)) != 25:
                raise ValueError("Expected 25 question bookmarks: " + slug)
            if "w:hyperlink" not in footer or BASE + "/" + slug + "/2027/" not in rels:
                raise ValueError("Footer site link missing: " + slug)
        print(f"PASS {slug}: 25 questions x L1,L2,L3, linked footer")
        return
    document = new_document(SUBJECTS[slug], slug)
    bookmark_id = 1
    for question in range(1, 26):
        document.add_page_break()
        qtitle = document.add_heading(f"Вопрос №{question}", level=1)
        add_bookmark(qtitle, f"q{question:02d}", bookmark_id)
        bookmark_id += 1
        for level in LEVELS:
            src = folder / f"q{question:02d}-{level}.md"
            if not src.is_file():
                raise ValueError("Missing approved published source: " + str(src))
            heading = document.add_heading(f"{level.upper()} — {LEVEL_NAMES[level]}", level=2)
            add_bookmark(heading, f"q{question:02d}_{level}", bookmark_id)
            bookmark_id += 1
            render_blocks(document, source_body(src))
    target.parent.mkdir(parents=True, exist_ok=True)
    document.save(target)
    build_one(root, slug, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    for slug in SUBJECTS:
        build_one(args.root, slug, check=args.check)
    if not args.check:
        for slug in SUBJECTS:
            folder = args.root / "subjects" / slug / "2027"
            index = folder / "index.md"
            old = index.read_text(encoding="utf-8")
            marker = "**Полный DOCX-сборник L1+L2+L3:**"
            link = f"{marker} [скачать редактируемый Word: №1 (L1, L2, L3) … №25 (L1, L2, L3)](docx/{OUTPUT})"
            pattern = r"(?m)^\*\*Полный DOCX-сборник L1\+L2\+L3:\*\*[^\n]*\n{0,2}"
            cleaned = re.sub(pattern, "", old)
            pdf_line = re.search(r"(?m)^\*\*Полный PDF-сборник L3\+L2\+L1:\*\*[^\n]*$", cleaned)
            if not pdf_line:
                raise ValueError("Existing full PDF link not found: " + slug)
            updated = cleaned[:pdf_line.end()] + "\n\n" + link + cleaned[pdf_line.end():]
            index.write_text(updated, encoding="utf-8")
    print("PASS: six editable 2027 DOCX subject collections")


if __name__ == "__main__":
    main()
