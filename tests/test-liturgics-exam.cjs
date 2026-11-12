"use strict";
const fs=require("node:fs"),path=require("node:path"),assert=require("node:assert/strict");
const root=path.resolve(__dirname,".."),read=p=>fs.readFileSync(path.join(root,p),"utf8");
const base="subjects/liturgics/2027/";
const manifest=JSON.parse(read("_data/liturgics_trainers_2027.json"));
const engine=read("assets/js/liturgics-pyramid.js");
const runner=read("assets/js/liturgics-sequence.js");
assert.equal(manifest.questions.length,15,"Official exam must contain fifteen practical tickets");
assert.deepEqual(manifest.questions.map(q=>q.number),Array.from({length:15},(_,i)=>i+1));
new Function(engine);new Function(runner);
function section(s,from,to){const i=s.indexOf(from),j=s.indexOf(to,i+from.length);assert.ok(i>=0&&j>i,"Missing real engine section: "+from);return s.slice(i,j)}
const diagCode=section(engine,"function diagnose(){",'\ndocument.getElementById("checkBtn")');
const hintCode=section(engine,"function hintProblem(){",'\ndocument.getElementById("hintBtn")');
const validCode=section(engine,"function validSaved(s){",'\nfunction persist()');
const diagnoseFactory=new Function("pyramid","required","dataById","isDiagnostic","game",diagCode+"\n"+hintCode+"\nreturn {diagnose:diagnose(),hint:hintProblem()};");
const savedFactory=new Function("dataById","DATA",validCode+"\nreturn validSaved;");
const allCases=[];
for(const q of manifest.questions){
 assert.ok(q.title&&q.cases.length>0,"Missing game "+q.number);
 assert.equal(q.cases.filter(c=>c.mode==="assembly").length,1,"One assembly case per ticket");
 for(const c of q.cases){
  const page=read(base+c.path);
  const sourceMatch=page.match(/data-case="data\/([^"]+\.json)"/);
  assert.ok(sourceMatch,"Missing case JSON in "+c.path);
  assert.equal(c.data_path,"sandbox-pyramid/data/"+sourceMatch[1],"Source path and manifest mismatch");
  const data=JSON.parse(read(base+c.data_path)),id=String(q.number).padStart(2,"0");
  assert.equal(data.case_id,c.case_id);
  assert.equal(data.version,c.version);
  assert.equal(data.question,q.number);
  assert.equal(data.mode,c.mode);
  assert.equal(data.assessment,"training_check","Never label non-certified keys as exam scoring");
  assert.equal(data.l3,"../q"+id+"-l3.html","L3 must belong to the same official ticket");
  assert.ok(fs.existsSync(path.join(root,base,"q"+id+"-l3.md")),"Missing L3 answer");
  assert.ok(page.includes('id="swapBtn"')&&page.includes('id="hintBtn"')&&page.includes('id="checkBtn"')&&page.includes('id="resetBtn"'));
  assert.ok(page.includes("assets/js/liturgics-pyramid.js")&&page.includes("assets/css/liturgics-pyramid.css"));
  const ids=data.items.map(x=>x.id),required=data.items.filter(x=>!x.extra).map(x=>x.id),extra=data.items.filter(x=>x.extra).map(x=>x.id);
  assert.equal(new Set(ids).size,ids.length,"Duplicate brick IDs");
  assert.ok(required.length>=1&&extra.length>=1);
  assert.ok(data.items.every(x=>x.name&&x.detail&&x.id),"Unexplained bricks");
  const lookup=new Map(data.items.map(x=>[x.id,x]));
  const test=pyramid=>diagnoseFactory(pyramid,required,lookup,data.mode==="diagnostic",data);
  const good=test(required);
  assert.equal(good.diagnose.correct,true,"Correct sequence rejected: "+c.case_id);
  assert.equal(good.hint,null,"Correct sequence asks for hint: "+c.case_id);
  const missing=test(required.slice(1));
  assert.equal(missing.diagnose.correct,false);
  assert.ok(missing.diagnose.missing.length===1&&missing.hint.kind==="missing"&&missing.hint.lines.length===3);
  const extraCase=test([...required,extra[0]]);
  assert.equal(extraCase.diagnose.correct,false);
  assert.ok(extraCase.diagnose.extra.includes(extra[0])&&extraCase.hint.kind==="extra"&&extraCase.hint.lines.length===3);
  if(required.length>1){
   const swapped=[...required];[swapped[0],swapped[1]]=[swapped[1],swapped[0]];
   const wrong=test(swapped);
   assert.equal(wrong.diagnose.correct,false,"Permutation accepted: "+c.case_id);
   assert.ok(wrong.diagnose.misplaced.length&&wrong.hint.kind==="order"&&wrong.hint.lines.length===3);
  }
  const isValidSaved=savedFactory(lookup,data.items);
  assert.equal(isValidSaved({sand:extra,pyramid:required,layoutSwapped:true}),true,"Cannot restore correct saved attempt");
  assert.equal(isValidSaved({sand:extra,pyramid:required.slice(1)}),false,"Invalid saved progress accepted");
  assert.equal(isValidSaved({sand:[...extra,required[0]],pyramid:required}),false,"Duplicate saved brick accepted");
  assert.equal(isValidSaved({sand:["unrecognized"],pyramid:required}),false);
  if(data.mode==="diagnostic"){
    assert.ok(data.initialPyramid.length>0,"Error-correction task must start with a populated Pyramid");
    assert.equal(test(data.initialPyramid).diagnose.correct,false,"Error-correction case starts already solved");
  }else assert.deepEqual(data.initialPyramid,[],"Assembly must start with empty Pyramid");
  if(q.number===1&&c.mode==="assembly")assert.equal(data.sourceStatus,"task_scope_reviewed");
  if(q.number===9&&c.mode==="assembly")assert.equal(data.sourceStatus,"task_scope_reviewed");
  allCases.push({q:q.number,id:c.case_id,mode:c.mode,version:c.version,path:c.path});
 }
}
assert.equal(allCases.filter(x=>x.mode==="assembly").length,15);
assert.equal(allCases.filter(x=>x.mode==="diagnostic").length,15);
assert.equal(new Set(allCases.map(x=>x.version)).size,30,"Local progress keys must be unique");
assert.equal(manifest.variant_slots.length,45);
assert.equal(manifest.variant_slots.filter(x=>x.status==="published_training").length,14);
assert.equal(manifest.variant_slots.filter(x=>x.status!=="published_training").length,31);
assert.equal(manifest.variant_slots.filter(x=>x.status==="task_defined_key_pending").length,31);
assert.equal(manifest.variant_slots.find(x=>x.id==="lit-15-C").status,"task_defined_key_pending");
assert.equal(manifest.questions.flatMap(q=>q.cases).filter(c=>c.year).length,11);
// Verify actual engine hooks, not a second implementation of state updates.
assert.match(engine,/markChecked\(d\.correct\)/);
assert.ok(engine.match(/markChecked\(false\)/g).length>=3,"Changes, reset and invalid state must clear checked status");
assert.match(engine,/function showSuccessL3Link\(\)/);
assert.match(engine,/link\.href=L3/);
assert.match(engine,/hintState\.level=Math\.min\(3,hintState\.level\+1\)/);
assert.match(engine,/addEventListener\("touchstart",touchStart/);
assert.match(engine,/addEventListener\("pointerdown",pointerStart/);
assert.match(engine,/addEventListener\("keydown",keyboardStart/);
assert.match(engine,/examSequenceNavigation\(\)/);
// Check the native selections and stored sequences through a DOM-less runner harness.
class Elem {
 constructor(tag="div"){this.tagName=tag.toUpperCase();this.children=[];this.events={};this.textContent="";this.value="";this.checked=false;this.disabled=false;this.hidden=false;this.href="";this.className="";}
 append(...nodes){for(const n of nodes){this.children.push(n);if(this.tagName==="SELECT"&&n.tagName==="OPTION"&&!this.value)this.value=n.value}}
 replaceChildren(...nodes){this.children=[];this.append(...nodes)}
 addEventListener(name,fn){(this.events[name]??=[]).push(fn)}
 dispatch(name){for(const fn of this.events[name]||[])fn({target:this})}
 setAttribute(){}
 querySelectorAll(selector){
  const found=[];const walk=x=>{for(const child of x.children){if(child instanceof Elem){if(selector==="input"&&child.tagName==="INPUT"||selector==="input:checked"&&child.tagName==="INPUT"&&child.checked)found.push(child);walk(child)}}};walk(this);return found;
 }
 querySelector(selector){return this.querySelectorAll(selector)[0]||null}
 after(node){this.afterNode=node}
}
const fields={};
for(const id of ["liturgicsSequenceManifest","sequenceError","questionList","oneCase","mode12","startSelected","startOne","startAll","session","sessionSummary","sessionItems","continue","end"])fields[id]=new Elem(id==="oneCase"||id==="mode12"?"select":"div");
fields.liturgicsSequenceManifest.textContent=JSON.stringify(manifest);
const store=new Map();
const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>{store.set(k,String(v))},removeItem:k=>store.delete(k)};
const document={getElementById:id=>fields[id],createElement:tag=>new Elem(tag),createTextNode:text=>({textContent:text})};
const window={location:{href:"",search:""},events:{},addEventListener(name,fn){this.events[name]=fn}};
new Function("document","window","localStorage","confirm",runner)(document,window,localStorage,()=>true);
assert.equal(fields.oneCase.children.length,30,"Single-question list must offer all published variants");
assert.equal(fields.mode12.children.length,5,"Question 12 exposes assembly, diagnostic prototype and A/B/C cases");
assert.equal(fields.questionList.querySelectorAll("input").length,15);
fields.oneCase.value="lit12-diagnostic";fields.startOne.dispatch("click");
let current=JSON.parse(store.get("bpds-liturgics-sequence-v1"));
assert.equal(current.mode,"Один вопрос");
assert.equal(current.entries[0].case_id,"lit12-diagnostic","Diagnostic mode must be launchable on its own");
assert.ok(window.location.href.endsWith("q12-errors.html?sequence=1"));
for(const box of fields.questionList.querySelectorAll("input"))if(["1","9","12"].includes(box.value)){box.checked=true;box.dispatch("change")}
fields.mode12.value="lit12-diagnostic";assert.equal(fields.startSelected.disabled,false);
fields.startSelected.dispatch("click");
current=JSON.parse(store.get("bpds-liturgics-sequence-v1"));
assert.deepEqual(current.entries.map(x=>x.number),[1,9,12],"Selected sequence order");
assert.equal(current.entries[2].mode,"diagnostic");
fields.startAll.dispatch("click");
current=JSON.parse(store.get("bpds-liturgics-sequence-v1"));
assert.equal(current.entries.length,15);
assert.equal(current.entries.find(e=>e.number===12).mode,"diagnostic","Full sequence must respect q12 mode");
assert.equal(new Set(current.entries.map(x=>x.number)).size,15);
const q1=current.entries[0];
store.set("bpds-liturgics-checked-"+q1.case_id,JSON.stringify({version:q1.version,correct:true}));
window.events.pageshow();
assert.ok(fields.sessionSummary.textContent.includes("Проверено 1 из 15"));
assert.equal(fields.sessionItems.children.length,15);
assert.equal(fields.sessionItems.children[0].children[1].textContent,"Проверено");
fields.end.dispatch("click");
assert.equal(store.has("bpds-liturgics-sequence-v1"),false);
assert.equal(store.has("bpds-liturgics-checked-"+q1.case_id),true,"Ending program must preserve individual results");
// Verify game-page navigation with the exact navigation function from the shared engine.
const navCode=section(engine,"function examSequenceNavigation(){",'\nfunction shuffleVisual()');
const navFn=new Function("game","CASE_VERSION","window","localStorage","document","report","URLSearchParams",navCode+"\nreturn examSequenceNavigation;");
const selection={v:1,mode:"Выбранные вопросы",index:0,entries:allCases.filter(x=>[1,9,12].includes(x.q)&&x.mode==="assembly").sort((a,b)=>a.q-b.q).map(x=>({number:x.q,case_id:x.id,version:x.version,path:x.path,mode:x.mode}))};
store.set("bpds-liturgics-sequence-v1",JSON.stringify(selection));
window.location.search="?sequence=1";
const report=new Elem();
navFn({question:9,case_id:selection.entries[1].case_id},selection.entries[1].version,window,localStorage,document,report,URLSearchParams)();
assert.ok(report.afterNode,"Game sequence navigation did not appear");
const nav=report.afterNode;
assert.equal(nav.children[0].textContent,"Билет 2 из 3");
assert.ok(nav.children.some(e=>e.href&&e.href.includes("q12-assembly.html?sequence=1")));
assert.ok(nav.children.some(e=>e.href&&e.href.includes("q01-assembly.html?sequence=1")));
assert.equal(JSON.parse(store.get("bpds-liturgics-sequence-v1")).index,1);
const plain=new Elem();window.location.search="";
navFn({question:9,case_id:selection.entries[1].case_id},selection.entries[1].version,window,localStorage,document,plain,URLSearchParams)();
assert.equal(plain.afterNode,undefined,"Single standalone game must not gain sequence controls");
// Ensure the rendered Jekyll page is generated from exactly the same case manifest.
const page=read(base+"trainers/sequence.html");
assert.match(page,/site\.data\.liturgics_trainers_2027 \| jsonify/);
assert.match(page,/global-navigation\.html/);
assert.match(read(base+"trainers/index.md"),/sequence\.html/);
console.log("PASS: 30 real keys and 45 audited slots; correct/missing/extra/order; three-stage hint; saved state; 15-select and q12 alternate; 1/selected/all; per-question checked progress; 3-ticket navigation; L3 links and task-scope review.");
