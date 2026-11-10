#!/usr/bin/env python3
"""Read actual chapter filenames AND labels from the published multi-file liturgical books."""
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser
from pathlib import Path
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
 f=Path("planning/data/site-2027-liturgy-exact-sections.json");f.parent.mkdir(parents=True,exist_ok=True)
 f.write_text(json.dumps({"date":"2026-11-10","source":"Live BPDS published index links, not guessed from EPUB numbering","books":out},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("FLAT_SECTIONS="+json.dumps({b:{"count":len(v["sections"]),"first":v["sections"][:4]} for b,v in out.items()},ensure_ascii=False))
if __name__=="__main__":main()
