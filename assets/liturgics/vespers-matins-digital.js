"use strict";
(()=>{const root=document.getElementById("vm-digital");if(!root)return;
const by=id=>document.getElementById(id),service=by("vm-service"),row=by("vm-row"),table=by("vm-table"),one=by("vm-one"),compare=by("vm-compare"),status=by("vm-status");
let data,mode="full";const iconBase=root.dataset.icons;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=String(text);if(cls)n.className=cls;return n};
function ico(parent,col){for(const icon of (col.icons?.length?col.icons:(col.icon?[col.icon]:[]))){const im=el("img",undefined,"vm-icon");im.src=iconBase+encodeURIComponent(icon);im.alt="";parent.append(im)}}
function hdr(col){const n=el("div");ico(n,col);n.append(el("strong",col.short));n.append(el("div",col.context,"vm-sub"));if(col.typikon)n.append(el("div",col.typikon,"vm-sub"));return n}
function val(r,c){return r.cells.find(x=>x.column_id===c.id)?.text??""}
function opt(sel,v,t){const n=el("option",t);n.value=v;sel.add(n)}
function drawFull(){
  table.replaceChildren();
  const layout=data.source_layout;
  const h=el("thead"),groups=el("tr"),titles=el("tr");
  const first=el("th","Элемент последования","vm-sticky");first.scope="col";first.rowSpan=2;groups.append(first);
  for(const g of layout.column_groups){
    const th=el("th",g.title);th.scope="colgroup";th.colSpan=g.colspan;th.className="vm-group";groups.append(th);
  }
  for(const c of data.columns){const th=el("th");th.scope="col";th.append(hdr(c));titles.append(th)}
  h.append(groups,titles);table.append(h);
  const body=el("tbody"),byId=new Map(data.rows.map((r,i)=>[r.id,i]));
  const bandCount=new Map();
  for(const b of layout.body_bands)bandCount.set(b.row_id,(bandCount.get(b.row_id)||0)+1);
  const origins=new Map(),covered=new Set();
  const cellKey=(r,c)=>r+":"+c;
  for(const m of layout.merged_regions){
    const ids=[...new Set(layout.body_bands.slice(m.row_start,m.row_start+m.rowspan).map(b=>b.row_id))];
    if(ids.length===1&&m.rowspan>1)continue;
    if(ids.some(id=>bandCount.get(id)!==1))continue;
    const rowIndices=ids.map(id=>byId.get(id));
    if(rowIndices.some(i=>i===undefined))continue;
    const top=Math.min(...rowIndices),height=Math.max(...rowIndices)-top+1;
    if(height!==rowIndices.length)continue;
    const col=m.col_start;
    const firstKey=cellKey(top,col);
    if(origins.has(firstKey))continue;
    const items=[];
    for(const r of rowIndices){
      for(let c=col;c<col+m.colspan;c++)items.push(cellKey(r,c));
    }
    if(items.some(k=>covered.has(k)))continue;
    origins.set(firstKey,{rowspan:height,colspan:m.colspan,rows:rowIndices});
    for(const k of items)if(k!==firstKey)covered.add(k);
  }
  data.rows.forEach((rr,r)=>{
    const tr=el("tr");
    for(let c=0;c<=data.columns.length;c++){
      const key=cellKey(r,c);if(covered.has(key))continue;
      const merge=origins.get(key);
      const node=c===0?el("th",null,"vm-sticky"):el("td");
      if(c===0)node.scope="row";
      if(merge){node.rowSpan=merge.rowspan;node.colSpan=merge.colspan}
      let parts=[];
      for(const ri of merge?.rows||[r]){
        const rowObj=data.rows[ri];
        if(c===0){parts.push(rowObj.section+" — "+rowObj.label)}
        else for(let ci=c;ci<c+(merge?.colspan||1);ci++)parts.push(val(rowObj,data.columns[ci]));
      }
      parts=parts.filter(Boolean);
      const dedup=[...new Set(parts)];
      node.textContent=dedup.join(" ");
      tr.append(node);
    }
    body.append(tr);
  });
  table.append(body);
}
function drawOne(){one.replaceChildren();const c=data.columns.find(x=>x.id===service.value)||data.columns[0],h=el("div",undefined,"vm-card"),title=el("h3");title.append(hdr(c));h.append(title,el("div",c.group,"vm-sub"));one.append(h);let group="";for(const r of data.rows){if(group!==r.section){group=r.section;one.append(el("h3",group))}const card=el("div",undefined,"vm-card");card.append(el("h4",r.label),el("div",val(r,c),"vm-entry"));one.append(card)}}
function drawCompare(){compare.replaceChildren();const r=data.rows.find(x=>x.id===row.value)||data.rows[0];compare.append(el("h3",r.section+" — "+r.label));const grid=el("div",undefined,"vm-grid");for(const c of data.columns){const card=el("div",undefined,"vm-card"),h=el("h4");h.append(hdr(c));card.append(h,el("div",val(r,c),"vm-entry"));grid.append(card)}compare.append(grid)}
function view(next){mode=next;for(const b of root.querySelectorAll("[data-vm-view]"))b.setAttribute("aria-pressed",String(b.dataset.vmView===next));by("vm-full").hidden=next!=="full";one.hidden=next!=="service";compare.hidden=next!=="compare";if(!data)return;if(next==="service")drawOne();if(next==="compare")drawCompare()}
root.querySelectorAll("[data-vm-view]").forEach(b=>b.addEventListener("click",()=>view(b.dataset.vmView)));
service.addEventListener("change",()=>{if(mode==="service")drawOne()});
row.addEventListener("change",()=>{if(mode==="compare")drawCompare()});
by("vm-scale").addEventListener("change",e=>{table.style.fontSize=e.target.value+"px"});
async function load(){const res=await fetch(root.dataset.source);if(!res.ok)throw Error("HTTP "+res.status);data=await res.json();
if(data.columns?.length!==17||data.rows?.length!==23||data.rows.some(r=>r.cells.length!==17))throw Error("Неверная структура таблицы");
for(const c of data.columns)opt(service,c.id,c.group+" — "+c.short+" — "+c.context);
for(const r of data.rows)opt(row,r.id,r.section+" — "+r.label);
drawFull();drawOne();drawCompare();view("full");status.textContent=""}
load().catch(e=>{status.textContent="Не удалось загрузить таблицу.";console.error(e)})})();
