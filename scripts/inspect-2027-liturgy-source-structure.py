#!/usr/bin/env python3
"""Inspect published flat liturgy source structure, without modifying library server."""
from urllib.request import Request,urlopen
from html.parser import HTMLParser
from pathlib import Path
import re,json
BASE="https://library.logoscosmos.org/bpds/gos-exams-2027/liturgics/"
class Inspect(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.headings=[];self.ids=[];self.tag=None;self.parts=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if "id" in attrs and len(self.ids)<20:self.ids.append(attrs["id"])
  if tag=="a" and attrs.get("href") and len(self.links)<90:self.links.append(attrs["href"])
  if re.fullmatch("h[1-6]",tag) and self.tag is None:self.tag=tag;self.parts=[]
 def handle_data(self,data):
  if self.tag:self.parts.append(data)
 def handle_endtag(self,tag):
  if self.tag==tag:
   val=" ".join(" ".join(self.parts).split())
   if val and len(self.headings)<70:self.headings.append([tag,val[:160]])
   self.tag=None
def main():
 out={}
 for name in ("book-18","typikon","averky-taushev"):
  url=BASE+name+"/index.html"
  with urlopen(Request(url,headers={"User-Agent":"GosExams-2027-inspect"}),timeout=20) as r:
   dat=r.read(3500000);p=Inspect();p.feed(dat.decode(r.headers.get_content_charset() or "utf-8",errors="replace"))
   out[name]={"status":r.status,"content_type":r.headers.get("Content-Type"),"first_html":dat[:250].decode("utf-8",errors="replace"),"links":p.links,"headings":p.headings,"ids_sample":p.ids,"bytes_read":len(dat)}
 f=Path("planning/data/site-2027-liturgy-unanchored-sources.json");f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("LITURGY_STRUCTURE="+json.dumps({name:{"status":x["status"],"header_count":len(x["headings"]),"links":len(x["links"]),"id_count_sample":len(x["ids_sample"]),"first":x["first_html"][:110]} for name,x in out.items()},ensure_ascii=False))
if __name__=="__main__":main()
