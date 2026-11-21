"use strict";
(() => {
  const root = document.getElementById("liturgics-table-app");
  if (!root) return;
  const base = root.dataset.base;
  const signBase = root.dataset.signs;
  const xs = [0,46,87,130,171,212,253,292,330,368,410,450,491,530,569,610,648,686,725];
  const H=1046, W=725, STRIDE=Math.ceil(W/8);
  const cols=[
    ["При одном святом","Вседневная служба",null],
    ["При двух святых","Вседневная служба",null],
    ["В субботу","Вседневная служба",null],
    ["В предпразднство или попразднство","Вседневная служба",null],
    ["Шестеричная — седмичный день","Шестеричная","shesterichnaya.svg"],
    ["Славословная — седмичный день","Славословная","slavoslovnaya.svg"],
    ["Полиелейная — седмичный день","Полиелейная","polieleynaya.svg"],
    ["Бденная среднего святого — седмичный день","Бденная","bdennaya-srednego-svyatogo.svg"],
    ["Бденная великого святого — седмичный день","Бденная","bdennaya-velikogo-svyatogo.svg"],
    ["Воскресенье: один святой без знака","Воскресное бдение",null],
    ["Воскресенье: два святых без знака","Воскресное бдение",null],
    ["Воскресенье: святой с малым знаком","Воскресное бдение","shesterichnaya.svg"],
    ["Воскресенье: святой с великим знаком","Воскресное бдение","bdennaya-velikogo-svyatogo.svg"],
    ["Воскресенье: святой без знака + предпразднство или попразднство","Воскресное бдение",null],
    ["Господский праздник — в любой день","Господский праздник","gospodskiy-prazdnik.svg"],
    ["Богородичный двунадесятый праздник — в седмичный день","Богородичный праздник","bogorodichnyy-dvunadesyatyy.svg"],
    ["Богородичный двунадесятый праздник — в воскресенье","Богородичный праздник","bogorodichnyy-dvunadesyatyy.svg"]
  ];
  const ys=[130,175,230,248,277,305,359,396,460,496,541,560,578,605,642,687,751,778,833,870,924,972,1017,1046];
  const titles=[
    'Вечерня: стихиры на «Господи, воззвах»',
    'Вечерня: «Слава, и ныне»',
    'Стихиры литии',
    'Лития: «Слава, и ныне»',
    'Стихиры стиховны',
    'Стиховна: «Слава, и ныне»',
    'Тропари отпустительные',
    'Вечерня: «Слава, и ныне» после тропарей',
    'Утреня: тропари на «Бог Господь»',
    'Утреня: «Слава, и ныне»',
    'Седальны по кафизмах',
    'Седальны по полиелее',
    'Степенные антифоны',
    'Прокимен и Евангелие',
    'Каноны',
    'Чтения после 3-й, 6-й и 9-й песней',
    'Светилен (эксапостиларий)',
    'Стихиры на хвалитех',
    'Хвалитех: «Слава, и ныне»',
    'Тропари отпустительные',
    'Утреня: «Слава, и ныне» после тропарей',
    'Тропари на часах',
    'Кондаки на часах'
  ];
  let original, selection=4, activeRow=0, zoom=1.5, mode="full";
  const full=document.getElementById("lit-full");
  const mobile=document.getElementById("lit-mobile");
  const compare=document.getElementById("lit-compare");
  const serviceSelect=document.getElementById("lit-service");
  const rowSelect=document.getElementById("lit-row");
  const zoomSelect=document.getElementById("lit-zoom");
  const status=document.getElementById("lit-status");
  const heading=document.getElementById("lit-service-heading");
  const controls=[...root.querySelectorAll("[data-view]")];
  function label(col){return cols[col][0]}
  function sign(col) {
    const f=cols[col][2];
    if (!f) return "";
    const safe=f.replace(/[^a-z0-9.\-]/g,"");
    return '<img class="lit-sign" src="'+signBase+'/'+safe+'" alt="" aria-hidden="true">';
  }
  function renderFull(){
    full.width=W;full.height=H;
    full.getContext("2d").drawImage(original,0,0);
    full.style.width=Math.round(W*zoom)+"px";
    full.style.height=Math.round(H*zoom)+"px";
  }
  function renderMobile(){
    const start=xs[selection+1],width=xs[selection+2]-start;
    const cv=mobile;cv.width=46+7+width;cv.height=H;
    const cx=cv.getContext("2d");
    cx.fillStyle="#fff";cx.fillRect(0,0,cv.width,cv.height);
    cx.drawImage(original,0,0,46,H,0,0,46,H);
    cx.drawImage(original,start,0,width,H,53,0,width,H);
    cv.setAttribute("aria-label","Состав службы: "+label(selection)+". Полная колонка таблицы с названиями строк.");
    heading.innerHTML=sign(selection)+"<strong>"+label(selection)+"</strong>";
  }
  function renderCompare(){
    compare.replaceChildren();
    const y=ys[activeRow],height=ys[activeRow+1]-y;
    for(let i=0;i<cols.length;i++){
      const section=document.createElement("section");section.className="lit-compare-item";
      const head=document.createElement("h3");head.className="lit-compare-label";
      if(cols[i][2]){
        const img=document.createElement("img");img.src=signBase+"/"+cols[i][2];img.alt="";img.className="lit-sign";head.appendChild(img);
      }
      head.append(document.createTextNode(label(i)));
      const cv=document.createElement("canvas");
      const x=xs[i+1],cw=xs[i+2]-x;cv.width=cw;cv.height=height;
      const cx=cv.getContext("2d");cx.fillStyle="#fff";cx.fillRect(0,0,cw,height);
      cx.drawImage(original,x,y,cw,height,0,0,cw,height);
      cv.className="lit-compare-cell";cv.setAttribute("role","img");cv.setAttribute("aria-label",label(i)+": "+titles[activeRow]);
      section.append(head,cv);compare.appendChild(section);
    }
    document.getElementById("lit-row-title").textContent=titles[activeRow];
  }
  function changeMode(next){
    mode=next;
    document.getElementById("lit-full-view").hidden=mode!=="full";
    document.getElementById("lit-mobile-view").hidden=mode!=="mobile";
    document.getElementById("lit-compare-view").hidden=mode!=="compare";
    controls.forEach(b=>{b.setAttribute("aria-pressed",b.dataset.view===mode?"true":"false")});
    if(!original)return;
    if(mode==="full")renderFull();
    if(mode==="mobile")renderMobile();
    if(mode==="compare")renderCompare();
  }
  async function load(){
    const urls=Array.from({length:7},(_,i)=>base+"/part-"+String(i+1).padStart(2,"0")+".txt");
    const parts=await Promise.all(urls.map(async u=>{const r=await fetch(u);if(!r.ok)throw Error("HTTP "+r.status);return r.text()}));
    const b64=parts.join("").trim();
    const binary=atob(b64);
    const compressed=Uint8Array.from(binary,c=>c.charCodeAt(0));
    if(!("DecompressionStream" in window))throw Error("Браузер не поддерживает распаковку изображения");
    const stream=new Blob([compressed]).stream().pipeThrough(new DecompressionStream("deflate"));
    const bytes=new Uint8Array(await new Response(stream).arrayBuffer());
    if(bytes.length!==STRIDE*H)throw Error("Размер изображения не совпадает");
    const cv=document.createElement("canvas");cv.width=W;cv.height=H;
    const ctx=cv.getContext("2d"),pixels=ctx.createImageData(W,H);
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){
      const bit=(bytes[y*STRIDE+(x>>3)]>>(7-(x&7)))&1;
      const i=(y*W+x)*4,shade=bit?255:0;
      pixels.data[i]=shade;pixels.data[i+1]=shade;pixels.data[i+2]=shade;pixels.data[i+3]=255;
    }
    ctx.putImageData(pixels,0,0);original=cv;
    status.textContent="Таблица загружена. Выберите режим просмотра.";
    changeMode(mode);
  }
  cols.forEach((col,i)=>{const o=document.createElement("option");o.value=i;o.textContent=String(i+1).padStart(2,"0")+". "+col[0];serviceSelect.appendChild(o)});
  titles.forEach((title,i)=>{const o=document.createElement("option");o.value=i;o.textContent=title;rowSelect.appendChild(o)});
  serviceSelect.value=String(selection);
  rowSelect.value=String(activeRow);
  controls.forEach(b=>b.addEventListener("click",()=>changeMode(b.dataset.view)));
  serviceSelect.addEventListener("change",e=>{selection=Number(e.target.value);if(original)renderMobile()});
  rowSelect.addEventListener("change",e=>{activeRow=Number(e.target.value);if(original)renderCompare()});
  zoomSelect.addEventListener("change",e=>{zoom=Number(e.target.value);if(original)renderFull()});
  changeMode("full");
  load().catch(err=>{status.textContent="Не удалось загрузить таблицу. Обновите страницу.";console.error("Liturgics table:",err)});
})();
