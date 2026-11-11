#!/usr/bin/env python3
"""Build approved Church History 2027 pages and real PDFs, preserving legacy pages."""
import argparse,csv,json,re,posixpath,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path("subjects/rpc/2027")
LEVELS=("l3","l2","l1")
GROUPS=[("origins","Крещение Руси и объединение земель",range(1,6)),
("moscow","Московская Русь и Патриаршество",range(6,11)),
("empire","Синодальная эпоха и начало гонений",range(11,16)),
("soviet","Гонения XX века и современная история",range(16,21)),
("themes","Монашество, образование, миссии и зарубежье",range(21,26))]
QUESTION=re.compile(r"^> \*\*Официальная формулировка:\*\*\s*(.+)$",re.M)
LINK=re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
def front(title):return "---\nlayout: default\ntitle: "+json.dumps(title,ensure_ascii=False)+"\n---\n\n"
def norm(s):return re.sub(r"\s+"," ",s.replace("**","").strip())
def convert(text,where):
    def fix(m):
        label,target=m.groups()
        if target.startswith(("https://","http://","#","mailto:")):return m.group(0)
        q=re.search(r"(?:^|/)(l[123])/(q\d\d)\.md$",target)
        if q:
            level,key=q.groups()
            dest=BASE/(key+"-"+level+".html")
            return "["+label+"]("+posixpath.relpath(str(dest),str(where.parent))+")"
        return label
    return LINK.sub(fix,text)
def write(rel,title,body,nav=""):
    target=ROOT/BASE/rel;target.parent.mkdir(parents=True,exist_ok=True)
    p=target.relative_to(ROOT)
    home=posixpath.relpath(str(BASE/"index.html"),str(p.parent))
    target.write_text(front(title)+"[История Русской Православной Церкви — 2027]("+home+")\n\n"+
        nav+convert(body,p).rstrip()+"\n",encoding="utf-8")
def patch(path,old,new):
    p=ROOT/path;text=p.read_text(encoding="utf-8")
    if new in text:return
    if old not in text:return  # New-only navigation has no archive anchor
    p.write_text(text.replace(old,new,1),encoding="utf-8")
def main():
    import subject_pdf
    from reportlab import rl_config
    rl_config.invariant=1
    ap=argparse.ArgumentParser()
    ap.add_argument("--private-root",required=True)
    ap.add_argument("--source-sha",required=True)
    ap.add_argument("--check",action="store_true")
    a=ap.parse_args();private=Path(a.private_root)
    with (private/"research/church-history/2027/rpc-quality-status.csv").open(encoding="utf-8",newline="") as f:
        statuses={int(x["question"]):x for x in csv.DictReader(f)}
    if set(statuses)!=set(range(1,26)):raise ValueError("Missing quality statuses")
    docs,rows={},[]
    for n in range(1,26):
        if statuses[n]["quality"]!="approved":raise ValueError("Not approved "+str(n))
        docs[n]={};key=f"q{n:02d}"
        for level in LEVELS:
            docs[n][level]=(private/"materials/rpc/2027"/level/(key+".md")).read_text(encoding="utf-8")
        matches=[QUESTION.search(docs[n][level]) for level in LEVELS]
        if not all(matches) or len({norm(x.group(1)) for x in matches})!=1:
            raise ValueError("Official question mismatch "+key)
        group=next(code for code,_,ns in GROUPS if n in ns)
        rows.append(dict(official_number=n,canonical_question=n,
            topic_id="rpc-2027-"+key,section_id=group,
            official_question=matches[0].group(1),session=0,
            quality="approved",source_folder="rpc",source_file=key+".md"))
    if a.check:
        print("PASS: 25 quality approvals and identical official texts in 75 files");return
    dest=ROOT/BASE
    for n in range(1,26):
        key=f"q{n:02d}"
        nav="**Билет №"+str(n)+"** · "+" · ".join(
            f"[{v.upper()}]({key}-{v}.html) · [PDF](pdf/{key}-{v}.pdf)" for v in LEVELS)+"\n\n"
        for level in LEVELS:
            write(f"{key}-{level}.md",f"История Русской Православной Церкви 2027 №{n} {level.upper()}",
                docs[n][level],nav)
    top=("# История Русской Православной Церкви — экзамен 2027\n\n"
        "**25 новых официальных вопросов, L3/L2/L1 и PDF.** "
        "[Прежний вопросник и материалы](../index.html) сохранены.\n\n"
        "[По номерам](numbers.html) · [Все предметы](../../index.html) · "
        "[Библиотека БПДС](https://library.logoscosmos.org/bpds/gos-exams-2027/)\n\n"
        "**PDF-сборники:** "+" · ".join(f"[{v.upper()}](pdf/{v}.pdf)" for v in LEVELS)+"\n\n")
    catalog=[top];numbers=["# История Русской Православной Церкви 2027 — по номерам\n\n[По разделам](index.html)\n\n"]
    for group,title,ns in GROUPS:
        catalog.append(f"## {title}\n\n")
        for n in ns:
            key=f"q{n:02d}"
            item=(f'<div id="{key}"></div>\n\n**[№{n}. {rows[n-1]["official_question"]}]({key}-l3.html)**\n\n'
                +" · ".join(f"[{v.upper()}]({key}-{v}.html) · [PDF](pdf/{key}-{v}.pdf)" for v in LEVELS)+"\n\n")
            catalog.append(item);numbers.append(item)
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"index.md").write_text(front("История Русской Православной Церкви — экзамен 2027")+"".join(catalog),encoding="utf-8")
    (dest/"numbers.md").write_text(front("История Русской Православной Церкви — 25 билетов 2027")+"".join(numbers),encoding="utf-8")
    model=dict(title="История Русской Православной Церкви — экзамен 2027",
        sections=[dict(id=code,title=title,official_numbers=list(ns)) for code,title,ns in GROUPS],
        topics=rows)
    subject_pdf._external_article_link=lambda row,lev,slug:(
        f"https://slobodatablichka.github.io/gos-exams-2027-public/"
        f"subjects/rpc/2027/q{row['official_number']:02d}-{lev}.html")
    manifest=dict(source_sha=a.source_sha,pdfs=[])
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for lev in LEVELS:
            folder=root/"materials/rpc"/lev;folder.mkdir(parents=True)
            for n in range(1,26):
                key=f"q{n:02d}"
                (folder/(key+".md")).write_text(
                    convert(docs[n][lev],BASE/(key+"-"+lev+".md")),encoding="utf-8")
        for lev in LEVELS:
            for n in range(1,26):
                pdf=dest/"pdf"/f"q{n:02d}-{lev}.pdf"
                subject_pdf.build_pdf(pdf,model,[rows[n-1]],root,"rpc",lev,source_ref=a.source_sha)
                manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),**subject_pdf.check_pdf(pdf)))
            pdf=dest/"pdf"/f"{lev}.pdf"
            subject_pdf.build_pdf(pdf,model,rows,root,"rpc",lev,source_ref=a.source_sha,include_index=True)
            manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),
                **subject_pdf.check_pdf(pdf,full=True,expected_numbers=range(1,26))))
    if len(manifest["pdfs"])!=78:raise ValueError("Expected 78 PDF files")
    (dest/"pdf-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    old=ROOT/"subjects/rpc/index.md";txt=old.read_text(encoding="utf-8")
    if "<!-- rpc-2027:entry -->" not in txt:
        anchor="# История Русской Православной Церкви\n"
        if anchor not in txt:raise ValueError("Old catalog header missing")
        txt=txt.replace(anchor,anchor+"\n<!-- rpc-2027:entry -->\n"
            "**[Новые вопросы экзамена 2027](2027/index.html)** — 25 L3/L2/L1 и PDF.\n\n"
            "*Ниже сохранён прежний вопросник.*\n",1)
        old.write_text(txt,encoding="utf-8")
    patch("subjects/index.md",
        "- [История Русской Православной Церкви](rpc/index.html) — 25 вопросов, L3/L2/L1, PDF.",
        "- **[История Русской Православной Церкви — экзамен 2027](rpc/2027/index.html)** — 25 вопросов, L3/L2/L1, PDF.\n"
        "- [История Русской Православной Церкви — архив](rpc/index.html) — старый вопросник.")
    patch("materials/index.md",
        "[История РПЦ](../subjects/rpc/index.html)",
        "[История Русской Православной Церкви 2027](../subjects/rpc/2027/index.html) · [ИРПЦ (архив)](../subjects/rpc/index.html)")
    patch("index.md",
        "[История РПЦ](subjects/rpc/index.html)",
        "[История Русской Православной Церкви 2027](subjects/rpc/2027/index.html) · [ИРПЦ (архив)](subjects/rpc/index.html)")
    for page in dest.rglob("*.md"):
        page.write_text(page.read_text(encoding="utf-8").rstrip()+"\n",encoding="utf-8")
    print("PASS: RPC 2027 — 75 articles, 78 PDFs, catalogs, legacy protected")
if __name__=="__main__":main()
