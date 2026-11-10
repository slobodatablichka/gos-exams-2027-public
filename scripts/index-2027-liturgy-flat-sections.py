#!/usr/bin/env python3
"""Read actual chapter filenames AND labels from the published multi-file liturgical books."""
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser
from pathlib import Path
import re
import json
BASE="https://library.logoscosmos.org/bpds/gos-exams-2027/liturgics/"
BOOKS=("typikon","averky-taushev","book-18")
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None;self.parts=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=="a" and (attrs.get("href") or "").startswith("index_split_"):
   self.current=attrs["href"];self.parts=[]
 def handle_data(self,data):
  if self.current is not None:self.parts.append(data)
 def handle_endtag(self,tag):
  if tag=="a" and self.current is not None:
   self.links.append({"file":self.current,"label":" ".join(" ".join(self.parts).split())})
   self.current=None
def main():
 out={}
 for book in BOOKS:
  index=BASE+book+"/index.html"
  with urlopen(Request(index,headers={"User-Agent":"GosExams-2027-exact-sections"}),timeout=18) as f:
   data=f.read(2500000);p=Links();p.feed(data.decode(f.headers.get_content_charset() or "utf-8",errors="replace"))
   out[book]={"index_http":f.status,"sections":[{"file":l["file"],"title":l["label"],"url":urljoin(index,l["file"])} for l in p.links]}
 targets={
  "liturgics-2027-01":[("typikon","index_split_012.xhtml"),("typikon","index_split_013.xhtml")],
  "liturgics-2027-02":[("typikon","index_split_003.xhtml"),("typikon","index_split_004.xhtml")],
  "liturgics-2027-07":[("typikon","index_split_092.xhtml")],
  "liturgics-2027-12":[("book-18","index_split_036.xhtml"),("book-18","index_split_045.xhtml")],
  "liturgics-2027-13":[("book-18","index_split_052.xhtml")],
  "liturgics-2027-14":[("book-18","index_split_046.xhtml")],
  "liturgics-2027-23":[("book-18","index_split_029.xhtml")],
  "liturgics-2027-24":[("book-18","index_split_030.xhtml")],
  "liturgics-2027-25":[("averky-taushev","index_split_003.xhtml")]
 }
 checks={}
 for q,pairs in targets.items():
  checks[q]=[]
  for book,name in pairs:
   entry=next((e for e in out[book]["sections"] if e["file"]==name),None)
   if not entry:
    checks[q].append({"book":book,"file":name,"status":"not_in_live_index"})
    continue
   try:
    with urlopen(Request(entry["url"],headers={"User-Agent":"GosExams-2027-exact-sections"}),timeout=15) as resp:
     content=resp.read(2500000)
     text=content.decode(resp.headers.get_content_charset() or "utf-8",errors="replace")
     russian_terms=bool(re.search("Русск|Российск|Киевск|Московск|Студийск",text,re.I))
     checks[q].append({"book":book,"file":name,"url":entry["url"],"title":entry["title"],"http_status":resp.status,"bytes":len(content),"contains_russian_church_terms":russian_terms})
   except Exception as e:
    checks[q].append({"book":book,"file":name,"url":entry["url"],"http_status":None,"error":type(e).__name__+": "+str(e)[:120]})
 outdata={"date":"2026-11-10","source":"Actual public library index links, independent chapter URL HTTP test","books":out,"verified_targets":checks}
 f=Path("planning/data/site-2027-liturgy-exact-sections.json");f.parent.mkdir(parents=True,exist_ok=True)
 f.write_text(json.dumps(outdata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("FLAT_SECTIONS="+json.dumps({b:{"count":len(v["sections"]),"first":v["sections"][:4]} for b,v in out.items()},ensure_ascii=False))
if __name__=="__main__":main()
