"use strict";
(()=>{const root=document.getElementById("vm-digital");if(!root)return;
const by=id=>document.getElementById(id),service=by("vm-service"),row=by("vm-row"),table=by("vm-table"),one=by("vm-one"),compare=by("vm-compare"),status=by("vm-status");
let data,mode="full";const iconBase=root.dataset.icons;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=String(text);if(cls)n.className=cls;return n};
function ico(parent,col){if(col.icon){const im=el("img",undefined,"vm-icon");im.src=iconBase+encodeURIComponent(col.icon);im.alt="";parent.append(im)}}
function hdr(col){const n=el("div");ico(n,col);n.append(el("strong",col.short));n.append(el("div",col.context,"vm-sub"));return n}
function val(r,c){return r.cells.find(x=>x.column_id===c.id)?.text??""}
function opt(sel,v,t){const n=el("option",t);n.value=v;sel.add(n)}
function drawFull(){table.replaceChildren();const h=el("thead"),r=el("tr"),first=el("th","Элемент последования","vm-sticky");first.scope="col";r.append(first);for(const c of data.columns){const th=el("th");th.scope="col";th.append(hdr(c));r.append(th)}h.append(r);table.append(h);const body=el("tbody");for(const rr of data.rows){const tr=el("tr"),hd=el("th",rr.section+" — "+rr.label,"vm-sticky");hd.scope="row";tr.append(hd);for(const c of data.columns)tr.append(el("td",val(rr,c)));body.append(tr)}table.append(body)}
function drawOne(){one.replaceChildren();const c=data.columns.find(x=>x.id===service.value)||data.columns[0],h=el("div",undefined,"vm-card"),title=el("h3");title.append(hdr(c));h.append(title,el("div",c.group,"vm-sub"));one.append(h);let group="";for(const r of data.rows){if(group!==r.section){group=r.section;one.append(el("h3",group))}const card=el("div",undefined,"vm-card");card.append(el("h4",r.label),el("div",val(r,c),"vm-entry"));one.append(card)}}
function drawCompare(){compare.replaceChildren();const r=data.rows.find(x=>x.id===row.value)||data.rows[0];compare.append(el("h3",r.section+" — "+r.label));const grid=el("div",undefined,"vm-grid");for(const c of data.columns){const card=el("div",undefined,"vm-card"),h=el("h4");h.append(hdr(c));card.append(h,el("div",val(r,c),"vm-entry"));grid.append(card)}compare.append(grid)}
function view(next){mode=next;for(const b of root.querySelectorAll("[data-vm-view]"))b.setAttribute("aria-pressed",String(b.dataset.vmView===next));by("vm-full").hidden=next!=="full";one.hidden=next!=="service";compare.hidden=next!=="compare";if(!data)return;if(next==="service")drawOne();if(next==="compare")drawCompare()}
root.querySelectorAll("[data-vm-view]").forEach(b=>b.addEventListener("click",()=>view(b.dataset.vmView)));
service.addEventListener("change",()=>{if(mode==="service")drawOne()});
row.addEventListener("change",()=>{if(mode==="compare")drawCompare()});
by("vm-scale").addEventListener("change",e=>{table.style.fontSize=e.target.value+"px"});
async function load(){const res=await fetch(root.dataset.source);if(!res.ok)throw Error("HTTP "+res.status);const b64=(await res.text()).trim();const raw=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const stream=new Blob([raw]).stream().pipeThrough(new DecompressionStream("deflate"));const json=new TextDecoder("utf-8").decode(await new Response(stream).arrayBuffer());data=JSON.parse(json);
if(data.columns?.length!==17||data.rows?.length!==23||data.rows.some(r=>r.cells.length!==17))throw Error("Неверная структура таблицы");
for(const c of data.columns)opt(service,c.id,c.group+" — "+c.short+" — "+c.context);
for(const r of data.rows)opt(row,r.id,r.section+" — "+r.label);
drawFull();drawOne();drawCompare();view("full");status.textContent=""}
load().catch(e=>{status.textContent="Не удалось загрузить таблицу.";console.error(e)})})();
