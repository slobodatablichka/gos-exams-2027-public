#!/usr/bin/env python3
"""Accessible A4 PDF editions for subject catalogs; only approved public-facing manuscripts.

Requires reportlab, markdown, beautifulsoup4, pypdf and Cyrillic DejaVu fonts.
Sections, clickable contents and numeric ticket index are generated from one JSON model.
All PDFs are reproducible from the same private manuscript paths used for the website.
"""
from __future__ import annotations

import hashlib
import html
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from markdown import markdown
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer)
from reportlab.platypus.tableofcontents import TableOfContents, TableOfContents as _TOC


LEVEL_NAMES = {"l3": "Полный ответ", "l2": "Устный ответ", "l1": "Тезисный план"}
PUBLIC_SITE = "https://slobodatablichka.github.io/gos-exams-2027-public/"
FONTS = (
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
)
FRONT = re.compile(r"\A---[ \t]*\n.*?\n---[ \t]*\n", re.S)
CODE_SPACES = re.compile(r"[ \t]+")


def _fonts():
    if "GosSans" in pdfmetrics.getRegisteredFontNames():
        return
    for normal, bold in FONTS:
        if Path(normal).is_file() and Path(bold).is_file():
            pdfmetrics.registerFont(TTFont("GosSans", normal))
            pdfmetrics.registerFont(TTFont("GosSansBold", bold))
            pdfmetrics.registerFontFamily("GosSans", normal="GosSans", bold="GosSansBold")
            return
    raise ValueError("Cyrillic TrueType fonts not available")


def _styles():
    _fonts()
    def p(name, size, lead, **kw):
        return ParagraphStyle(name, **dict({"fontName":"GosSans","fontSize":size,"leading":lead}, **kw))
    return {
        "title": p("GosTitle", 18, 25, fontName="GosSansBold", spaceAfter=14),
        "intro": p("GosIntro", 10, 15, spaceAfter=9, textColor=colors.HexColor("#485664")),
        "section": p("GosSection", 14, 20, fontName="GosSansBold",
                     spaceBefore=12, spaceAfter=9, keepWithNext=True),
        "question": p("GosQuestion", 11.5, 17, fontName="GosSansBold",
                      spaceBefore=8, spaceAfter=7, keepWithNext=True),
        "h2": p("GosH2", 11, 16, fontName="GosSansBold",
                spaceBefore=9, spaceAfter=5, keepWithNext=True),
        "h3": p("GosH3", 10.5, 15, fontName="GosSansBold",
                spaceBefore=8, spaceAfter=4, keepWithNext=True),
        "body": p("GosBody", 10, 15.1, spaceAfter=6),
        "quote": p("GosQuote", 9.6, 14.5, leftIndent=12, spaceAfter=8,
                   textColor=colors.HexColor("#33485A")),
        "list": p("GosList", 9.9, 15, leftIndent=16, firstLineIndent=-9, spaceAfter=4),
        "tiny": p("GosTiny", 8.4, 13, spaceAfter=4),
        "toc": p("GosTOC", 9.0, 13, leftIndent=10, firstLineIndent=-6, spaceAfter=4),
        "toc2": p("GosTOCChild", 8.7, 12.7, leftIndent=22, firstLineIndent=-7, spaceAfter=3),
    }


def _number_index_sort(entry):
    m = re.search(r"№\s*(\d+)", entry[1])
    return int(m.group(1)) if m else 9999


class NumericTOC(_TOC):
    """Sort ticket-number entries while retaining stable multiBuild convergence."""
    def beforeBuild(self):
        self._lastEntries = sorted(self._entries, key=_number_index_sort)
        self.clearEntries()

    def isSatisfied(self):
        return sorted(self._entries, key=_number_index_sort) == self._lastEntries


class SubjectDoc(BaseDocTemplate):
    def __init__(self, path, title, *, source_ref=""):
        super().__init__(str(path), pagesize=A4, leftMargin=42, rightMargin=42,
                         topMargin=49, bottomMargin=49, title=title,
                         author="Госэкзамены — 2027", pageCompression=1)
        self.source_ref = source_ref
        f = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                  id="body", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="pages", frames=[f], onPage=self._header_footer))

    def _header_footer(self, canv, doc):
        canv.saveState()
        canv.setFont("GosSans", 7.5)
        canv.setFillColor(colors.HexColor("#66717B"))
        canv.drawString(self.leftMargin, 26, "Госэкзамены — 2027")
        canv.drawRightString(A4[0] - self.rightMargin, 26, "Стр. %d" % doc.page)
        canv.restoreState()

    def afterFlowable(self, flowable):
        bookmark = getattr(flowable, "_bookmark", None)
        if not bookmark:
            return
        self.canv.bookmarkPage(bookmark)
        level = getattr(flowable, "_heading_level", 0)
        text = getattr(flowable, "_toc_title", flowable.getPlainText())
        self.canv.addOutlineEntry(text[:110], bookmark, level=level, closed=False)
        self.notify("TOCEntry", (level, html.escape(text), self.page, bookmark))
        for n in getattr(flowable, "_question_numbers", []):
            self.notify("IndexEntry", (0, "№%02d" % n, self.page, bookmark))


def _format_inline(node):
    if isinstance(node, NavigableString):
        return html.escape(str(node), quote=False)
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    content = "".join(_format_inline(child) for child in node.children)
    if name in {"b", "strong"}:
        return "<b>" + content + "</b>"
    if name in {"em", "i"}:
        return "<i>" + content + "</i>"
    if name in {"br"}:
        return "<br/>"
    if name == "code":
        return '<font color="#495566">' + content + "</font>"
    if name == "a":
        url = node.get("href", "").strip()
        if url.startswith(("https://", "http://")):
            return '<link href="%s" color="#235B83">%s</link>' % (
                html.escape(url, quote=True), content)
        return content
    if name == "sup":
        return '<super>' + content + '</super>'
    if name == "sub":
        return '<sub>' + content + '</sub>'
    if name == "img":
        return html.escape(node.get("alt", "Иллюстрация в онлайн-версии"), quote=False)
    return content


def _paragraph(elem, style):
    value = _format_inline(elem).strip()
    if not value:
        return None
    return Paragraph(value, style)


def _render_blocks(parent, styles, depth=0):
    result = []
    if depth > 15:
        raise ValueError("Markdown nesting too deep")
    for element in parent.children:
        if isinstance(element, NavigableString):
            if element.strip():
                result.append(Paragraph(html.escape(element.strip()), styles["body"]))
            continue
        if not isinstance(element, Tag):
            continue
        tag = element.name.lower()
        if tag in ("script", "style"):
            continue
        if tag == "h1":
            # The question's heading and official formulation are emitted separately.
            continue
        if tag in ("h2", "h3", "h4", "h5", "h6"):
            p = _paragraph(element, styles["h2"] if tag == "h2" else styles["h3"])
            if p:
                result.append(p)
        elif tag == "p":
            # The canonical official question is already printed above the manuscript.
            if re.match(r"^Официальн(?:ый вопрос|ая формулировка)\s*[.:]",
                        element.get_text(" ", strip=True)):
                continue
            p = _paragraph(element, styles["body"])
            if p:
                result.append(p)
        elif tag == "blockquote":
            for child in element.find_all("p", recursive=False):
                if re.match(r"^Официальн(?:ый вопрос|ая формулировка)\s*[.:]",
                            child.get_text(" ", strip=True)):
                    continue
                p = _paragraph(child, styles["quote"])
                if p:
                    result.append(p)
            if not element.find("p", recursive=False):
                p = _paragraph(element, styles["quote"])
                if p:
                    result.append(p)
        elif tag in ("ul", "ol"):
            number = 0
            for child in element.find_all("li", recursive=False):
                number += 1
                own = "".join(_format_inline(ch) for ch in child.children
                              if not (isinstance(ch, Tag) and ch.name in ("ol", "ul")))
                mark = ("%d." % number) if tag == "ol" else "•"
                result.append(Paragraph(html.escape(mark) + " " + own.strip(), styles["list"]))
                for nested in child.find_all(["ol", "ul"], recursive=False):
                    result.extend(_render_blocks(BeautifulSoup(str(nested), "html.parser"), styles, depth + 1))
        elif tag == "table":
            # Render each row as a set of labelled cells. This allows long cells to
            # split naturally across pages, unlike a non-splittable oversized table.
            for tr in element.find_all("tr"):
                cells = tr.find_all(["th", "td"], recursive=False)
                if cells:
                    values = [_format_inline(cell).strip() for cell in cells]
                    result.append(Paragraph("  |  ".join(values), styles["body"]))
        elif tag == "pre":
            result.append(Paragraph(html.escape(element.get_text()).replace("\n", "<br/>"), styles["tiny"]))
        elif tag == "hr":
            result.append(Spacer(1, 7))
        else:
            result.extend(_render_blocks(element, styles, depth + 1))
    return result


def manuscript_flowables(source, styles):
    text = FRONT.sub("", source.replace("\r\n", "\n"))
    # The private manuscripts are editorial originals, not arbitrary web HTML.
    rendered = markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    soup = BeautifulSoup(rendered, "html.parser")
    result = _render_blocks(soup, styles)
    if not result:
        raise ValueError("Manuscript has no printable content")
    return result


def _short_title(row):
    text = row["official_question"].split(". ")[0].strip().rstrip(".")
    if len(text) > 84:
        text = text[:81].rsplit(" ", 1)[0] + "…"
    return text


def _header_for_chapter(row, canon_numbers):
    nums = canon_numbers[row["canonical_question"]]
    return "Вопрос " + "/".join("№%d" % n for n in nums)


def _external_article_link(row, level, slug):
    # The current official FOS, never an earlier session or question bank.
    return PUBLIC_SITE + "subjects/%s/2027/q%02d-%s.html" % (
        slug, row["canonical_question"], level)


def build_pdf(path, model, rows, private_root, slug, level, *, source_ref="", include_index=False):
    styles = _styles()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    topics = model["topics"]
    by_canonical = {}
    for row in topics:
        by_canonical.setdefault(row["canonical_question"], []).append(row["official_number"])
    unique_numbers = set(row["canonical_question"] for row in rows)
    if len(unique_numbers) != len(rows):
        raise ValueError("Duplicate manuscript included in PDF")
    all_sections = {x["id"]: x for x in model["sections"]}
    title = model["title"]
    story = [
        Paragraph(html.escape(title), styles["title"]),
        Paragraph("%s · Госэкзамены — 2027 · %s" % (level.upper(), datetime.now(timezone.utc).strftime("%d.%m.%Y")), styles["intro"]),
        Paragraph("Ответы подготовлены по православным учебникам библиотеки БПДС. "
                  "Официальные номера билетов сохранены.", styles["intro"]),
    ]
    if source_ref:
        story.append(Paragraph("Версия исходных материалов: " + html.escape(source_ref[:40]),
                               styles["tiny"]))
    if include_index:
        toc = TableOfContents()
        toc.levelStyles = [styles["toc"], styles["toc2"]]
        toc.dotsMinLevel = 0
        number_index = NumericTOC(notifyKind="IndexEntry")
        number_index.levelStyles = [styles["toc"]]
        number_index.dotsMinLevel = 0
        story.extend([
            Paragraph("Оглавление", styles["section"]), toc,
            Paragraph("Указатель официальных номеров 1–25", styles["section"]),
            number_index, PageBreak(),
        ])
    prev_section = None
    for i, row in enumerate(rows):
        if i and not include_index:
            raise ValueError("Individual PDF must contain exactly one answer")
        if i:
            story.append(PageBreak())
        section_id = row["section_id"]
        if include_index and section_id != prev_section:
            section = all_sections[section_id]
            p = Paragraph(html.escape(section["title"]), styles["section"])
            p._bookmark = "section-" + section_id
            p._heading_level = 0
            p._toc_title = section["title"]
            story.append(p)
            prev_section = section_id
        h = _header_for_chapter(row, by_canonical)
        article_title = h + ". " + _short_title(row)
        chapter = Paragraph(html.escape(article_title), styles["question"])
        chapter._bookmark = "question-%02d" % row["canonical_question"]
        chapter._heading_level = 1 if include_index else 0
        # Keep TOC titles compact so the right-aligned page number never collides.
        chapter._toc_title = (article_title if len(article_title) <= 62
                              else article_title[:59].rsplit(" ", 1)[0] + "…")
        chapter._question_numbers = by_canonical[row["canonical_question"]]
        story.append(chapter)
        story.append(Paragraph("<b>Официальная формулировка:</b> " +
                               html.escape(row["official_question"]), styles["quote"]))
        source_url = _external_article_link(row, level, slug)
        story.append(Paragraph('<link href="%s" color="#235B83">Открыть ответ на сайте</link>' %
                               html.escape(source_url, quote=True), styles["tiny"]))
        if row.get("quality") != "approved":
            notice = row.get("working_note") or "Содержательная доработка обязательных разделов продолжается."
            story.append(Paragraph('<b>РАБОЧАЯ РЕДАКЦИЯ. </b>' + html.escape(notice),
                                   styles["quote"]))
            note_url = row.get("working_notice_url")
            if note_url:
                url = PUBLIC_SITE + note_url
                story.append(Paragraph('<link href="%s" color="#235B83">Сведения о недостатках источников</link>' %
                                       html.escape(url, quote=True), styles["tiny"]))
        folder = row.get("source_folder", slug)
        filename = row.get("source_file", "q%02d.md" % row["canonical_question"])
        source_path = Path(private_root) / "materials" / folder / level / filename
        manuscript = source_path.read_text(encoding="utf-8")
        story.extend(manuscript_flowables(manuscript, styles))

    doc = SubjectDoc(path, "%s — %s" % (title, level.upper()), source_ref=source_ref)
    doc.multiBuild(story, maxPasses=7)
    if not path.is_file() or path.stat().st_size < 1400:
        raise ValueError("PDF is empty: %s" % path)


def check_pdf(path, *, full=False, expected_numbers=None, expected_title=None):
    path = Path(path)
    pdf = PdfReader(str(path), strict=True)
    if len(pdf.pages) < 1:
        raise ValueError("PDF has no pages: %s" % path)
    sample_pages = pdf.pages if full else pdf.pages[:min(2, len(pdf.pages))]
    contents = "\n".join(p.extract_text() or "" for p in sample_pages)
    if "Госэкзамены" not in contents and "Вопрос" not in contents:
        raise ValueError("Unextractable Cyrillic PDF text: %s" % path)
    if expected_title and expected_title not in contents:
        raise ValueError("Title absent: %s" % path)
    for page in pdf.pages:
        if abs(float(page.mediabox.width) - A4[0]) > 2 or abs(float(page.mediabox.height) - A4[1]) > 2:
            raise ValueError("Non-A4 page: %s" % path)
        if not (page.extract_text() or "").strip():
            raise ValueError("Blank PDF page: %s" % path)
    if full:
        if "Указатель официальных номеров" not in contents:
            raise ValueError("Numeric ticket index missing: %s" % path)
        outlines = pdf.outline
        if len(outlines) < 4:
            raise ValueError("Clickable contents/bookmarks missing: %s" % path)
        if expected_numbers:
            all_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            for n in expected_numbers:
                if "№%d" % n not in all_text and "№%02d" % n not in all_text:
                    raise ValueError("Index entry #%d missing: %s" % (n, path))
    return {"pages": len(pdf.pages), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
