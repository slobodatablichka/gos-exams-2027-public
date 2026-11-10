#!/usr/bin/env python3
"""Read-only inspect exact TOC anchors in current online BPDS books for source gap closure."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from html.parser import HTMLParser
import json,re
BASE="https://library.logoscosmos.org/bpds/gos-exams-2027/"
PATHS=[
"nt/book-01/index.html","nt/book-02/index.html","nt/book-03/index.html","nt/book-04/index.html",
"ot/book-06/index.html","ot/book-07/index.html","ot/book-09/index.html","ot/book-10/index.html",
"russian-church/book-08/index.html","russian-church/book-12/index.html",
"liturgics/book-13/index.html","liturgics/typikon/index.html","liturgics/averky-taushev/index.html",
"liturgics/book-14/index.html",
"liturgics/book-18/index.html",
"ot/lopukhin/ot/book-10/index.html","ot/lopukhin/ot/book-11/index.html","ot/lopukhin/ot/book-12/index.html",
"ot/lopukhin/ot/book-25/index.html","ot/lopukhin/ot/book-26/index.html","ot/lopukhin/ot/book-27/index.html"
]
class Toc(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.links=[];self.active=None;self.chunks=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if attrs.get("id"):self.ids.add(attrs["id"])
  if attrs.get("name"):self.ids.add(attrs["name"])
  if tag=="a" and (attrs.get("href") or "").startswith("#"):
   self.active=attrs["href"][1:];self.chunks=[]
 def handle_data(self,d):
  if self.active is not None:self.chunks.append(d)
 def handle_endtag(self,tag):
  if tag=="a" and self.active is not None:
   label=" ".join(" ".join(self.chunks).split())
   if len(label)>5:self.links.append({"id":self.active,"heading":label})
   self.active=None;self.chunks=[]
def main():
 result={}
 for path in PATHS:
  url=BASE+path
  try:
   with urlopen(Request(url,headers={"User-Agent":"GosExams-2027-Toc-Audit"}),timeout=18) as r:
    b=r.read(10000000)
    h=Toc();h.feed(b.decode(r.headers.get_content_charset() or "utf-8",errors="replace"))
    seen=set();chapters=[]
    for item in h.links:
     if item["id"] in h.ids and item["id"] not in seen and not re.search(r"--(?:TOC|calibre_toc)",item["id"],re.I):
      seen.add(item["id"]);chapters.append(item)
    result[path]={"http_status":r.status,"total_ids":len(h.ids),"chapters":chapters,"chapter_count":len(chapters),"truncated":len(b)>=10000000}
  except Exception as e:result[path]={"http_status":None,"error":type(e).__name__+": "+str(e)[:180],"chapters":[]}
 out=Path("planning/data/site-2027-library-toc.json")
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({"source":"Live library HTTP downloaded on GitHub Actions, 2026-11-10","books":result},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("LIBRARY_TOC_SUMMARY="+json.dumps({k:{"http":v["http_status"],"chapters":len(v["chapters"]),"error":v.get("error")} for k,v in result.items()},ensure_ascii=False))
if __name__=="__main__":main()
