async function test(){
 const fs=(await import("node:fs")).default;
 const path=(await import("node:path")).default;
 const {fileURLToPath,pathToFileURL}=await import("node:url");
 const assert=(await import("node:assert/strict")).default;
 const {chromium}=await import("playwright");
 const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
 const dir="subjects/dogmatics/2027/trainers";
 const mustRead=p=>fs.readFileSync(path.join(ROOT,p),"utf8");
 const pages=fs.readdirSync(path.join(ROOT,dir)).filter(p=>/^(official|training)-\d\d(?:-[123])?\.html$/.test(p)).sort();
 assert.equal(pages.length,40,"Expected exactly 40 public trainer routes");
 assert.ok(fs.existsSync(path.join(ROOT,"assets/js/dogmatics-trainer.js")));
 assert.ok(fs.existsSync(path.join(ROOT,"assets/css/dogmatics-trainer.css")));
 const browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
 const errors=[];let done=0,blocks=0,links=0;
 const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:"reduce"});
 page.on("pageerror",e=>errors.push(e.message));
 const state=()=>page.evaluate(()=>window.StageFivePreview.getState());
 try{
  for(const file of pages){
   const html=mustRead(dir+"/"+file);
   const json=JSON.parse(html.match(/<script type="application\/json" id="case-data">([\s\S]*?)<\/script>/)?.[1]||"null");
   assert.ok(json&&json.case_id===file.slice(0,-5),"Embedded case/source mismatch");
   assert.equal(json.status,"accepted_data");
   assert.ok(!html.includes("private/blob/main")&&!html.includes("<!-- CORE_GOES_HERE -->"));
   const n=String(json.fos_no).padStart(2,"0");
   for(const stem of ["q"+n+"-l3.md","q"+n+"-l2.md","q"+n+"-l1.md"])
     assert.ok(fs.existsSync(path.join(ROOT,"subjects/dogmatics/2027",stem)));
   assert.ok(html.includes("href=\"../q"+n+"-l3.html\""));
   for(const id of [...new Set([json.case_id.replace(/(?:official|training)-/,"")])])assert.ok(id);
   await page.goto(pathToFileURL(path.join(ROOT,dir,file)).href);
   await page.waitForFunction(()=>window.StageFivePreview&&window.StageFivePreview.getState().stage===1,{timeout:10000}).catch(async e=>{
    const runtime=await page.evaluate(()=>({url:location.href,script:document.querySelector('script[src]')?.src,hasStageOne:!!window.StageOneCore,hasStageTwo:!!window.StageTwoCore,hasStageThree:!!window.StageThreeCore,hasPreview:!!window.StageFivePreview}));
    throw Error("Browser bootstrap failed "+file+": "+JSON.stringify(runtime)+"; page errors "+JSON.stringify(errors)+"; "+e.message);
   });
   assert.equal((await state()).sourceText,json.source.original_text);
   assert.ok((await page.title()).includes("№"+json.fos_no));
   assert.equal(await page.locator(".trainer-nav a").count()>=6,true);
   const wrong=json.sentence_groups.flatMap(g=>g.draggables).filter(x=>x.judgment==="heresy");
   for(const u of wrong){
    await page.locator('[data-origin="source"][data-unit-id="'+u.id+'"]').focus();
    await page.keyboard.press("Enter");
   }
   await page.locator("#check-button").click();
   assert.equal((await state()).stage1Result.correct,true);
   await page.locator("#next-button").click();
   await page.waitForFunction(()=>window.StageFivePreview.getState().stage===2);
   for(const u of wrong)await page.locator('[data-stage2-item="true"][data-unit-id="'+u.id+'"] select').selectOption(u.heresies[0]);
   await page.locator("#check-button").click();
   assert.equal((await state()).stage2Result.correct,true);
   await page.locator("#next-apology-button").click();
   await page.waitForFunction(()=>window.StageFivePreview.getState().stage===3);
   assert.equal(await page.locator("#apology-progress .apology-step").count(),json.apology.blocks.length);
   for(let i=0;i<json.apology.blocks.length;i++){
    const b=json.apology.blocks[i];
    for(const o of b.options.filter(x=>x.correct))
     await page.locator('[data-apology-id="'+o.id+'"]').check();
    await page.locator("#apology-check").click();
    assert.equal((await state()).stage3Result.correct,true);
    const urls=await page.locator("#apology-feedback .apology-evidence").evaluateAll(els=>els.map(x=>x.getAttribute("href")));
    assert.ok(urls.length>0,"No public evidence links");
    for(const url of urls){
     assert.ok(!url.includes("/gos-exams-2027/blob/main"),"Private GitHub evidence link in public trainer");
     if(!url.startsWith("https:"))assert.ok(fs.existsSync(path.resolve(ROOT,dir,url.replace(/\.html$/,".md"))),"Local source link missing: "+url);
    }
    links+=urls.length;blocks++;
    if(i<json.apology.blocks.length-1)await page.locator("#apology-next").click();
   }
   assert.equal((await state()).stage3Completed,true);
   assert.ok((await page.locator("#oral-l3").getAttribute("href")).endsWith("q"+n+"-l3.html"));
   if(json.practical_no===8)assert.equal(await page.locator("#p8-note").isVisible(),true);
   await page.locator("#back-taxonomy").click();
   await page.waitForFunction(()=>window.StageFivePreview.getState().stage===2);
   await page.locator("#restart-button").click();
   assert.equal((await state()).sourceText,json.source.original_text);
   done++;
  }
  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:"reduce"});
  mobile.on("pageerror",e=>errors.push(e.message));
  for(const id of ["official-03","official-08","training-10-3"]){
   await mobile.goto(pathToFileURL(path.join(ROOT,dir,id+".html")).href);
   await mobile.waitForFunction(()=>window.StageFivePreview&&window.StageFivePreview.getState().stage===1);
   const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);
   assert.equal(overflow,false,"Mobile horizontal overflow "+id);
   assert.ok(await mobile.locator(".trainer-nav a").count()>=6);
   const x=mobile.locator('[data-origin="source"][data-unit-id]').first();
   await x.tap();
   assert.equal((await mobile.evaluate(()=>window.StageFivePreview.getState())).selectedIds.length,1);
  }
  assert.deepEqual(errors,[]);
  console.log("PASS Stage 9 public: "+done+"/40 browser routes, "+blocks+" apology blocks, "+links+" visible source links, mobile touch/reduced-motion PASS, no JS errors.");
 }finally{await browser.close();}
}
test().catch(e=>{console.error(e.stack||e);process.exit(1)});
