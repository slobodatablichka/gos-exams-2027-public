/* Shared stage-I engine: no DOM, no theology inference, no source editing. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.StageOneCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const ensure = (value, message) => { if (!value) throw new Error(message); };
  const positions = (caseData) => {
    const index = new Map();
    for (const group of caseData.sentence_groups) {
      for (const unit of group.draggables) {
        ensure(!index.has(unit.id), "Duplicate unit id: " + unit.id);
        index.set(unit.id, { unit, group });
      }
    }
    return index;
  };
  function validate(caseData) {
    ensure(caseData?.schema_version === "1.0.0", "Unsupported data schema");
    ensure(caseData.case_id && caseData.source?.original_text, "Missing exercise source");
    const original = caseData.source.original_text;
    ensure(caseData.sentence_groups.map(group => original.slice(group.source_start, group.source_end)).join(" ") === original, "The original text is not reconstructable");
    const index = positions(caseData);
    ensure(index.size, "Missing movable units");
    for (const group of caseData.sentence_groups) {
      ensure(original.slice(group.source_start, group.source_end) === group.source_sentence, "Changed source sentence: " + group.id);
      ensure(group.draggables.length > 0, "Empty source group");
      ensure(Object.keys(group.display_states).length === 2 ** group.draggables.length, "Incomplete prepared display states: " + group.id);
      for (const unit of group.draggables) {
        ensure(unit.source_quote === original.slice(unit.source_start, unit.source_end), "Incorrect unit coordinates: " + unit.id);
        ensure(unit.standalone && unit.standalone.endsWith("."), "Unfinished detached utterance: " + unit.id);
        ensure(["orthodox", "heresy"].includes(unit.judgment), "Invalid hidden classification: " + unit.id);
      }
      for (let mask = 0; mask < 2 ** group.draggables.length; mask++) {
        const state = group.display_states[String(mask)];
        const ids = group.draggables.filter((_, i) => mask & (1 << i)).map(unit => unit.id);
        ensure(state && typeof state.remaining_text === "string" && JSON.stringify(state.extracted) === JSON.stringify(ids),
          "Invalid prepared state: " + group.id + " / " + mask);
        if (mask === 0) ensure(state.remaining_text === group.source_sentence, "State zero must be literal");
      }
    }
    return { index, original };
  }
  function createSession(caseData) {
    const { index, original } = validate(caseData);
    const selected = new Set();
    let result = null;
    const orderedIds = [...index.keys()];
    const allErroneous = new Set([...index].filter(([, value]) => value.unit.judgment === "heresy").map(([id]) => id));
    function stateFor(group) {
      let mask = 0;
      group.draggables.forEach((unit, i) => { if (selected.has(unit.id)) mask |= (1 << i); });
      return { mask, ...group.display_states[String(mask)] };
    }
    function runsFor(group) {
      const state = stateFor(group);
      if (!state.remaining_text) return [];
      const remaining = group.draggables.filter(u => !selected.has(u.id));
      if (state.mask === 0) {
        let cursor = group.source_start;
        const runs = [];
        for (const unit of group.draggables) {
          if (unit.source_start > cursor) runs.push({ text: original.slice(cursor, unit.source_start), id: null });
          runs.push({ text: unit.source_quote, id: unit.id });
          cursor = unit.source_end;
        }
        if (cursor < group.source_end) runs.push({ text: original.slice(cursor, group.source_end), id: null });
        ensure(runs.map(r => r.text).join("") === group.source_sentence, "Initial inline mapping lost source text");
        return runs;
      }
      // A revised remainder can be displayed as a whole when one draggable is left.
      // Later P8/P9 trials will explicitly validate (or extend) multi-survivor binding.
      if (remaining.length === 1) return [{ text: state.remaining_text, id: remaining[0].id }];
      // For an unchanged multi-survivor text preserve the exact matching source quotes.
      const runs = []; let cursor = 0;
      for (const unit of remaining) {
        const start = state.remaining_text.indexOf(unit.source_quote, cursor);
        ensure(start >= 0, "Revised multi-unit sentence needs approved inline mapping: " + group.id);
        if (start > cursor) runs.push({ text: state.remaining_text.slice(cursor, start), id: null });
        runs.push({ text: unit.source_quote, id: unit.id });
        cursor = start + unit.source_quote.length;
      }
      if (cursor < state.remaining_text.length) runs.push({ text: state.remaining_text.slice(cursor), id: null });
      return runs;
    }
    const notifyChange = () => { result = null; };
    return {
      caseData, sourceOriginal: original, orderedIds,
      selectedIds: () => orderedIds.filter(id => selected.has(id)),
      isSelected: id => selected.has(id),
      lookup: id => index.get(id) || null,
      stateFor, runsFor, currentResult: () => result,
      transfer(id) {
        ensure(index.has(id), "Unknown movable source span: " + id);
        if (selected.has(id)) return false;
        selected.add(id); notifyChange(); return true;
      },
      restore(id) {
        ensure(index.has(id), "Unknown moved claim: " + id);
        if (!selected.delete(id)) return false;
        notifyChange(); return true;
      },
      reset() { selected.clear(); result = null; },
      check() {
        const missed = orderedIds.filter(id => allErroneous.has(id) && !selected.has(id));
        const extra = orderedIds.filter(id => !allErroneous.has(id) && selected.has(id));
        result = { correct: missed.length === 0 && extra.length === 0, missed: missed.length, extra: extra.length,
          selected: selected.size, expectedCount: allErroneous.size, checked: true };
        return { ...result };
      }
    };
  }
  return { validate, createSession };
});

;
/* Stage II (Ересь → Таксономия). Pure state; no DOM and no hints before check(). */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.StageTwoCore=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
function createSession(caseData,stageOne){
  assert(caseData?.schema_version==="1.0.0","Unsupported case schema");
  assert(stageOne?.currentResult()?.correct===true,"Stage I must be passed before taxonomy");
  const selected=stageOne.selectedIds();
  const entries=new Map(selected.map(id=>[id,stageOne.lookup(id)?.unit]));
  assert(entries.size===selected.length&&selected.length>0,"Invalid selected units");
  const categories=caseData?.taxonomy?.categories||[];
  const ids=new Set(categories.map(c=>c.id));
  assert(ids.size===categories.length,"Duplicate taxonomy categories");
  assert(categories.length>=3&&categories.every(c=>c.id&&c.label),"Invalid category list");
  assert(categories.filter(c=>c.role==="distractor").length>=2,"At least two surplus categories required");
  const required=[...new Set(selected.flatMap(id=>entries.get(id)?.heresies||[]))];
  assert(required.length>=1&&required.every(id=>ids.has(id)),"Some correct classifications have no category");
  assert(required.length===categories.filter(c=>c.role==="target").length,"Category key mismatch");
  assert(categories.filter(c=>c.role==="target").every(c=>required.includes(c.id)),"Unexpected target label");
  const assigned=new Map();
  let lastResult=null;
  function ensureStageOne(){
    assert(stageOne.currentResult()?.correct===true,"Stage I was changed after transition");
    assert(JSON.stringify(stageOne.selectedIds())===JSON.stringify(selected),"Stage I selection changed after transition");
  }
  return {
    selectedIds:()=>[...selected],
    categories:()=>categories.map(c=>({id:c.id,label:c.label})), // No secret role in UI output.
    assignmentOf:id=>{assert(entries.has(id),"Unknown extracted unit: "+id);return assigned.get(id)||null;},
    assignments:()=>selected.map(id=>({id,category:assigned.get(id)||null})),
    currentResult:()=>lastResult?{...lastResult}:null,
    assign(id,categoryId){
      ensureStageOne();
      assert(entries.has(id),"Unknown extracted unit "+id);
      if(categoryId==null||categoryId===""){if(assigned.delete(id)){lastResult=null;return true;}return false;}
      assert(ids.has(categoryId),"Unknown taxonomy section "+categoryId);
      if(assigned.get(id)===categoryId)return false;
      assigned.set(id,categoryId);lastResult=null;return true;
    },
    reset(){ensureStageOne();assigned.clear();lastResult=null;},
    check(){
      ensureStageOne();
      const missing=selected.filter(id=>!assigned.has(id)).length;
      const wrong=selected.filter(id=>assigned.has(id)&&!entries.get(id).heresies.includes(assigned.get(id))).length;
      lastResult={checked:true,correct:missing===0&&wrong===0,assigned:selected.length-missing,total:selected.length,missing,wrong};
      return {...lastResult};
    }
  };
}
return {createSession};
});

;
/* Stage III: «Таксономия → Апология». Pure pedagogical session, no DOM or premature key disclosure. */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.StageThreeCore=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const assert=(value,message)=>{if(!value)throw new Error(message);};
const types=["history","theology","rebuttal"];
function createSession(data,stageOne,stageTwo){
  assert(data?.schema_version==="1.0.0","Unsupported trainer schema");
  assert(stageOne?.currentResult()?.correct===true,"Stage I must be passed");
  assert(stageTwo?.currentResult()?.correct===true,"Stage II must be passed");
  const stageOneSnapshot=JSON.stringify(stageOne.selectedIds());
  const stageTwoSnapshot=JSON.stringify(stageTwo.assignments());
  const targets=data.taxonomy.categories.filter(c=>c.role==="target");
  assert(targets.length>0,"No actual teachings in taxonomy");
  const expected=targets.flatMap(cat=>types.map(type=>cat.id+":"+type));
  const sourceIds=new Set((data.sources||[]).map(s=>s.id));
  assert(sourceIds.size===data.sources.length&&sourceIds.size>0,"Missing reference registry");
  const index=new Map();
  const optionIds=new Set();
  for(const block of data.apology.blocks){
    const key=block.category_id+":"+block.type;
    assert(expected.includes(key)&&!index.has(key),"Duplicate or unexpected Apology block "+key);
    assert(block.prompt?.length>12,"Missing block question "+key);
    assert(block.options.length>=6&&block.options.length<=8,"Expected 6–8 choices "+key);
    let nCorrect=0;
    for(const option of block.options){
      assert(!optionIds.has(option.id),"Duplicate Apology option "+option.id);
      optionIds.add(option.id);
      assert(typeof option.correct==="boolean","Missing option key "+option.id);
      if(option.correct)nCorrect++;
      assert(option.explanation?.length>12,"Missing explanation "+option.id);
      assert(option.evidence_refs?.length&&option.evidence_refs.every(ref=>sourceIds.has(ref)),"Broken source reference "+option.id);
    }
    assert(nCorrect>=2&&nCorrect<=4,"Must have 2–4 correct choices in "+key);
    index.set(key,block);
  }
  assert(index.size===expected.length,"Each teaching needs three distinct Apology tasks");
  const blocks=expected.map(key=>index.get(key));
  const checked=blocks.map(()=>null);
  const answers=blocks.map(()=>new Set());
  let current=0;
  const categoryLabel=new Map(targets.map(x=>[x.id,x.label]));
  function checkPrior(){
    assert(stageOne.currentResult()?.correct===true&&JSON.stringify(stageOne.selectedIds())===stageOneSnapshot,
      "Stage I changed after beginning Apology");
    assert(stageTwo.currentResult()?.correct===true&&JSON.stringify(stageTwo.assignments())===stageTwoSnapshot,
      "Stage II changed after beginning Apology");
  }
  function present(block){
    return {categoryId:block.category_id,categoryLabel:categoryLabel.get(block.category_id),
      type:block.type,kind:types.indexOf(block.type)+1,prompt:block.prompt,
      options:block.options.map(x=>({id:x.id,text:x.text}))};
  }
  function resultAt(i){
    const value=checked[i];return value?{...value}:null;
  }
  function completed(){return checked.every(x=>x?.correct===true);}
  return {
    blockCount:()=>blocks.length,
    currentIndex:()=>current,
    currentBlock:()=>present(blocks[current]),
    progress:()=>blocks.map((b,i)=>({categoryId:b.category_id,type:b.type,passed:checked[i]?.correct===true,checked:checked[i]!==null})),
    selection:()=>blocks[current].options.filter(x=>answers[current].has(x.id)).map(x=>x.id),
    currentResult:()=>resultAt(current),
    completed:()=>completed(),
    select(optionId,on){
      checkPrior();
      const option=blocks[current].options.find(x=>x.id===optionId);
      assert(!!option,"Unknown Apology answer "+optionId);
      const selected=answers[current];
      const change=on?(!selected.has(optionId)):(selected.has(optionId));
      if(!change)return false;
      if(on)selected.add(optionId);else selected.delete(optionId);
      for(let i=current;i<checked.length;i++)checked[i]=null;
      return true;
    },
    checkCurrent(){
      checkPrior();
      const options=blocks[current].options,selection=answers[current];
      const missing=options.filter(x=>x.correct&&!selection.has(x.id)).length;
      const extra=options.filter(x=>!x.correct&&selection.has(x.id)).length;
      checked[current]={checked:true,correct:missing===0&&extra===0,selected:selection.size,
        total:options.length,missing,extra};
      return resultAt(current);
    },
    feedback(){
      checkPrior();
      if(!checked[current])return null;
      return blocks[current].options.map(o=>({
        id:o.id,text:o.text,selected:answers[current].has(o.id),correct:o.correct,
        explanation:o.explanation,evidenceRefs:[...o.evidence_refs]
      }));
    },
    evidence(refId){
      checkPrior();
      assert(!!checked[current],"Sources are revealed after checking");
      const source=data.sources.find(x=>x.id===refId);
      assert(source,"Unknown evidence reference "+refId);
      return {...source};
    },
    next(){
      checkPrior();
      if(!checked[current]?.correct||current===blocks.length-1)return false;
      current++;return true;
    },
    previous(){
      checkPrior();
      if(current===0)return false;
      current--;return true;
    },
    oralTask(){
      checkPrior();
      if(!completed())return null;
      return {instruction:data.oral_task.instruction,l3_path:data.oral_task.l3_path,
        auto_grade:false,original_text:data.source.original_text};
    },
    reset(){
      checkPrior();
      for(const s of answers)s.clear();
      checked.fill(null);current=0;
    }
  };
}
return {createSession};
});

;
/* Stage VI: complete P3 three-stage browser controller, preserving approved Stage-I/II engines. */
(function () {
  "use strict";
  const doc = document;
  const $ = (id) => doc.getElementById(id);
  const sourceEl = $("source-text");
  const targetEl = $("heresy-zone");
  const listEl = $("selected-list");
  const feedbackEl = $("feedback");
  const statusEl = $("live-status");
  const caseData = JSON.parse($("case-data").textContent);
  const caseName=caseData.kind==="official"?"П"+caseData.practical_no+" / №"+caseData.fos_no
     :"Учебное П"+caseData.practical_no+"-"+caseData.variant+" / №"+caseData.fos_no;
  const session = window.StageOneCore.createSession(caseData);
  const [dragThreshold, dragPreviewLimit] = [7, 144];
  let pointer = null;
  let ghost = null;
  let selectedOrder = [];
  let stage = 1;
  let taxonomySession = null;
  let apologySession = null;
  let transitionStageIIIAnimated = false;
  let transitionBusy = false;
  let transitionWasAnimated = false;
  doc.title = "Скриптура → Ересь — " + caseName;
  $("source-label").textContent = (caseData.kind==="official"?"Официальное практическое №":"Учебный вариант "+caseData.variant+" · практическое №")+caseData.practical_no+" · ФОС №"+caseData.fos_no;
  function element(tag, attributes, content) {
    const node = doc.createElement(tag);
    for (const [key,value] of Object.entries(attributes || {})) {
      if (key === "class") node.className = value;
      else if (key === "title") node.title = value;
      else node.setAttribute(key, value);
    }
    if (content != null) node.textContent = content;
    return node;
  }
  function announce(text) { statusEl.textContent = text; }
  function clearFeedback() {
    feedbackEl.hidden = true;
    feedbackEl.textContent = "";
    delete feedbackEl.dataset.kind;
    if(stage===1) $("next-button").hidden = true;
    if(stage===2) $("next-apology-button").hidden = true;
  }
  function renderSource() {
    const frag = doc.createDocumentFragment();
    let visibleCount = 0;
    for (const group of caseData.sentence_groups) {
      const state = session.stateFor(group);
      if (state.remaining_text) {
        if (visibleCount++) frag.append(doc.createTextNode(" "));
        const sentence = element("span", { "data-group-id": group.id, class: "source-sentence" });
        for (const run of session.runsFor(group)) {
          if (run.id) sentence.append(element("span", {
            class: "source-unit", role: "button", tabindex: "0",
            "data-origin": "source", "data-unit-id": run.id,
            "aria-label": "Перенести смысловое положение: " + run.text
          }, run.text));
          else sentence.append(doc.createTextNode(run.text));
        }
        frag.append(sentence);
        if (state.mask) frag.append(element("span",{class:"source-gap","aria-hidden":"true",
          title:"Отсюда извлечено положение; восстановить его можно в окне «Ересь»"}));
      } else if (state.mask) {
        // Nonverbal, subtle anchor: no edited words are added to the remaining prose.
        frag.append(element("span",{class:"source-gap","aria-hidden":"true",
          title:"Из этой части текста перенесено положение"}));
      }
    }
    sourceEl.replaceChildren(frag);
  }
  function renderSelected() {
    listEl.replaceChildren();
    selectedOrder = session.selectedIds();
    targetEl.querySelector(".empty")?.remove();
    for (const [index, id] of selectedOrder.entries()) {
      const { unit, group } = session.lookup(id);
      const li = element("li",{class:"selected-item",role:"button",tabindex:"0",
        "aria-label":"Перемещённое положение: " + unit.standalone + " Нажмите Enter или стрелку влево для возвращения.",
        "data-origin":"heresy","data-unit-id":id});
      const text = element("p",{},unit.standalone);
      const footer = element("div",{class:"item-footer"});
      footer.append(element("span",{},"Из предложения " + (caseData.sentence_groups.findIndex(g=>g.id===group.id)+1)));
      const restore = element("button",{class:"text-button",type:"button","data-restore-id":id,
        "aria-label":"Вернуть положение на исходное место"},"Вернуть");
      footer.append(restore);
      li.append(text,footer);
      listEl.append(li);
    }
    if (!selectedOrder.length) targetEl.append(element("p",{class:"empty"},"Перетащите сюда неверные, по вашему мнению, положения. Их можно вернуть до проверки."));
    $("selected-count").textContent = "Перенесено: " + selectedOrder.length;
  }
  function render() { renderSource(); renderSelected(); }
  function transfer(id, focus = true) {
    if (!session.transfer(id)) return;
    clearFeedback();render();announce("Положение перенесено. Правильность пока не проверяется.");
    if (focus) listEl.querySelector('[data-unit-id="' + id + '"]')?.focus({preventScroll:true});
  }
  function restore(id,focus = true) {
    if (!session.restore(id)) return;
    clearFeedback();render();announce("Положение возвращено на исходное место.");
    if (focus) sourceEl.querySelector('[data-unit-id="' + id + '"]')?.focus({preventScroll:true});
  }
  const startPointer=(event)=>{
    if(stage!==1 || transitionBusy || event.button!==0 || event.target.closest("[data-restore-id]"))return;
    const source=event.target.closest("[data-unit-id][data-origin]");
    if(!source)return;
    event.preventDefault();
    pointer={id:source.dataset.unitId,origin:source.dataset.origin,pointerId:event.pointerId,
      startX:event.clientX,startY:event.clientY,moved:false};
    source.setPointerCapture?.(event.pointerId);
  };
  const movePointer=(event)=>{
    if(stage!==1 || !pointer||pointer.pointerId!==event.pointerId)return;
    if(!pointer.moved&&Math.hypot(event.clientX-pointer.startX,event.clientY-pointer.startY)>dragThreshold){
      pointer.moved=true;
      const item=session.lookup(pointer.id)?.unit;
      ghost=element("div",{class:"drag-ghost","aria-hidden":"true"},item?.standalone.slice(0,dragPreviewLimit)||"");
      doc.body.append(ghost);
    }
    if(!pointer.moved)return;
    ghost.style.left=(event.clientX+13)+"px";ghost.style.top=(event.clientY+13)+"px";
    const zone=pointer.origin==="source"?targetEl:$("source-panel");
    const at=doc.elementFromPoint(event.clientX,event.clientY);
    zone.classList.toggle("over", !!at&&(zone===at||zone.contains(at)));
  };
  const endPointer=(event)=>{
    if(stage!==1 || !pointer||pointer.pointerId!==event.pointerId)return;
    const {id,origin,moved}=pointer;const target=origin==="source"?targetEl:$("source-panel");
    const at=doc.elementFromPoint(event.clientX,event.clientY);
    const isOver=!!at&&(at===target||target.contains(at));
    ghost?.remove();ghost=null;target.classList.remove("over");pointer=null;
    if(moved&&isOver) origin==="source"?transfer(id,false):restore(id,false);
    else if(!moved&&event.pointerType==="touch")
      origin==="source"?transfer(id,false):restore(id,false); // Touch tap: usable when panels stack vertically.
  };
  function cancelDrag(){if(pointer){pointer=null;ghost?.remove();ghost=null;targetEl.classList.remove("over");$("source-panel").classList.remove("over");announce("Перемещение отменено.");}}
  doc.addEventListener("pointerdown",startPointer);
  doc.addEventListener("pointermove",movePointer);
  doc.addEventListener("pointerup",endPointer);
  doc.addEventListener("pointercancel",cancelDrag);
  doc.addEventListener("keydown",(event)=>{
    if(stage!==1)return;
    if(event.key==="Escape"){cancelDrag();return;}
    if(event.target.closest("button"))return;
    const node=event.target.closest("[data-unit-id][data-origin]");
    if(!node)return;
    const key=event.key;
    if(key!=="Enter"&&key!==" "&&key!=="ArrowRight"&&key!=="ArrowLeft")return;
    event.preventDefault();
    const origin=node.dataset.origin,id=node.dataset.unitId;
    if(origin==="source"&&["Enter"," ","ArrowRight"].includes(key))transfer(id);
    else if(origin==="heresy"&&["Enter"," ","ArrowLeft"].includes(key))restore(id);
  });
  doc.addEventListener("click",(event)=>{
    const button=event.target.closest("[data-restore-id]");
    if(stage===1&&button){event.preventDefault();restore(button.dataset.restoreId);}
  });
  $("check-button").addEventListener("click",()=>{
    if(transitionBusy)return;
    if(stage===2){
      const result=taxonomySession.check();
      feedbackEl.hidden=false;feedbackEl.dataset.kind=result.correct?"pass":"fail";
      feedbackEl.textContent=result.correct
        ?"Этап II пройден: все положения распределены верно. Перейдите к «Апологии»."
        :"Попытка завершена: не распределено "+result.missing+"; неверно отнесено "+result.wrong+". Исправьте распределение и повторите проверку.";
      $("next-apology-button").hidden=!result.correct;
      announce(result.correct?"Таксономия пройдена.":"Проверка классификации обнаружила ошибки.");
      feedbackEl.scrollIntoView({block:"nearest",behavior:"auto"});return;
    }
    const result=session.check();
    feedbackEl.hidden=false;
    feedbackEl.dataset.kind=result.correct?"pass":"fail";
    if(result.correct){ feedbackEl.textContent="Этап I пройден: найдены все неверные положения, а верные оставлены в «Скриптуре». Перейдите к «Таксономии»."; $("next-button").hidden=false; }
    else feedbackEl.textContent="Попытка завершена. Есть пропущенные неверные положения ("+result.missed+
      ") и/или ошибочно перенесённые верные ("+result.extra+"). Исправьте выбор и проверьте снова.";
    announce(result.correct?"Этап пройден.":"Проверка выявила ошибки.");
    feedbackEl.scrollIntoView({block:"nearest",behavior:"auto"});
  });
  $("reset-button").addEventListener("click",()=>{
    if(transitionBusy)return;
    if(stage===3){ apologySession.reset();renderApology();announce("Ответы Апологии очищены; таксономия сохранена.");return; }
    if(stage===2){ taxonomySession.reset();for(const id of taxonomySession.selectedIds())moveClaim(id,null,false);clearFeedback();announce("Распределение по разделам очищено; положения остались извлечёнными.");return; }
    cancelDrag();session.reset();clearFeedback();render();
    announce("Начальный текст восстановлен дословно; все перенесённые положения возвращены.");
    sourceEl.focus({preventScroll:true});
  });

  // Stage II preserves the Stage-I extracted <li> objects and their underlying source IDs.
  const stagePanels=$("stage-panels"),scripturePanel=$("source-panel"),heresyPanel=$("target-panel");
  const taxonomyPanel=$("taxonomy-panel"),taxonomyGrid=$("taxonomy-list");
  const reduced=()=>window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let taxPointer=null, taxGhost=null, hoverDrop=null;
  function categoryNode(categoryId){
    return taxonomyGrid.querySelector('[data-category-id="'+categoryId+'"]');
  }
  function prepareCategories(){
    const list=[...caseData.taxonomy.categories].sort((a,b)=>a.label.localeCompare(b.label,"ru"));
    taxonomyGrid.replaceChildren();
    for(const cat of list){
      const area=element("section",{class:"category-drop","data-category-id":cat.id,
        "aria-label":"Раздел «"+cat.label+"»"});
      const heading=element("div",{class:"category-heading"});
      heading.append(element("span",{class:"category-title"},cat.label));
      heading.append(element("span",{class:"category-count","aria-hidden":"true"},"0"));
      area.append(heading,element("ol",{class:"category-claims","data-category-list":cat.id,
        "aria-label":"Отнесённые положения: "+cat.label}));
      taxonomyGrid.append(area);
    }
  }
  function prepareClaims(){
    const items=Array.from(listEl.children).filter(x=>x.dataset.unitId);
    for(const li of items){
      li.dataset.stage2Item="true";
      li.setAttribute("role","group");
      li.querySelector("[data-restore-id]")?.remove();
      li.setAttribute("aria-label","Перемещаемое положение. Нажмите Enter для выбора ереси или перетащите в раздел.");
      const wrapper=element("label",{class:"claim-select-label"});
      wrapper.append(element("span",{class:"sr-only"},"Отнести положение к ереси"));
      const select=element("select",{class:"claim-category-select","data-assign-select":li.dataset.unitId,
        "aria-label":"Выбрать ересь для положения: "+session.lookup(li.dataset.unitId).unit.standalone});
      select.append(element("option",{value:""},"— Пока без раздела —"));
      const cats=[...caseData.taxonomy.categories].sort((a,b)=>a.label.localeCompare(b.label,"ru"));
      for(const cat of cats)select.append(element("option",{value:cat.id},cat.label));
      wrapper.append(select);li.append(wrapper);
    }
  }
  function updateCounts(){
    const left=taxonomySession.assignments().filter(x=>!x.category).length;
    $("selected-count").textContent="Не распределено: "+left;
    targetEl.querySelector(".empty")?.remove();
    if(!left) targetEl.append(element("p",{class:"empty"},"Все положения распределены. Перенесите их обратно для исправления."));
    for(const area of taxonomyGrid.querySelectorAll(".category-drop")){
      const n=area.querySelectorAll("[data-stage2-item]").length;
      area.querySelector(".category-count").textContent=String(n);
    }
  }
  function moveClaim(id,categoryId,animate=true){
    const li=doc.querySelector('[data-stage2-item="true"][data-unit-id="'+id+'"]');
    if(!li)throw Error("Stage-II claim element lost: "+id);
    const oldRect=li.getBoundingClientRect();
    const newParent=categoryId?categoryNode(categoryId)?.querySelector(".category-claims"):listEl;
    if(!newParent)throw Error("Unknown taxonomy area "+categoryId);
    newParent.append(li); // Move the SAME node, never reconstruct the semantic object.
    li.dataset.origin=categoryId?"taxonomy":"heresy";
    li.querySelector("[data-assign-select]").value=categoryId||"";
    li.classList.toggle("assigned",!!categoryId);
    updateCounts();
    const newRect=li.getBoundingClientRect();
    if(animate&&!reduced()&&oldRect.width&&newRect.width){
      const dx=oldRect.left-newRect.left,dy=oldRect.top-newRect.top;
      li.animate([{transform:"translate("+dx+"px,"+dy+"px)",opacity:.87},{transform:"translate(0,0)",opacity:1}],
        {duration:350,easing:"cubic-bezier(.22,1,.36,1)"});
    }
  }
  function assignClaim(id,categoryId,focus=false){
    if(stage!==2||transitionBusy)return;
    if(taxonomySession.assign(id,categoryId||null)){
      clearFeedback();moveClaim(id,categoryId||null);
      announce(categoryId?"Положение размещено в разделе. Правильность пока не проверяется.":"Положение возвращено в окно «Ересь».");
      if(focus)doc.querySelector('[data-stage2-item="true"][data-unit-id="'+id+'"] [data-assign-select]')?.focus({preventScroll:true});
    }
  }
  doc.addEventListener("change",(event)=>{
    if(stage!==2)return;
    const select=event.target.closest("[data-assign-select]");
    if(select)assignClaim(select.dataset.assignSelect,select.value,true);
  });
  function clearTaxHover(){hoverDrop?.classList.remove("over");hoverDrop=null;}
  doc.addEventListener("pointerdown",(event)=>{
    if(stage!==2||transitionBusy||event.button!==0||event.target.closest("select,option,button"))return;
    const li=event.target.closest('[data-stage2-item="true"]');
    if(!li)return;
    event.preventDefault();
    taxPointer={id:li.dataset.unitId,pointerId:event.pointerId,x:event.clientX,y:event.clientY,moved:false};
    li.setPointerCapture?.(event.pointerId);
  });
  doc.addEventListener("pointermove",(event)=>{
    if(stage!==2||!taxPointer||taxPointer.pointerId!==event.pointerId)return;
    const drag=taxPointer;
    if(!drag.moved&&Math.hypot(event.clientX-drag.x,event.clientY-drag.y)>7){
      drag.moved=true;
      taxGhost=element("div",{class:"drag-ghost","aria-hidden":"true"},session.lookup(drag.id).unit.standalone.slice(0,150));
      doc.body.append(taxGhost);
    }
    if(!drag.moved)return;
    taxGhost.style.left=(event.clientX+15)+"px";taxGhost.style.top=(event.clientY+14)+"px";
    const at=doc.elementFromPoint(event.clientX,event.clientY);
    const area=at?.closest("[data-category-id]")||at?.closest("#heresy-zone");
    if(hoverDrop!==area){clearTaxHover();hoverDrop=area||null;hoverDrop?.classList.add("over");}
  });
  function finishTaxPointer(event){
    if(stage!==2||!taxPointer||taxPointer.pointerId!==event.pointerId)return;
    const drag=taxPointer,at=doc.elementFromPoint(event.clientX,event.clientY);
    const category=at?.closest("[data-category-id]"),left=at?.closest("#heresy-zone");
    taxPointer=null;taxGhost?.remove();taxGhost=null;clearTaxHover();
    if(drag.moved&&(category||left))assignClaim(drag.id,category?.dataset.categoryId||null);
    else if(!drag.moved&&event.pointerType==="touch")
      doc.querySelector('[data-stage2-item="true"][data-unit-id="'+drag.id+'"] [data-assign-select]')?.focus({preventScroll:true});
  }
  doc.addEventListener("pointerup",finishTaxPointer);
  doc.addEventListener("pointercancel",()=>{taxPointer=null;taxGhost?.remove();taxGhost=null;clearTaxHover();});
  doc.addEventListener("keydown",(event)=>{
    if(stage!==2||event.target.closest("select,option,button"))return;
    const li=event.target.closest('[data-stage2-item="true"]');
    if(!li)return;
    if(["Enter"," ","ArrowLeft"].includes(event.key)){
      event.preventDefault();
      if(event.key==="ArrowLeft"&&taxonomySession.assignmentOf(li.dataset.unitId))assignClaim(li.dataset.unitId,null,true);
      else li.querySelector("[data-assign-select]")?.focus({preventScroll:true});
    }
  });
  async function advance(){
    if(stage!==1||transitionBusy||session.currentResult()?.correct!==true)return;
    taxonomySession=window.StageTwoCore.createSession(caseData,session);
    transitionBusy=true;cancelDrag();
    $("next-button").hidden=true;
    const before=heresyPanel.getBoundingClientRect();
    // Keep the Heresy panel and all its already-extracted DOM nodes intact.
    if(!reduced()){
      transitionWasAnimated=true;
      const folding=scripturePanel.animate([{transform:"scaleX(1)",opacity:1},{transform:"scaleX(.04)",opacity:0}],
        {duration:340,easing:"ease-in",fill:"forwards"});
      await folding.finished.catch(()=>{});
      folding.cancel(); // Remove retained transform so restart displays Scripture normally.
    }
    scripturePanel.hidden=true;
    taxonomyPanel.hidden=false;
    const after=heresyPanel.getBoundingClientRect();
    prepareCategories();prepareClaims();
    heresyPanel.querySelector(".window-head p").textContent="Распределите извлечённые положения по учениям справа.";
    taxonomyPanel.querySelector(".window-head p").textContent="Названий больше, чем необходимо. Перенесите все положения в подходящие разделы.";
    updateCounts();
    const work=[];
    if(!reduced()){
      const x=before.left-after.left,y=before.top-after.top;
      work.push(heresyPanel.animate([{transform:"translate("+x+"px,"+y+"px)"},{transform:"translate(0,0)"}],
        {duration:460,easing:"cubic-bezier(.22,1,.36,1)"}).finished);
      work.push(taxonomyPanel.animate([{transform:"scaleX(.07)",opacity:0},{transform:"scaleX(1)",opacity:1}],
        {duration:460,easing:"cubic-bezier(.22,1,.36,1)",transformOrigin:"left center"}).finished);
      await Promise.all(work.map(p=>p.catch(()=>{})));
    }
    stage=2;transitionBusy=false;
    clearFeedback();
    $("stage-notice").textContent="Этап II из III · Таксономия";
    $("stage-hint").textContent="Определите, к какой ереси относится каждое положение. Лишние названия не используйте.";
    $("stage-description").textContent="Опытный тренажёр · Этап II · «Ересь → Таксономия»";
    $("control-hint").textContent="Мышь — перетащить положение в раздел; клавиатура и сенсорный экран — выбрать название в списке под положением. Возврат — «Без раздела» или перенос обратно в «Ересь».";
    $("check-button").textContent="Проверить этап II";
    $("reset-button").textContent="Очистить распределение";
    $("restart-button").hidden=false;
    doc.title="Ересь → Таксономия — " + caseName;
    announce("Окно «Ересь» переместилось влево, «Таксономия» открылась справа. Все извлечённые положения сохранены.");
  }
  $("next-button").addEventListener("click",advance);
  $("restart-button").addEventListener("click",()=>{
    if((stage!==2&&stage!==3)||transitionBusy)return;
    if(stage===3){apologyPanel.hidden=true;heresyPanel.hidden=false;taxonomyPanel.hidden=false;}
    apologySession=null;
    taxonomySession.reset();stage=1;
    taxonomyPanel.hidden=true;scripturePanel.hidden=false;
    for(const li of [...doc.querySelectorAll('[data-stage2-item="true"]')])li.remove();
    session.reset();clearFeedback();render();
    $("stage-notice").textContent="Этап I из III · Распознавание";
    $("stage-hint").textContent="Найдите все ошибочные утверждения. Истинные должны остаться в исходном тексте. Проверка — только в конце.";
    $("stage-description").textContent="Опытный тренажёр · Этап I · «Скриптура → Ересь»";
    $("control-hint").textContent="Мышь — перетащить; касание — коснуться; клавиатура — Tab и Enter / пробел. Возврат — «Вернуть» либо стрелка влево.";
    heresyPanel.querySelector(".window-head p").textContent="Сюда перенесите все ошибочные положения.";
    $("check-button").textContent="Проверить этап I";
    $("reset-button").textContent="Сбросить";
    $("restart-button").hidden=true;
    $("next-apology-button").hidden=true;
    $("check-button").hidden=false;
    doc.title="Скриптура → Ересь — " + caseName;
    announce("Возврат к этапу I. Официальный текст полностью восстановлен.");
  });


  // Stage III: one question at a time, with source-linked explanations only after checking.
  const apologyPanel=$("apology-panel"),apologyOptions=$("apology-options");
  const apologyFeedback=$("apology-feedback");
  const labels={history:"Историческая справка",theology:"Богословская оценка",rebuttal:"Православное опровержение"};
  function sourceUrl(source){
    if(source.url)return source.url;
    const s=source.path||"";
    let m=s.match(/^materials\/dogmatics\/2027\/(?:l1|l2|l3)\/q(\d{2})\.md$/);
    if(m)return "../q"+m[1]+"-l3.html";
    m=s.match(/^materials\/dogmatics\/2027\/practice\/(practicum-\d{2}|methodology|heresy-comparison)\.md$/);
    if(m)return "../practice/"+m[1]+".html";
    return "../index.html";
  }
  function clearApologyFeedback(){
    apologyFeedback.replaceChildren();
    apologyFeedback.hidden=true;
    delete apologyFeedback.dataset.kind;
  }
  function makeEvidence(refId){
    const source=apologySession.evidence(refId);
    const link=element("a",{href:sourceUrl(source),target:"_blank",rel:"noopener noreferrer",
      class:"apology-evidence"},source.label);
    link.title=source.section?source.label+" — "+source.section:source.label;
    return link;
  }
  function renderApology(){
    if(stage!==3)return;
    const block=apologySession.currentBlock(),index=apologySession.currentIndex();
    const selection=new Set(apologySession.selection());
    const checked=apologySession.currentResult();
    $("apology-position").textContent="Блок "+(index+1)+" из "+apologySession.blockCount();
    $("apology-category").textContent=block.categoryLabel;
    $("apology-type").textContent=labels[block.type];
    $("apology-question").textContent=block.prompt;
    const flags=apologySession.progress();
    $("apology-progress").replaceChildren(...flags.map((x,i)=>{
      const span=element("span",{class:"apology-step"+(i===index?" active":"")+(x.passed?" passed":""),
        "aria-label":"Блок "+(i+1)+(x.passed?" пройден":" ещё не пройден")},String(i+1));
      return span;
    }));
    const list=doc.createDocumentFragment();
    for(const option of block.options){
      const item=element("label",{class:"apology-option"});
      const control=element("input",{type:"checkbox","data-apology-id":option.id});
      control.checked=selection.has(option.id);
      const copy=element("span",{class:"apology-option-text"},option.text);
      item.append(control,copy);
      list.append(item);
    }
    apologyOptions.replaceChildren(list);
    clearApologyFeedback();
    if(checked){
      apologyFeedback.hidden=false;
      apologyFeedback.dataset.kind=checked.correct?"pass":"fail";
      apologyFeedback.append(element("p",{class:"apology-result"},
        checked.correct?"Блок пройден: выбран полный набор обоснованных положений.":
        "Проверка завершена: пропущено верных — "+checked.missing+
        ", отмечено лишних — "+checked.extra+". Исправьте ответ и повторите проверку."));
      const detail=apologySession.feedback();
      const relevant=checked.correct?detail.filter(o=>o.correct):
        detail.filter(o=>(o.correct&&!o.selected)||(!o.correct&&o.selected));
      for(const item of relevant){
        const box=element("section",{class:"apology-explanation"});
        const status=item.correct?(item.selected?"Верно выбрано":"Пропущено верное положение"):"Выбрано лишнее положение";
        box.append(element("p",{class:"apology-explanation-heading"},status));
        box.append(element("p",{},item.explanation));
        const refs=element("div",{class:"apology-sources"});
        for(const ref of item.evidenceRefs)refs.append(makeEvidence(ref));
        box.append(refs);apologyFeedback.append(box);
      }
    }
    $("apology-check").hidden=apologySession.completed()&&index===apologySession.blockCount()-1;
    $("apology-prev").disabled=index===0;
    $("apology-next").hidden=!checked?.correct||index===apologySession.blockCount()-1;
    $("apology-next").textContent="Следующий блок";
    $("apology-current").hidden=false;
    const oral=apologySession.oralTask();
    $("oral-panel").hidden=!oral;
    if(oral){
      $("oral-instruction").textContent=oral.instruction;
      const link=$("oral-l3");
      link.href=sourceUrl({path:oral.l3_path});
      link.setAttribute("target","_blank");link.setAttribute("rel","noopener noreferrer");
    }
  }
  apologyOptions.addEventListener("change",(event)=>{
    if(stage!==3||transitionBusy)return;
    const option=event.target.closest("[data-apology-id]");
    if(!option)return;
    apologySession.select(option.dataset.apologyId,option.checked);
    clearApologyFeedback();
    $("apology-next").hidden=true;
    $("oral-panel").hidden=true;
    // Preserve keyboard focus / checkbox states during editing; redraw only after explicit check.
  });
  $("apology-check").addEventListener("click",()=>{
    if(stage!==3||transitionBusy)return;
    const result=apologySession.checkCurrent();
    renderApology();
    announce(result.correct?"Блок Апологии пройден.":"Блок проверен; показаны пояснения к ошибкам и ссылки на источники.");
    apologyFeedback.scrollIntoView({block:"nearest",behavior:"auto"});
  });
  $("apology-prev").addEventListener("click",()=>{
    if(stage!==3||transitionBusy)return;
    if(apologySession.previous())renderApology();
  });
  $("apology-next").addEventListener("click",()=>{
    if(stage!==3||transitionBusy)return;
    if(apologySession.next())renderApology();
  });
  async function advanceToApology(){
    if(stage!==2||transitionBusy||taxonomySession?.currentResult()?.correct!==true)return;
    apologySession=window.StageThreeCore.createSession(caseData,session,taxonomySession);
    transitionBusy=true;
    $("next-apology-button").hidden=true;
    const before=taxonomyPanel.getBoundingClientRect();
    if(!reduced()){
      transitionStageIIIAnimated=true;
      const fold=heresyPanel.animate([{transform:"scaleX(1)",opacity:1},{transform:"scaleX(.04)",opacity:0}],
        {duration:340,easing:"ease-in",fill:"forwards"});
      await fold.finished.catch(()=>{});
      fold.cancel();
    }
    heresyPanel.hidden=true;
    apologyPanel.hidden=false;
    const after=taxonomyPanel.getBoundingClientRect();
    for(const select of taxonomyPanel.querySelectorAll("[data-assign-select]"))select.disabled=true;
    if(!reduced()){
      const dx=before.left-after.left,dy=before.top-after.top;
      await Promise.all([
        taxonomyPanel.animate([{transform:"translate("+dx+"px,"+dy+"px)"},{transform:"translate(0,0)"}],
          {duration:460,easing:"cubic-bezier(.22,1,.36,1)"}).finished.catch(()=>{}),
        apologyPanel.animate([{transform:"scaleX(.07)",opacity:0},{transform:"scaleX(1)",opacity:1}],
          {duration:460,easing:"cubic-bezier(.22,1,.36,1)",transformOrigin:"left center"}).finished.catch(()=>{})
      ]);
    }
    stage=3;transitionBusy=false;
    clearFeedback();
    $("stage-notice").textContent="Этап III из III · Апология";
    $("stage-hint").textContent="Для каждого учения последовательно выполните историю, оценку и православное опровержение.";
    $("stage-description").textContent="Опытный тренажёр · Этап III · «Таксономия → Апология»";
    $("control-hint").textContent="Отметьте все подходящие утверждения в каждом блоке. Проверяйте по окончании выбора; после проверки доступны объяснения и ссылки.";
    $("check-button").hidden=true;
    $("reset-button").textContent="Очистить Апологию";
    $("back-taxonomy").hidden=false;
    $("restart-button").hidden=false;
    doc.title="Таксономия → Апология — " + caseName;
    renderApology();
    announce("«Ересь» свернулась, «Таксономия» перешла влево, «Апология» раскрылась справа. Существующая классификация сохранена.");
  }
  $("next-apology-button").addEventListener("click",advanceToApology);
  $("back-taxonomy").addEventListener("click",async()=>{
    if(stage!==3||transitionBusy)return;
    transitionBusy=true;
    const before=taxonomyPanel.getBoundingClientRect();
    apologyPanel.hidden=true;heresyPanel.hidden=false;
    const after=taxonomyPanel.getBoundingClientRect();
    if(!reduced()){
      const dx=before.left-after.left,dy=before.top-after.top;
      await Promise.all([
        taxonomyPanel.animate([{transform:"translate("+dx+"px,"+dy+"px)"},{transform:"translate(0,0)"}],
          {duration:340,easing:"ease-out"}).finished.catch(()=>{}),
        heresyPanel.animate([{transform:"scaleX(.06)",opacity:0},{transform:"scaleX(1)",opacity:1}],
          {duration:340,easing:"ease-out"}).finished.catch(()=>{})
      ]);
    }
    for(const select of taxonomyPanel.querySelectorAll("[data-assign-select]"))select.disabled=false;
    apologySession=null;stage=2;transitionBusy=false;clearFeedback();
    $("stage-notice").textContent="Этап II из III · Таксономия";
    $("stage-hint").textContent="Определите, к какой ереси относится каждое положение. Лишние названия не используйте.";
    $("stage-description").textContent="Опытный тренажёр · Этап II · «Ересь → Таксономия»";
    $("control-hint").textContent="Перетащите фрагменты либо выберите учение в списке; затем снова проверьте этап II.";
    $("check-button").hidden=false;
    $("check-button").textContent="Проверить этап II";
    $("reset-button").textContent="Очистить распределение";
    $("back-taxonomy").hidden=true;
    doc.title="Ересь → Таксономия — " + caseName;
    announce("Возврат к Таксономии. Распределение сохранено; ответы Апологии сброшены.");
  });

  render();
  // Public, read-only inspection for automated/browser QA, not a production security boundary.
  window.StageOnePreview={getState:()=>({selectedIds:session.selectedIds(),sourceText:sourceEl.textContent,
    checked:session.currentResult()?.checked||false,result:session.currentResult()?{...session.currentResult()}:null}),
    original:caseData.source.original_text};
  window.StageFivePreview={
    getState:()=>({stage,transitionBusy,transitionWasAnimated,selectedIds:session.selectedIds(),
      assignments:taxonomySession?taxonomySession.assignments():[],
      stage1Result:session.currentResult(),stage2Result:taxonomySession?.currentResult()||null,
      stage3Result:apologySession?apologySession.currentResult():null,
      stage3Index:apologySession?apologySession.currentIndex():null,
      stage3Completed:apologySession?.completed()||false,
      transitionStageIIIAnimated,
      sourceOriginal:caseData.source.original_text,sourceText:sourceEl.textContent}),
    sourcePanel:scripturePanel,heresyPanel,taxonomyPanel
  };
})();
