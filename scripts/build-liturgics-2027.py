#!/usr/bin/env python3
"""Build distinct 2027 Liturgics content without overwriting old material."""
import argparse, json, re, posixpath, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path("subjects/liturgics/2027")
LEVELS=("l3","l2","l1")
GRPS=[("services","Построение служб",range(1,11)),("liturgy","Последования Литургии",range(11,16)),("sacraments","Таинства",range(16,21)),("rites","Освящения и погребение",range(21,23)),("history","История богослужения",range(23,26))]
Q=re.compile(r"^\*\*Официальный вопрос:\*\*\s*(.+)$",re.M)
LINK=re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
def pre(title):return "---\nlayout: default\ntitle: "+json.dumps(title,ensure_ascii=False)+"\n---\n\n"
def convert(src,where):
    def fix(m):
        name,target=m.groups()
        if target.startswith(("https://","http://","#","mailto:")): return m.group(0)
        dest=None
        x=re.search(r"(?:^|/)(l[123]|practice|examples)/(q\d\d)\.md$",target)
        if x:
            k,n=x.groups()
            dest=BASE/(f"{n}-{k}.html" if k.startswith("l") else f"{k}/{n}.html")
        x=re.search(r"examples/full/(q\d\d)\.md$",target)
        if x:dest=BASE/"examples/full"/(x.group(1)+".html")
        if "METHODOLOGY-A" in target:dest=BASE/"practice/methodology-a.html"
        if "METHODOLOGY-B" in target:dest=BASE/"practice/methodology-b.html"
        if dest is None:return name
        return "["+name+"]("+posixpath.relpath(str(dest),str(where.parent))+")"
    return LINK.sub(fix,src)
def write(rel,title,text,nav=""):
    dest=ROOT/BASE/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    path=dest.relative_to(ROOT)
    base_link=posixpath.relpath(str(BASE/"index.html"),str(path.parent))
    dest.write_text(pre(title)+"[Литургика — экзамен 2027]("+base_link+")\n\n"+nav+convert(text,path)+"\n",encoding="utf-8")
def main():
    import subject_pdf
    ap=argparse.ArgumentParser();ap.add_argument("--private-root",required=True);ap.add_argument("--source-sha",required=True);ap.add_argument("--check",action="store_true")
    a=ap.parse_args();private=Path(a.private_root);docs={};model={"title":"Литургика — экзамен 2027","sections":[{"id":i,"title":t,"official_numbers":list(rr)} for i,t,rr in GRPS]};rows=[]
    for n in range(1,26):
        docs[n]={}
        for level in LEVELS:
            src=private/"materials/liturgics/2027"/level/f"q{n:02d}.md"
            if not src.exists():raise ValueError("Missing "+str(src))
            docs[n][level]=src.read_text(encoding="utf-8")
        qq=[Q.search(docs[n][l]) for l in LEVELS]
        if any(x is None for x in qq) or len({x.group(1) for x in qq})!=1:raise ValueError("Question mismatch "+str(n))
        question=qq[0].group(1);docs[n]["question"]=question
        group=next(k for k,_,ns in GRPS if n in ns)
        rows.append(dict(official_number=n,canonical_question=n,topic_id=f"liturgics-q{n:02d}",section_id=group,official_question=question,session=0,quality="approved",source_folder="liturgics",source_file=f"q{n:02d}.md"))
    model["topics"]=rows
    if a.check:print("PASS: 25 identical official formulations across L3/L2/L1");return
    for n in range(1,26):
        links=" · ".join(f"[{v.upper()}](q{n:02d}-{v}.html) / [PDF](pdf/q{n:02d}-{v}.pdf)" for v in LEVELS)
        more=f" · [Практикум](practice/q{n:02d}.html) · [Задания](examples/q{n:02d}.html)" if n<=15 else ""
        for level in LEVELS:write(f"q{n:02d}-{level}.md",f"Литургика 2027 №{n} {level.upper()}",docs[n][level],f"**Билет №{n}** · {links}{more}\n\n")
    for n in range(1,16):
        for folder in ("practice","examples"):
            src=private/"materials/liturgics/2027"/folder/f"q{n:02d}.md"
            if not src.is_file():raise ValueError("Missing "+str(src))
            write(f"{folder}/q{n:02d}.md",f"Литургика — {folder} №{n}",src.read_text(encoding="utf-8"),f"[L3](../q{n:02d}-l3.html) · [L2](../q{n:02d}-l2.html) · [L1](../q{n:02d}-l1.html)\n\n")
    for n in range(1,11):
        src=private/"materials/liturgics/2027/examples/full"/f"q{n:02d}.md"
        if not src.is_file():raise ValueError("Missing "+str(src))
        write(f"examples/full/q{n:02d}.md",f"Литургика — образец №{n}",src.read_text(encoding="utf-8"),f"[L3](../../q{n:02d}-l3.html) · [Упражнения](../q{n:02d}.html)\n\n")
    for s,name in (("a","METHODOLOGY-A-SERVICE-COMPOSITION.md"),("b","METHODOLOGY-B-LITURGY-ORDERS.md")):
        src=private/"materials/liturgics/2027/practice"/name
        if not src.is_file():raise ValueError("Missing "+str(src))
        write(f"practice/methodology-{s}.md",f"Литургика — методика {s}",src.read_text(encoding="utf-8"))
    top="# Литургика — официальный экзамен 2027\n\n**Новый перечень: 25 вопросов, 15 практических и 10 теоретических.** Экзамен — 18 мая 2027 года. [Старый перечень и ранее опубликованные ответы](../index.html) сохранены.\n\n"
    top+="[По номерам](numbers.html) · [Методика составления служб](practice/methodology-a.html) · [Методика литургических чинов](practice/methodology-b.html)\n\n**PDF-сборники:** "+ " · ".join(f"[{v.upper()}](pdf/{v}.pdf)" for v in LEVELS)+"\n\n"
    catalog=[top];numbers=["# Литургика — официальные билеты 2027 по номерам\n\n[По смысловым разделам](index.html)\n\n"]
    for ident,title,ns in GRPS:
        catalog.append(f"## {title}\n\n")
        for n in ns:
            entry=f'<div id="q{n:02d}"></div>\n\n**[№{n}. {docs[n]["question"]}](q{n:02d}-l3.html)**\n\n'
            entry+=" · ".join(f"[{v.upper()}](q{n:02d}-{v}.html) · [PDF](pdf/q{n:02d}-{v}.pdf)" for v in LEVELS)
            if n<=15:entry+=f" · [Практика](practice/q{n:02d}.html) · [Упражнения](examples/q{n:02d}.html)"
            catalog.append(entry+"\n\n");numbers.append(entry+"\n\n")
    dest=ROOT/BASE
    (dest/"index.md").write_text(pre("Литургика — новый экзамен 2027")+"".join(catalog),encoding="utf-8")
    (dest/"numbers.md").write_text(pre("Литургика — 25 билетов 2027")+"".join(numbers),encoding="utf-8")
    # Existing PDF renderer + searchable A4 text, Cyrillic, bookmarks and TOC.
    subject_pdf._external_article_link=lambda r,l,slug:f"https://slobodatablichka.github.io/gos-exams-2027-public/subjects/liturgics/2027/q{r['official_number']:02d}-{l}.html"
    manifest={"source_sha":a.source_sha,"pdfs":[]}
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td)
        for level in LEVELS:
            folder=temp/"materials/liturgics"/level;folder.mkdir(parents=True)
            for n in range(1,26):(folder/f"q{n:02d}.md").write_text(convert(docs[n][level],BASE/f"q{n:02d}-{level}.md"),encoding="utf-8")
        for level in LEVELS:
            for n in range(1,26):
                pdf=dest/"pdf"/f"q{n:02d}-{level}.pdf"
                subject_pdf.build_pdf(pdf,model,[rows[n-1]],temp,"liturgics",level,source_ref=a.source_sha)
                manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),**subject_pdf.check_pdf(pdf)))
            pdf=dest/"pdf"/f"{level}.pdf"
            subject_pdf.build_pdf(pdf,model,rows,temp,"liturgics",level,source_ref=a.source_sha,include_index=True)
            manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),**subject_pdf.check_pdf(pdf,full=True,expected_numbers=range(1,26))))
    assert len(manifest["pdfs"])==78
    (dest/"pdf-manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    old=ROOT/"subjects/liturgics/index.md";text=old.read_text(encoding="utf-8")
    if "<!-- liturgics-2027:entry -->" not in text:
        text=text.replace("# Литургика\n","# Литургика\n\n<!-- liturgics-2027:entry -->\n**[Литургика — новый официальный экзамен 2027](2027/index.html)**: 25 вопросов, практические задания, PDF.\n\n*Ниже сохранён прежний вопросник и архивные материалы.*\n",1)
        old.write_text(text,encoding="utf-8")
    cat=ROOT/"subjects/index.md";text=cat.read_text(encoding="utf-8")
    text=text.replace("- [Литургика](liturgics/index.html) — 25 вопросов, L3/L2/L1, PDF.","- **[Литургика — новый экзамен 2027](liturgics/2027/index.html)** — 25 вопросов, L3/L2/L1, задания, PDF.\n- [Литургика — прежний вопросник](liturgics/index.html) — архивные материалы.")
    cat.write_text(text,encoding="utf-8")
    page=ROOT/"materials/index.md";text=page.read_text(encoding="utf-8")
    text=text.replace("[Литургика](../subjects/liturgics/index.html)","[Литургика 2027](../subjects/liturgics/2027/index.html) · [Литургика (архив)](../subjects/liturgics/index.html)",1)
    page.write_text(text,encoding="utf-8")
    # Git diff --check rejects blank lines at EOF in generated Markdown.
    for md in (ROOT/BASE).rglob("*.md"):
        md.write_text(md.read_text(encoding="utf-8").rstrip()+"\n",encoding="utf-8")
    print("PASS: 75 new answers, 15 practice, 15 exercises, 10 full cases, 2 methodologies, 78 PDFs")
if __name__=="__main__":main()
