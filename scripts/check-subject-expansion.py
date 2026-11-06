#!/usr/bin/env python3
"""Acceptance of staged OI/RPC/Liturgics without modifying the published site."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SLUGS=("oi","rpc","liturgics")
LEVELS=("l3","l2","l1")
START="<!-- subject-navigation:begin -->"
END="<!-- subject-navigation:end -->"

def check(stage,original,private):
    count=0
    original_paths=set()
    working=0
    targets=set()
    for slug in SLUGS:
        m=json.loads((private/"planning"/("subject-order-"+slug+".json")).read_text(encoding="utf-8"))
        rows=m["topics"]
        if len(rows)!=25 or set(r["official_number"] for r in rows)!=set(range(1,26)):
            raise ValueError("Question inventory: "+slug)
        folder=stage/"subjects"/slug
        for page in ("index.md","numbers.md"):
            body=(folder/page).read_text(encoding="utf-8")
            for n in range(1,26):
                if ("number-q%02d"%n) not in body:
                    raise ValueError("Missing numeric anchor: "+slug+" "+str(n))
                if page=="index.md" and ("meaning-q%02d"%n) not in body:
                    raise ValueError("Missing semantic anchor: "+slug+" "+str(n))
        manifest=json.loads((folder/"pdf-manifest.json").read_text(encoding="utf-8"))
        if len(manifest["files"])!=78 or manifest["pdf_count"]!=78:
            raise ValueError("PDF inventory: "+slug)
        for item in manifest["files"]:
            file=folder/item["file"]
            if not file.is_file() or file.stat().st_size!=item["bytes"]:
                raise ValueError("Missing/changed PDF: "+str(file))
            if hashlib.sha256(file.read_bytes()).hexdigest()!=item["sha256"]:
                raise ValueError("PDF hash mismatch: "+str(file))
        for row in rows:
            if row["site"]=="published_working":
                working+=1
                if row["quality"]=="approved" or not (stage/row["working_notice_url"].replace(".html",".md")).is_file():
                    raise ValueError("Working status/notice incorrect")
            for level in LEVELS:
                url=row["level_urls"][level]
                original_md=original/url.replace(".html",".md")
                staged_md=stage/url.replace(".html",".md")
                if not original_md.is_file() or not staged_md.is_file():
                    raise ValueError("Original route lost: "+url)
                old=original_md.read_text(encoding="utf-8")
                new=staged_md.read_text(encoding="utf-8")
                if new.count(START)!=1 or new.count(END)!=1:
                    raise ValueError("Managed return link missing: "+url)
                def legacy_body(txt):
                    if START not in txt:
                        return txt
                    return re.sub(re.escape(START)+r"\n.*?\n"+re.escape(END)+r"\n\n?", "",txt,count=1,flags=re.S)
                if legacy_body(new)!=legacy_body(old):
                    raise ValueError("Legacy article altered outside managed block: "+url)
                block=new.split(START)[1].split(END)[0]
                for fragment in ("meaning-q%02d"%row["official_number"],"number-q%02d"%row["official_number"]):
                    if fragment not in block:
                        raise ValueError("Reverse anchor missing: "+url)
                original_paths.add(url)
                count+=1
                targets.add(url)
    if count!=225 or len(original_paths)!=225 or working!=6:
        raise ValueError("Incorrect final inventory: %d articles, %d working"%(count,working))
    catalog=(stage/"subjects/index.md").read_text(encoding="utf-8")
    for slug in SLUGS:
        if ("("+slug+"/index.html)") not in catalog:
            raise ValueError("Missing expanded catalog entry: "+slug)
        for p in ("index.md","materials/index.md"):
            if ("subjects/"+slug+"/index.html") not in (stage/p).read_text(encoding="utf-8"):
                raise ValueError("Missing site entry: "+p+" "+slug)
    for p in ("index.md","materials/index.md","assets/css/style.scss"):
        old=(original/p).read_text(encoding="utf-8")
        new=(stage/p).read_text(encoding="utf-8")
        start,end= ("/* subject-navigation:begin */","/* subject-navigation:end */") if p.endswith(".scss") else (START,END)
        if old.count(start)!=1 or new.count(start)!=1:
            raise ValueError("Existing managed region lost "+p)
        def outside(txt):return txt.split(start)[0]+txt.split(end)[1]
        if outside(old)!=outside(new):
            raise ValueError("Legacy header/style modified outside managed region "+p)
    print("FINAL PASS: 75 official numbers, 225 preserved existing HTML routes, 225 reverse navigation links, 234 verified PDF files, 6 working editions, 3 subject entry points")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--private",type=Path,required=True)
    args=p.parse_args()
    check(args.stage,args.original,args.private)
