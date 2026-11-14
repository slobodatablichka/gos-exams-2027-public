async function generate(){
 const fs=(await import("node:fs")).default;
 const path=(await import("node:path")).default;
 const assert=(await import("node:assert/strict")).default;
 const {fileURLToPath}=await import("node:url");
 const PUBLIC=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
 const flags=process.argv.slice(2),pos=flags.indexOf("--private-root");
 assert.ok(pos>=0&&flags[pos+1],"Specify --private-root");
 assert.ok(flags.includes("--write")||flags.includes("--check"),"Use --write or --check");
 const check=flags.includes("--check"),PRIVATE=path.resolve(PUBLIC,flags[pos+1]);
 const read=(root,p)=>fs.readFileSync(path.join(root,p),"utf8");
 const registry=JSON.parse(read(PRIVATE,"materials/dogmatics/2027/trainer/cases/index.json"));
 assert.deepEqual(registry.counts,{total:40,official:10,training:30,complete:40,pending:0});
 const dest="subjects/dogmatics/2027";
 const output=new Map(),emit=(p,s)=>{assert.ok(!output.has(p),"Duplicate "+p);output.set(p,s)};
 const template=read(PRIVATE,"prototypes/dogmatics/stage-06/template.html");
 const style=["prototypes/dogmatics/stage-04/stage1.css","prototypes/dogmatics/stage-05/stage5.css","prototypes/dogmatics/stage-06/stage6.css"].map(p=>read(PRIVATE,p)).join("\n\n");
 emit("assets/css/dogmatics-trainer.css",style+`
/* Dogmatics publication: standalone browser UI, independent of Jekyll Cayman CSS. */
.trainer-nav,.trainer-links{max-width:1280px;margin:auto;padding:12px 28px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.trainer-nav a,.trainer-links .variant-links a{display:inline-block;padding:7px 12px;background:#fffcf7;border:1px solid #b7cbbf;border-radius:9px;text-decoration:none;color:#214b3a;font-weight:650}
.trainer-nav a:focus-visible,.trainer-links a:focus-visible{outline:3px solid #225f8a;outline-offset:2px}
.trainer-links{display:block;padding-top:0;padding-bottom:6px}
.trainer-links h2{font-size:1.1rem;margin:13px 0 8px}
.trainer-links .variant-links{display:flex;gap:8px;flex-wrap:wrap}
.trainer-links .variant-links a[aria-current="page"]{background:#dcebe0;border-color:#567b61;font-weight:750}
.trainer-links a:hover,.trainer-nav a:hover{background:#e2eee3}
#p8-note{background:#fff6df;border:1px solid #d9c79a;border-radius:10px;padding:12px 16px;margin-bottom:16px}
@media(max-width:620px){.trainer-nav,.trainer-links{padding-left:14px;padding-right:14px}.trainer-nav a,.trainer-links .variant-links a{font-size:13px;padding:7px 9px}}
`);
 let ui=read(PRIVATE,"prototypes/dogmatics/stage-06/stage6-ui.js");
 const sourceUrlOld=`function sourceUrl(source){
    if(source.url)return source.url;
    return "https://github.com/slobodatablichka/gos-exams-2027/blob/main/"+source.path;
  }`;
 const sourceUrlNew=`function sourceUrl(source){
    if(source.url)return source.url;
    const s=source.path||"";
    let m=s.match(/^materials\\/dogmatics\\/2027\\/(?:l1|l2|l3)\\/q(\\d{2})\\.md$/);
    if(m)return "../q"+m[1]+"-l3.html";
    m=s.match(/^materials\\/dogmatics\\/2027\\/practice\\/(practicum-\\d{2}|methodology|heresy-comparison)\\.md$/);
    if(m)return "../practice/"+m[1]+".html";
    return "../index.html";
  }`;
 assert.ok(ui.includes(sourceUrlOld),"Unexpected stage-6 source link mapping");
 ui=ui.replace(sourceUrlOld,sourceUrlNew);
 const key='const caseData = JSON.parse($("case-data").textContent);';
 assert.ok(ui.includes(key));
 ui=ui.replace(key,key+`
  const caseName=caseData.kind==="official"?"П"+caseData.practical_no+" / №"+caseData.fos_no
     :"Учебное П"+caseData.practical_no+"-"+caseData.variant+" / №"+caseData.fos_no;`);
 ui=ui.replaceAll("— П3 / №18", '— " + caseName');
 const labelOld='$("source-label").textContent = "Официальное практическое №" + caseData.practical_no + " · ФОС №" + caseData.fos_no;';
 assert.ok(ui.includes(labelOld));
 ui=ui.replace(labelOld,'$("source-label").textContent = (caseData.kind==="official"?"Официальное практическое №":"Учебный вариант "+caseData.variant+" · практическое №")+caseData.practical_no+" · ФОС №"+caseData.fos_no;');
 emit("assets/js/dogmatics-trainer.js",[
 "prototypes/dogmatics/stage-04/stage1-core.js","prototypes/dogmatics/stage-05/stage2-core.js","prototypes/dogmatics/stage-06/stage3-core.js"
 ].map(p=>read(PRIVATE,p)).concat(ui).join("\n;\n"));
 const fmt=x=>String(x).padStart(2,"0"), rows=[];
 for(let practical=1;practical<=10;practical++){
  const fos=practical+15,n=fmt(practical);
  const group=registry.cases.filter(c=>c.practical_no===practical);
  assert.equal(group.length,4);
  const cases=[group.find(x=>x.kind==="official"),...group.filter(x=>x.kind==="training").sort((a,b)=>a.variant-b.variant)];
  assert.ok(cases.every(Boolean));
  const links=cases.map(c=>({id:c.case_id,label:c.kind==="official"?"Официальный ФОС":"Учебный "+c.variant}));
  rows.push({practical,fos,links});
  const nav=`<nav class="trainer-nav" aria-label="Навигация по учебному сайту">
   <a href="../../../../index.html">Главная</a>
   <a href="../../../../practice/index.html">Практика</a>
   <a href="../index.html">Догматика №1–25</a>
   <a href="index.html">Все 40 тренажёров</a>
   <a href="../practice/practicum-${n}.html">Практикум №${practical}</a>
   <a href="../practice/methodology.html">Методика</a>
   </nav>`;
  const flag=practical===8?`<p class="hint" id="p8-note">Учебная оговорка к П8: официальный ФОС говорит о двух ересях, но в полном тексте присутствуют три исторически различимых группы заблуждений. Тренажёр показывает все фактически присутствующие учения; формулировка ФОС не изменена. «Единая сложная ипостась» сама по себе православна.</p>`:"";
  for(const c of cases){
   assert.equal(c.state,"accepted_data");
   const data=JSON.parse(read(PRIVATE,c.case_file));
   assert.equal(data.status,"accepted_data");
   assert.equal(data.case_id,c.case_id);
   assert.equal(data.fos_no,fos);
   const label=c.kind==="official"?`П${practical} / №${fos}`:`Учебное П${practical}-${c.variant} / №${fos}`;
   const panel=`<section class="trainer-links" aria-label="Соседние учебные варианты">
    <h2>Практическое №${practical} · ФОС №${fos}</h2>
    <div class="variant-links">${links.map(v=>`<a href="${v.id}.html"${v.id===c.case_id?' aria-current="page"':''}>${v.label}</a>`).join(" ")}</div>
    <p>Материал: <a href="../q${fmt(fos)}-l3.html">L3</a> · <a href="../q${fmt(fos)}-l2.html">L2</a> · <a href="../q${fmt(fos)}-l1.html">L1</a> · <a href="../practice/practicum-${n}.html">Практикум</a> · <a href="../practice/heresy-comparison.html">Таблица ересей</a></p>
    </section>`;
   let html=template.replaceAll("П3 / №18",label)
     .replace(/<style>\s*<!-- STYLE_GOES_HERE -->\s*<\/style>/,'<link rel="stylesheet" href="../../../../assets/css/dogmatics-trainer.css">')
     .replaceAll("Сверить устный ответ с L3 по вопросу №18","Сверить устный ответ с L3 по вопросу №"+fos)
     .replace('<main class="shell">',nav+panel+'<main class="shell">\n'+flag)
     .replace("Опытный тренажёр · Этап I","Электронный тренажёр · Этап I")
     .replace("Исходная формулировка ФОС сохраняется неизменной. Это учебный прототип, а не официальный экзамен; все три этапа работают в опытном режиме; результаты не являются официальной экзаменационной оценкой.",
       "Исходная формулировка задания сохраняется неизменной. Это учебный тренажёр, а не официальный экзамен; результат самопроверки не является оценкой комиссии.");
   if(c.kind==="training")html=html.replace("Официальный текст ФОС. Нажмите на фрагмент и перетащите целиком.","Учебный тренировочный текст. Нажмите на фрагмент и перетащите целиком.");
   html=html.replace("<!-- DATA_GOES_HERE -->",JSON.stringify(data).replace(/</g,"\\u003c").replace(/&/g,"\\u0026"));
   const scripts=/<script><!-- CORE_GOES_HERE --><\/script>\s*<script><!-- STAGE2_GOES_HERE --><\/script>\s*<script><!-- STAGE3_GOES_HERE --><\/script>\s*<script><!-- UI_GOES_HERE --><\/script>/;
   assert.ok(scripts.test(html),"Stage6 template script slots missing");
   html=html.replace(scripts,'<script src="../../../../assets/js/dogmatics-trainer.js" defer></script>');
   assert.ok(!html.includes("<!-- DATA_GOES_HERE -->")&&!html.includes("<!-- STYLE_GOES_HERE -->"));
   emit(`${dest}/trainers/${c.case_id}.html`,html);
  }
 }
 assert.equal([...output.keys()].filter(k=>k.endsWith(".html")).length,40);
 let listing=`---
layout: default
title: "Догматика — 40 электронных тренажёров"
---

# Догматическое различение — 40 тренажёров

**10 официальных текстов ФОС и 30 учебных вариантов.** Одна программная система: «Скриптура → Ересь → Таксономия → Апология». Три последовательных этапа: обнаружение, распределение по учениям и православное опровержение.

[Все вопросы Догматики](../index.html) · [Практика](../../../practice/index.html) · [Методика](../practice/methodology.html) · [Таблица ересей](../practice/heresy-comparison.html)

| Практическое | Основной ФОС | Учебные варианты | Материалы |
|---|---|---|---|
`;
 for(const r of rows){
   const [main,...training]=r.links;
   listing+=`| №${r.practical} / ФОС №${r.fos} | [Официальный](${main.id}.html) | ${training.map((v,i)=>`[${i+1}](${v.id}.html)`).join(" · ")} | [L3](../q${fmt(r.fos)}-l3.html) · [L2](../q${fmt(r.fos)}-l2.html) · [L1](../q${fmt(r.fos)}-l1.html) · [Практикум](../practice/practicum-${fmt(r.practical)}.html) |\n`;
 }
 listing+=`
## Как работать

**I. Скриптура → Ересь:** перенесите из сплошного текста все ошибочные положения, оставив правильные. **II. Ересь → Таксономия:** распределите их по названиям учений; не все предложенные названия нужны. **III. Таксономия → Апология:** выберите все верные исторические, богословские и православно-опровергающие положения. В конце сформулируйте устный ответ и сверьте его с L3.

**П8:** в исходном ФОС сказано «две ереси», но в тексте есть три различимые группы ошибочных учений. Здесь они не смешиваются; утверждение о «единой сложной ипостаси» не является само по себе ересью. ФОС не изменён.

*Тренажёр — учебная самопроверка, а не оценка экзаменационной комиссии.*
`;
 emit(`${dest}/trainers/index.md`,listing);
 function managed(rel,marker,text){
  const before=read(PUBLIC,rel),start=`<!-- ${marker}:start -->`,end=`<!-- ${marker}:end -->`;
  const block=`${start}\n${text.trim()}\n${end}`;
  let after;
  if(before.includes(start)){
   assert.ok(before.includes(end));
   after=before.replace(new RegExp(start+"[\\s\\S]*?"+end),block);
  }else{
   const anchor=rel===`${dest}/index.md`?"**15 теоретических вопросов и 10 практических заданий.**":null;
   after=anchor&&before.includes(anchor)?before.replace(anchor,anchor+"\n\n"+block):before.trimEnd()+"\n\n"+block+"\n";
  }
  emit(rel,after);
 }
 managed(`${dest}/index.md`,"dogmatics-2027-trainers",
 '**[40 электронных тренажёров Догматики](trainers/index.html)** — официальные тексты ФОС №16–25 и три тренировочных варианта к каждому.');
 managed("practice/index.md","dogmatics-2027-trainers",
 '**[Догматика — 40 электронных тренажёров](../subjects/dogmatics/2027/trainers/index.html)** — 10 практических номеров ФОС и 30 учебных вариантов.');
 for(const r of rows){
  const id=`official-${fmt(r.practical)}`,no=fmt(r.fos);
  for(const level of ["l3","l2","l1"])
   managed(`${dest}/q${no}-${level}.md`,"dogmatics-2027-trainer-links",
     `[Электронный тренажёр ФОС №${r.fos}](trainers/${id}.html) · [Все учебные варианты](trainers/index.html)`);
  managed(`${dest}/practice/practicum-${fmt(r.practical)}.md`,"dogmatics-2027-trainer-links",
     `**[Пройти официальный электронный тренажёр](../trainers/${id}.html)** · [Другие варианты](../trainers/index.html) · [L3](../q${no}-l3.html)`);
 }
 const navPath="_includes/global-navigation.html";
 let nav=read(PUBLIC,navPath);
 const anchor="{%- if exam_subject == 'liturgics' %}";
 assert.ok(nav.includes(anchor));
 if(!nav.includes("Тренажёры Догматики"))nav=nav.replace(anchor,`{%- if exam_subject == 'dogmatics' %}
    <a class="exam-global-nav__link" href="{{ '/subjects/dogmatics/2027/trainers/index.html' | relative_url }}">Тренажёры Догматики</a>
    {%- endif %}
    `+anchor);
 emit(navPath,nav);
 for(const [rel,s] of output){
  const f=path.join(PUBLIC,rel);
  if(check){assert.ok(fs.existsSync(f),"Missing "+rel);assert.equal(read(PUBLIC,rel),s,"Drift "+rel);}
  else{fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,s);}
 }
 console.log("PASS Stage 9 "+registry.cases.length+" browser pages, common engine, "+output.size+" managed files ("+(check?"check":"write")+").");
}
generate().catch(e=>{console.error(e.stack||e);process.exit(1)});
