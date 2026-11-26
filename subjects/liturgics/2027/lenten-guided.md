---
layout: default
title: "Великопостное богослужение — изучение и самопроверка"
---

# Великопостное богослужение

[← Все последования](quiz/index.html)

<style>
#full-day-guide{max-width:850px;margin:auto;overflow-wrap:anywhere}
#full-day-guide [hidden]{display:none!important}
#full-day-guide .fd-fields{display:grid;grid-template-columns:1fr 2fr;gap:12px}
#full-day-guide label{display:block;font-weight:600}
#full-day-guide select,#full-day-guide button{font:inherit;padding:.7rem;border:1px solid #8ca4a7;border-radius:7px;background:transparent;color:inherit;cursor:pointer}
#full-day-guide select{width:100%;background:var(--bg,#fff);color:var(--text,#222)}
#full-day-guide button:disabled{opacity:.6;cursor:default}
#full-day-guide .fd-primary{display:block;width:100%;background:#286871;color:white;border-color:#286871;font-weight:600;margin:.8rem 0}
#full-day-guide .fd-card{border:1px solid #a4b6b8;border-radius:9px;padding:1rem;margin:1rem 0}
#full-day-guide .fd-current{border:2px solid #397e89}
#full-day-guide .fd-heading{border-bottom:2px solid #397e89;padding-bottom:.5rem}
#full-day-guide .fd-map{padding-left:1.6rem}
#full-day-guide .fd-map li{padding:.5rem;border-bottom:1px solid #a4b6b850}
#full-day-guide small{display:block;opacity:.8}
#full-day-guide details{margin:.75rem 0;padding:.7rem;border:1px solid #a4b6b8;border-radius:7px}
#full-day-guide summary{cursor:pointer;font-weight:600}
#full-day-guide .fd-service,#full-day-guide .fd-choice{display:block;width:100%;text-align:left;margin:.4rem 0}
#full-day-guide .fd-correct{border-color:#39835c;background:#39835c22}
#full-day-guide .fd-wrong{border-color:#b65350;background:#b6535022}
#full-day-guide .fd-nav{display:flex;gap:.5rem;flex-wrap:wrap}
#full-day-guide progress{width:100%}
#full-day-guide button:focus-visible,#full-day-guide select:focus-visible{outline:3px solid #397e89;outline-offset:2px}
#fd-jump{position:fixed;bottom:1rem;right:1rem;z-index:20;background:#286871!important;color:white!important}
@media(max-width:550px){#full-day-guide .fd-fields{grid-template-columns:1fr}#full-day-guide .fd-card{padding:.7rem}}
@media(prefers-color-scheme:dark){#full-day-guide select{background:#202426;color:#eee}}
</style>
<div id="full-day-guide" data-source="{{ '/assets/liturgics/lenten-full-day-data.json' | relative_url }}">
 <p id="fd-status" role="status">Загрузка последований…</p>
 <div id="fd-loaded" hidden>
  <section id="fd-picker">
   <div class="fd-fields"><label>Период<select id="fd-period"><option value="1">Основные службы</option><option value="2">Особые дни</option><option value="3">Страстная седмица</option></select></label><label>Богослужебный день<select id="fd-day"></select></label></div>
   <div id="fd-overview"></div>
  </section>
  <section id="fd-reader" hidden>
   <div class="fd-nav"><button id="fd-back" type="button">← К выбору дня</button><button id="fd-pause" type="button">Пауза</button><button id="fd-reset" type="button">Начать заново</button></div>
   <h2 id="fd-title"></h2><p id="fd-count" role="status"></p><progress id="fd-progress" value="0" max="1"></progress><p id="fd-stats"></p>
   <div id="fd-stream"></div><button id="fd-jump" type="button" hidden>К текущему шагу</button>
  </section>
 </div>
</div>
<script src="{{ '/assets/liturgics/lenten-full-day.js' | relative_url }}" defer></script>

[Вопрос №2](q02-l3.html) · [Вопрос №5](q05-l3.html) · [Вопрос №6](q06-l3.html) · [Вопрос №15](q15-l3.html)
