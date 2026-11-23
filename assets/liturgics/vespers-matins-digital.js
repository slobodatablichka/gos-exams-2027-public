"use strict";
(()=>{const root=document.getElementById("vm-digital");if(!root)return;
const by=id=>document.getElementById(id),service=by("vm-service"),row=by("vm-row"),table=by("vm-table"),one=by("vm-one"),compare=by("vm-compare"),status=by("vm-status");
let data,mode="full";const iconBase=root.dataset.icons;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=String(text);if(cls)n.className=cls;return n};
function ico(parent,col){for(const icon of (col.icons?.length?col.icons:(col.icon?[col.icon]:[]))){const im=el("img",undefined,"vm-icon");im.src=iconBase+encodeURIComponent(icon);im.alt="";parent.append(im)}}
function hdr(col){const n=el("div");ico(n,col);n.append(el("strong",col.short));n.append(el("div",col.context,"vm-sub"));if(col.typikon)n.append(el("div",col.typikon,"vm-sub"));return n}
function val(r,c){
  const cell=r.cells.find(x=>x.column_id===c.id);
  if(!cell)return "";
  if(cell.kind==="span"&&cell.span_anchor){
    const origin=r.cells.find(x=>x.column_id===cell.span_anchor);
    return origin?.text??"";
  }
  return cell.text??"";
}
function opt(sel,v,t){const n=el("option",t);n.value=v;sel.add(n)}
function drawFull(){
  table.replaceChildren();
  const layout=data.source_layout;
  const h=el("thead"),groups=el("tr"),titles=el("tr");
  const first=el("th","Элемент последования","vm-sticky");first.scope="col";first.rowSpan=2;groups.append(first);
  for(const g of layout.column_groups){const th=el("th",g.title);th.scope="colgroup";th.colSpan=g.colspan;th.className="vm-group";groups.append(th)}
  for(const c of data.columns){const th=el("th");th.scope="col";th.append(hdr(c));titles.append(th)}
  h.append(groups,titles);table.append(h);
  const sourceById=new Map();
  for(let i=0;i<layout.body_bands.length;i++){const id=layout.body_bands[i].row_id;if(!sourceById.has(id))sourceById.set(id,[]);sourceById.get(id).push(i)}
  const displayed=[];
  for(const rr of data.rows){
    if(rr.source_bands?.length){
      for(const band of rr.source_bands)displayed.push({row:rr,source:[band.source_band],label:band.label,
        texts:band.texts,parts:band.cell_parts||{}});
    }else displayed.push({row:rr,source:sourceById.get(rr.id)||[],label:rr.source_label!==undefined?rr.source_label:rr.section+" — "+rr.label,
      texts:rr.cells.map(c=>c.text),parts:{}});
  }
  const key=(r,c)=>r+":"+c,origins=new Map(),covered=new Set();
  for(const m of layout.merged_regions){
    const bandSet=new Set(Array.from({length:m.rowspan},(_,i)=>m.row_start+i));
    const eligible=[];
    for(let r=0;r<displayed.length;r++){
      const source=displayed[r].source;
      if(source.some(i=>bandSet.has(i))){if(!source.every(i=>bandSet.has(i))){eligible.length=0;break}eligible.push(r)}
    }
    if(!eligible.length||eligible.some((v,i)=>i&&v!==eligible[i-1]+1))continue;
    const sum=eligible.reduce((n,r)=>n+displayed[r].source.length,0);
    if(sum!==m.rowspan)continue;
    const r0=eligible[0],c0=m.col_start,items=[];
    for(const r of eligible)for(let c=c0;c<c0+m.colspan;c++)items.push(key(r,c));
    if(items.some(k=>covered.has(k)))continue;
    origins.set(key(r0,c0),{rows:eligible,colspan:m.colspan});
    for(const k of items)if(k!==key(r0,c0))covered.add(k);
  }
  const body=el("tbody");
  displayed.forEach((rr,r)=>{
    const tr=el("tr");
    for(let c=0;c<=data.columns.length;c++){
      if(covered.has(key(r,c)))continue;
      const m=origins.get(key(r,c));
      const node=c===0?el("th",undefined,"vm-sticky"):el("td");
      if(c===0)node.scope="row";
      if(m){node.rowSpan=m.rows.length;node.colSpan=m.colspan}
      const rows=m?.rows||[r],width=m?.colspan||1,values=[];
      for(const ix of rows){
        const d=displayed[ix];
        if(c===0){if(d.label)values.push(d.label)}
        else for(let col=c;col<c+width;col++){
          const parts=d.parts[data.columns[col-1].id];
          if(parts?.length){
            const container=el("div",undefined,"vm-parts");
            parts.forEach(part=>container.append(el("div",part,"vm-inner-line")));
            node.append(container);
          } else if(d.texts[col-1])values.push(d.texts[col-1]);
        }
      }
      const unique=[...new Set(values)];
      if(unique.length){const value=el("span",unique.join(" "));node.prepend(value)}
      tr.append(node);
    }
    body.append(tr);
  });
  table.append(body);
}
function drawOne(){one.replaceChildren();const c=data.columns.find(x=>x.id===service.value)||data.columns[0],h=el("div",undefined,"vm-card"),title=el("h3");title.append(hdr(c));h.append(title,el("div",c.group,"vm-sub"));one.append(h);let group="";for(const r of data.rows){if(group!==r.section){group=r.section;one.append(el("h3",group))}const card=el("div",undefined,"vm-card");card.append(el("h4",r.label),el("div",val(r,c),"vm-entry"));one.append(card)}}
function drawCompare(){compare.replaceChildren();const r=data.rows.find(x=>x.id===row.value)||data.rows[0];compare.append(el("h3",r.section+" — "+r.label));const grid=el("div",undefined,"vm-grid");for(const c of data.columns){const card=el("div",undefined,"vm-card"),h=el("h4");h.append(hdr(c));card.append(h,el("div",val(r,c),"vm-entry"));grid.append(card)}compare.append(grid)}

const selectedTable=by("vm-selected-table"),selectedOptions=by("vm-selected-options"),
  selectedOrder=by("vm-selected-order"),selectedCount=by("vm-selected-count"),
  selectedPartInput=by("vm-selected-part"),selectedEmpty=by("vm-selected-empty");
const selectedStorageKey="gos-exams-2027-liturgics-selected-v1";
let selectedIds=["c01","c06","c07"],selectedPart="all";

function saveSelected(){
  try{localStorage.setItem(selectedStorageKey,JSON.stringify({ids:selectedIds,part:selectedPart}))}catch(_){}
}
function restoreSelected(){
  try{
    const saved=JSON.parse(localStorage.getItem(selectedStorageKey)||"null");
    if(saved&&Array.isArray(saved.ids)){
      const allowed=new Set(data.columns.map(c=>c.id));
      selectedIds=[...new Set(saved.ids.filter(id=>allowed.has(id)))];
    }
    if(["all","Вечерня","Утреня","Часы"].includes(saved?.part))selectedPart=saved.part;
  }catch(_){}
  selectedPartInput.value=selectedPart;
}
function selectIds(ids){
  const allowed=new Set(data.columns.map(c=>c.id));
  selectedIds=[...new Set(ids.filter(id=>allowed.has(id)))];
  saveSelected();
  drawSelected();
}
function shiftSelected(id,direction){
  const index=selectedIds.indexOf(id),other=index+direction;
  if(index<0||other<0||other>=selectedIds.length)return;
  const next=selectedIds.slice();
  [next[index],next[other]]=[next[other],next[index]];
  selectIds(next);
}
function drawSelectedControls(){
  selectedOptions.replaceChildren();
  selectedOrder.replaceChildren();
  selectedCount.textContent=selectedIds.length;
  for(const c of data.columns){
    const label=el("label",undefined,"vm-checkitem"),checkbox=el("input");
    checkbox.type="checkbox";checkbox.value=c.id;checkbox.checked=selectedIds.includes(c.id);
    checkbox.setAttribute("aria-label",c.group+" — "+c.short);
    checkbox.addEventListener("change",()=>selectIds(checkbox.checked?[...selectedIds,c.id]:selectedIds.filter(id=>id!==c.id)));
    label.append(checkbox,el("span",c.group+" — "+c.short));selectedOptions.append(label);
  }
  selectedIds.forEach((id,index)=>{
    const c=data.columns.find(col=>col.id===id);
    const chip=el("div",undefined,"vm-orderitem");
    chip.append(el("span",c.short,"vm-ordername"));
    for(const [symbol,title,delta] of [["←","Переместить влево",-1],["→","Переместить вправо",1]]){
      const button=el("button",symbol);button.type="button";
      button.disabled=delta===-1?index===0:index===selectedIds.length-1;
      button.setAttribute("aria-label",title+": "+c.short);
      button.addEventListener("click",()=>shiftSelected(id,delta));chip.append(button);
    }
    const remove=el("button","×");remove.type="button";
    remove.setAttribute("aria-label","Убрать службу: "+c.short);
    remove.addEventListener("click",()=>selectIds(selectedIds.filter(x=>x!==id)));
    chip.append(remove);selectedOrder.append(chip);
  });
}
function drawSelectedTable(){
  selectedTable.replaceChildren();
  const columns=selectedIds.map(id=>data.columns.find(c=>c.id===id));
  const empty=!columns.length;
  selectedEmpty.hidden=!empty;
  by("vm-selected-scroller").hidden=empty;
  if(empty)return;
  const thead=el("thead"),header=el("tr");
  const title=el("th","Элемент последования","vm-sticky");title.scope="col";header.append(title);
  for(const c of columns){
    const th=el("th");th.scope="col";th.append(hdr(c));
    const remove=el("button","×","vm-remove-col");remove.type="button";
    remove.setAttribute("aria-label","Убрать службу: "+c.short);
    remove.title="Убрать этот столбец";
    remove.addEventListener("click",()=>selectIds(selectedIds.filter(x=>x!==c.id)));
    th.append(remove);header.append(th);
  }
  thead.append(header);
  const tbody=el("tbody");
  let section="";
  for(const r of data.rows){
    if(selectedPart!=="all"&&r.section!==selectedPart)continue;
    if(section!==r.section){
      section=r.section;
      const sectionRow=el("tr"),th=el("th",section,"vm-section-heading");
      th.scope="rowgroup";th.colSpan=columns.length+1;
      sectionRow.append(th);tbody.append(sectionRow);
    }
    const tr=el("tr"),heading=el("th",r.label,"vm-sticky");
    heading.scope="row";tr.append(heading);
    for(const c of columns)tr.append(el("td",val(r,c)));
    tbody.append(tr);
  }
  selectedTable.append(thead,tbody);
  selectedTable.style.fontSize=by("vm-scale").value+"px";
}
function drawSelected(){
  if(!data)return;
  drawSelectedControls();drawSelectedTable();
}
by("vm-select-all").addEventListener("click",()=>selectIds(data.columns.map(c=>c.id)));
by("vm-select-none").addEventListener("click",()=>selectIds([]));
selectedPartInput.addEventListener("change",()=>{
  selectedPart=selectedPartInput.value;saveSelected();drawSelectedTable();
});

function view(next){mode=next;for(const b of root.querySelectorAll("[data-vm-view]"))b.setAttribute("aria-pressed",String(b.dataset.vmView===next));by("vm-full").hidden=next!=="full";one.hidden=next!=="service";compare.hidden=next!=="compare";by("vm-selected").hidden=next!=="selected";if(!data)return;if(next==="service")drawOne();if(next==="compare")drawCompare();if(next==="selected")drawSelected()}
root.querySelectorAll("[data-vm-view]").forEach(b=>b.addEventListener("click",()=>view(b.dataset.vmView)));
service.addEventListener("change",()=>{if(mode==="service")drawOne()});
row.addEventListener("change",()=>{if(mode==="compare")drawCompare()});
by("vm-scale").addEventListener("change",e=>{table.style.fontSize=e.target.value+"px";selectedTable.style.fontSize=e.target.value+"px"});
async function load(){const res=await fetch(root.dataset.source);if(!res.ok)throw Error("HTTP "+res.status);data=await res.json();
if(data.columns?.length!==17||data.rows?.length!==23||data.rows.some(r=>r.cells.length!==17))throw Error("Неверная структура таблицы");
for(const c of data.columns)opt(service,c.id,c.group+" — "+c.short+" — "+c.context);
for(const r of data.rows)opt(row,r.id,r.section+" — "+r.label);
restoreSelected();drawFull();drawOne();drawCompare();drawSelected();view("full");
const requestedRow=new URLSearchParams(window.location.search).get("row");
if(data.rows.some(r=>r.id===requestedRow)){row.value=requestedRow;view("compare")}
status.textContent=""}
load().catch(e=>{status.textContent="Не удалось загрузить таблицу.";console.error(e)})})();
