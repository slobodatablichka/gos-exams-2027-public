---
layout: default
title: "Вечерня и утреня — исходная таблица"
---

<link rel="stylesheet" href="{{ '/assets/liturgics/vespers-matins-viewer.css' | relative_url }}">

# Вечерня и утреня. Исходная таблица

Таблица для изучения **17 вариантов богослужения**: вседневных, шестеричных, славословных, полиелейных, бденных, воскресных и праздничных служб.

[← Цифровая таблица](vespers-matins.html) · [Литургика — вопросы ФОС](index.html) · [Знаки служб](service-signs.html) · [Материал к вопросам №1–6](practicum/materials/evening-matins-comparison-2026-11-22.html)

<div id="liturgics-table-app"
 data-base="{{ '/assets/liturgics/vespers-matins-image' | relative_url }}"
 data-signs="{{ '/assets/liturgics/service-signs' | relative_url }}">

  <div class="lit-signs" aria-label="Знаки богослужебных служб">
    <span><img src="{{ '/assets/liturgics/service-signs/shesterichnaya.svg' | relative_url }}" alt="">Шестеричная</span>
    <span><img src="{{ '/assets/liturgics/service-signs/slavoslovnaya.svg' | relative_url }}" alt="">Славословная</span>
    <span><img src="{{ '/assets/liturgics/service-signs/polieleynaya.svg' | relative_url }}" alt="">Полиелейная</span>
    <span><img src="{{ '/assets/liturgics/service-signs/bdennaya-srednego-svyatogo.svg' | relative_url }}" alt="">Бденная среднего святого</span>
    <span><img src="{{ '/assets/liturgics/service-signs/bdennaya-velikogo-svyatogo.svg' | relative_url }}" alt="">Бденная великого святого</span>
    <span><img src="{{ '/assets/liturgics/service-signs/gospodskiy-prazdnik.svg' | relative_url }}" alt="">Господский праздник</span>
    <span><img src="{{ '/assets/liturgics/service-signs/bogorodichnyy-dvunadesyatyy.svg' | relative_url }}" alt="">Богородичный праздник</span>
  </div>

  <div class="lit-switch" role="group" aria-label="Режим просмотра">
    <button type="button" data-view="full" aria-pressed="true">Вся таблица</button>
    <button type="button" data-view="mobile" aria-pressed="false">Одна служба</button>
    <button type="button" data-view="compare" aria-pressed="false">Сравнить строки</button>
  </div>

  <div class="lit-controls">
    <label>Вид службы
      <select id="lit-service" aria-label="Выберите вид службы"></select>
    </label>
    <label>Часть службы
      <select id="lit-row" aria-label="Выберите строку для сравнения"></select>
    </label>
    <label>Увеличение общей таблицы
      <select id="lit-zoom" aria-label="Масштаб общей таблицы">
        <option value="1">100%</option>
        <option value="1.5" selected>150%</option>
        <option value="2">200%</option>
        <option value="3">300%</option>
        <option value="4">400%</option>
      </select>
    </label>
  </div>

  <p class="lit-status" id="lit-status" role="status">Загрузка таблицы…</p>

  <section class="lit-view" id="lit-full-view">
    <p class="lit-guides">Прокручивайте таблицу по горизонтали и вертикали. Для чтения мелкого текста выберите увеличение 200–400%.</p>
    <div class="lit-scroll" tabindex="0" aria-label="Полная таблица вечерни и утрени с горизонтальной и вертикальной прокруткой">
      <canvas id="lit-full" role="img" aria-label="Полная сравнительная таблица состава вечерни и утрени по семнадцати видам службы"></canvas>
    </div>
  </section>

  <section class="lit-view" id="lit-mobile-view" hidden>
    <p class="lit-guides">Выберите вид службы выше. Слева — части богослужения, справа — соответствующий порядок по выбранной колонке.</p>
    <div id="lit-service-heading" class="lit-service-heading"></div>
    <canvas id="lit-mobile" role="img" aria-label="Последование выбранного вида службы"></canvas>
  </section>

  <section class="lit-view" id="lit-compare-view" hidden>
    <p class="lit-guides">Выберите часть богослужения выше. Она появится во всех семнадцати вариантах.</p>
    <h2 id="lit-row-title">Сравнение частей службы</h2>
    <div id="lit-compare" class="lit-compare-grid"></div>
  </section>

</div>

<script defer src="{{ '/assets/liturgics/vespers-matins-viewer.js' | relative_url }}"></script>

## Подготовка к экзамену

[№1. Седмичные и субботние службы](q01-l3.html) · [№2. Воскресное бдение](q02-l3.html) · [№3. Великие праздники](q03-l3.html) · [№4. Предпразднства и попразднства](q04-l3.html) · [№5. Великий пост](q05-l3.html) · [№6. Страстная и Светлая седмицы](q06-l3.html)

Порядок вечерни и утрени изучается вместе с **Типиконом, Часословом, Октоихом, Минеей и Триодями**. Для экзамена необходимо также составлять последование часов. Особые уставные главы Великого поста, Страстной и Светлой седмиц изучаются по соответствующим богослужебным книгам.

[← Литургика](index.html)
