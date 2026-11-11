#!/usr/bin/env python3
"""Generate independent 2027 Dogmatics pages and PDFs."""
import argparse,csv,json,posixpath,re,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=Path("subjects/dogmatics/2027")
LEVELS=("l3","l2","l1")
GROUPS=[("basics","Основы догматики",range(1,6)),("christology","Творение и христология",range(6,11)),("salvation","Спасение, Церковь и последние судьбы",range(11,16)),("practical","Практические задания",range(16,26))]
Q=re.compile(r"^> \*\*Официальный вопрос\.\*\*\s*(.+)$",re.M)
LINK=re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
def pre(t):return "---\nlayout: default\ntitle: "+json.dumps(t,ensure_ascii=False)+"\n---\n\n"
def norm(t):return re.sub(r"\s+"," ",t.replace("**","").strip())
def sec(s,h):
    m=re.search(r"^## "+re.escape(h)+r"\s*\n([\s\S]*?)(?=^## |\Z)",s,re.M)
    if not m:raise ValueError("Missing section: "+h)
    return norm(m.group(1))
def convert(s,where):
    def fix(m):
        name,target=m.groups()
        if target.startswith(("http://","https://","#","mailto:")):return m.group(0)
        dest=None
        q=re.search(r"(?:^|/)(l1|l2|l3)/(q\d\d)\.md$",target)
        if q:dest=BASE/(q.group(2)+"-"+q.group(1)+".html")
        q=re.search(r"(?:^|/)practice/(practicum-\d\d|methodology|heresy-comparison)\.md$",target)
        if q:dest=BASE/"practice"/(q.group(1)+".html")
        if re.fullmatch(r"practicum-\d\d\.md|methodology\.md|heresy-comparison\.md",target):
            dest=BASE/"practice"/(target[:-3]+".html")
        return "["+name+"]("+posixpath.relpath(str(dest),str(where.parent))+")" if dest else name
    return LINK.sub(fix,s)
def write(rel,title,body,nav=""):
    file=ROOT/BASE/rel;file.parent.mkdir(parents=True,exist_ok=True)
    rp=file.relative_to(ROOT)
    home=posixpath.relpath(str(BASE/"index.html"),str(rp.parent))
    file.write_text(pre(title)+"[Догматика — 2027]("+home+")\n\n"+nav+convert(body,rp).rstrip()+"\n",encoding="utf-8")
def main():
    import subject_pdf
    from reportlab import rl_config
    rl_config.invariant=1
    a=argparse.ArgumentParser();a.add_argument("--private-root",required=True);a.add_argument("--source-sha",required=True);a.add_argument("--check",action="store_true");arg=a.parse_args()
    private=Path(arg.private_root)
    with (private/"research/dogmatics/2027/quality-status.csv").open(encoding="utf-8") as f:
        statuses={x["question"]:x for x in csv.DictReader(f)}
    assert len(statuses)==25
    docs,rows={},[]
    for n in range(1,26):
        key=f"q{n:02d}";quality=statuses[key]
        required="review_pending" if n==23 else "approved"
        if quality["sources"]!="done" or quality["quality"]!=required:raise ValueError("Quality gate: "+key)
        docs[n]={}
        for level in LEVELS:
            f=private/"materials/dogmatics/2027"/level/(key+".md")
            if not f.is_file():raise ValueError("Missing "+str(f))
            docs[n][level]=f.read_text(encoding="utf-8")
        if n<=15:
            qq=[Q.search(docs[n][level]) for level in LEVELS]
            if any(x is None for x in qq) or len({norm(x.group(1)) for x in qq})!=1:raise ValueError("Formulation mismatch "+key)
            question=qq[0].group(1)
        else:
            tasks=[sec(docs[n][lev],"Официальное задание") for lev in LEVELS]
            fragments=[sec(docs[n][lev],"Официальный текст" if lev=="l1" else "Официальный текст для разбора") for lev in LEVELS]
            if len(set(tasks))!=1 or len(set(fragments))!=1:raise ValueError("Practical mismatch "+key)
            question=f"Практическое задание №{n-15}. Выявление и опровержение еретических положений"
        if n==23 and not all("П8" in docs[n][lev] or "сложная природ" in docs[n][lev].lower() for lev in LEVELS):
            raise ValueError("Missing P8 status")
        group=next(code for code,_,ns in GROUPS if n in ns)
        rows.append(dict(official_number=n,canonical_question=n,topic_id=f"dogmatics-2027-q{n:02d}",section_id=group,official_question=question,session=0,quality=required,source_folder="dogmatics",source_file=key+".md"))
    if arg.check:
        print("PASS: 25 matching triplets, quality gates, 10 practical originals");return
    banner="\n\n> **Рабочая редакция (review_pending).** Практическое №8 содержит монофизитское, монофелитское/моноэнергистское и пелагианское заблуждения. Требование назвать две ереси нуждается в уточнении; окончательный допуск не утверждён.\n\n"
    for n in range(1,26):
        key=f"q{n:02d}"
        links=" · ".join(f"[{lev.upper()}]({key}-{lev}.html) · [PDF](pdf/{key}-{lev}.pdf)" for lev in LEVELS)
        if n>=16:links+=f" · [Практикум](practice/practicum-{n-15:02d}.html)"
        for lev in LEVELS:
            write(f"{key}-{lev}.md",f"Догматика 2027 №{n} {lev.upper()}",(banner if n==23 else "")+docs[n][lev],"**Билет №"+str(n)+"** · "+links+"\n\n")
    folder=private/"materials/dogmatics/2027/practice"
    for name in ("methodology","heresy-comparison")+tuple(f"practicum-{i:02d}" for i in range(1,11)):
        f=folder/(name+".md")
        if not f.is_file():raise ValueError("Missing "+str(f))
        n=int(name[-2:]) if name.startswith("practicum") else None
        nav=f"[L3](../q{n+15:02d}-l3.html) · [L2](../q{n+15:02d}-l2.html) · [L1](../q{n+15:02d}-l1.html)\n\n" if n else ""
        write("practice/"+name+".md","Догматика 2027 — "+name,f.read_text(encoding="utf-8"),nav)
    head=("# Догматическое богословие — экзамен 2027\n\n**15 теоретических вопросов и 10 практических заданий.** "
          "[Прежний вопросник и материалы](../index.html) сохранены.\n\n"
          "[По номерам](numbers.html) · [Методика](practice/methodology.html) · [Таблица ересей](practice/heresy-comparison.html)\n\n"
          "**PDF-сборники:** [L3](pdf/l3.pdf) · [L2](pdf/l2.pdf) · [L1](pdf/l1.pdf)\n\n"
          "**Практическое №8:** [рабочая редакция, требуется уточнение](source-status.html).\n\n")
    catalog=[head];numbers=["# Догматика 2027 — билеты по номерам\n\n[По смысловым разделам](index.html)\n\n"]
    for group,title,nums in GROUPS:
        catalog.append(f"## {title}\n\n")
        for n in nums:
            key=f"q{n:02d}"
            entry=f"**[№{n}. {rows[n-1]['official_question']}]({key}-l3.html)**"+(" **(рабочая редакция)**" if n==23 else "")+"\n\n"
            entry+=" · ".join(f"[{lev.upper()}]({key}-{lev}.html) · [PDF](pdf/{key}-{lev}.pdf)" for lev in LEVELS)
            if n>=16:entry+=f" · [Практикум](practice/practicum-{n-15:02d}.html)"
            catalog.append(entry+"\n\n");numbers.append(entry+"\n\n")
    dest=ROOT/BASE;dest.mkdir(parents=True,exist_ok=True)
    (dest/"index.md").write_text(pre("Догматика — экзамен 2027")+"".join(catalog),encoding="utf-8")
    (dest/"numbers.md").write_text(pre("Догматика — номера 2027")+"".join(numbers),encoding="utf-8")
    write("source-status.md","Догматика 2027 — статус практического №8",
          "# Статус практического задания №8\n\n**Рабочая редакция (review_pending).** В тексте есть монофизитская формула «одна сложная природа», монофелитская/моноэнергистская формула об одной Божественной воле и действии, а также пелагианское положение о спасении без благодати. Термин «сложная Ипостась» сам по себе допустим. Формальное требование комиссии о двух ересях нуждается в уточнении. [L3](q23-l3.html) · [L2](q23-l2.html) · [L1](q23-l1.html) · [Практикум](practice/practicum-08.html).\n")
    model=dict(title="Догматическое богословие — экзамен 2027",sections=[dict(id=group,title=title,official_numbers=list(nums)) for group,title,nums in GROUPS],topics=rows)
    subject_pdf._external_article_link=lambda row,lev,slug:f"https://slobodatablichka.github.io/gos-exams-2027-public/subjects/dogmatics/2027/q{row['official_number']:02d}-{lev}.html"
    manifest=dict(source_sha=arg.source_sha,pdfs=[])
    with tempfile.TemporaryDirectory() as td:
        base=Path(td)
        for lev in LEVELS:
            loc=base/"materials/dogmatics"/lev;loc.mkdir(parents=True)
            for n in range(1,26):
                source=(banner if n==23 else "")+docs[n][lev]
                (loc/f"q{n:02d}.md").write_text(convert(source,BASE/f"q{n:02d}-{lev}.md"),encoding="utf-8")
        for lev in LEVELS:
            for n in range(1,26):
                pdf=dest/"pdf"/f"q{n:02d}-{lev}.pdf"
                subject_pdf.build_pdf(pdf,model,[rows[n-1]],base,"dogmatics",lev,source_ref=arg.source_sha)
                manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),**subject_pdf.check_pdf(pdf)))
            pdf=dest/"pdf"/f"{lev}.pdf"
            subject_pdf.build_pdf(pdf,model,rows,base,"dogmatics",lev,source_ref=arg.source_sha,include_index=True)
            manifest["pdfs"].append(dict(file=pdf.relative_to(dest).as_posix(),**subject_pdf.check_pdf(pdf,full=True,expected_numbers=range(1,26))))
    assert len(manifest["pdfs"])==78
    (dest/"pdf-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    archive=ROOT/"subjects/dogmatics/index.md";txt=archive.read_text(encoding="utf-8")
    marker="<!-- dogmatics-2027:entry -->"
    if marker not in txt:
        anchor="# Догматическое богословие\n"
        if anchor not in txt:raise ValueError("Legacy heading missing")
        txt=txt.replace(anchor,anchor+"\n"+marker+"\n**[Догматика — экзамен 2027](2027/index.html)**: 15 теоретических, 10 практических, L3/L2/L1 и PDF.\n\n*Ниже сохранён прежний вопросник.*\n",1)
        archive.write_text(txt,encoding="utf-8")
    for name,old,new in [
        ("subjects/index.md","- [Догматическое богословие](dogmatics/index.html) — 25 вопросов, L3/L2/L1, PDF.","- **[Догматика — новый экзамен 2027](dogmatics/2027/index.html)** — 25 вопросов, материалы и PDF.\n- [Догматика — архив](dogmatics/index.html) — старый вопросник."),
        ("materials/index.md","[Догматика](../subjects/dogmatics/index.html)","[Догматика 2027](../subjects/dogmatics/2027/index.html) · [Догматика (архив)](../subjects/dogmatics/index.html)"),
        ("index.md","[Догматика](subjects/dogmatics/index.html)","[Догматика 2027](subjects/dogmatics/2027/index.html) · [Догматика (архив)](subjects/dogmatics/index.html)")]:
        f=ROOT/name;t=f.read_text(encoding="utf-8")
        if old not in t and new not in t:continue  # New-only navigation
        if old in t:f.write_text(t.replace(old,new,1),encoding="utf-8")
    for file in dest.rglob("*.md"):file.write_text(file.read_text(encoding="utf-8").rstrip()+"\n",encoding="utf-8")
    print("PASS: 75 subject answers, 12 practice pages, 78 PDFs, q23 working")
if __name__=="__main__":main()
