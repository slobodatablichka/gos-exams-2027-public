---
layout: default
title: "Литургика — 61 электронный тренажёр · ФОС БПДС 2027"
---

# Электронные тренажёры по Литургике — 61 задание

**15 практических вопросов ФОС · 15 основных заданий · 45 вариантов А/Б/В · 1 дополнительное диагностическое задание №12.** Все 61 задания имеются в действующем реестре и доступны по прямым ссылкам. Это учебная самопроверка, не официальная экзаменационная оценка: для ряда вариантов полный автоматический ключ ещё не аттестован.

**С чего начать:** [программа десяти занятий](../practicum/index.html) → **занятие №1, 2, 3 или 4** → соответствующая тема ниже → **основной тренажёр** → **вариант А**. Полные L3 и задания преподавателя открываются из каждой строки и из самого тренажёра.

[Литургика — все 25 вопросов](../index.html) · [Последовательная самопроверка](sequence.html) · [Богослужебный год](year.html) · [Методика составления служб](../practice/methodology-a.html) · [Методика литургических чинов](../practice/methodology-b.html)

## Первый круг — занятия №1–4: основной тренажёр и вариант А

**Учебные комплекты занятий №1–4 опубликованы.** Ниже задания расположены **в порядке их прохождения по занятиям**, а не в числовом порядке ФОС. Номер официального вопроса сохраняется.

{% assign trainer_prefix = '/subjects/liturgics/2027/' %}
{% assign lesson_codes = '01,02,03,04' | split: ',' %}
{% for lesson_code in lesson_codes %}
{% if lesson_code == '01' %}
 {% assign selected_ids = '01,02,10' | split: ',' %}{% assign lesson_caption = 'Основы богослужебного устава' %}
{% elsif lesson_code == '02' %}
 {% assign selected_ids = '03,04,07,08' | split: ',' %}{% assign lesson_caption = 'Праздники и соединение служб' %}
{% elsif lesson_code == '03' %}
 {% assign selected_ids = '05,06,09,15' | split: ',' %}{% assign lesson_caption = 'Постный и Пасхальный круги' %}
{% else %}
 {% assign selected_ids = '11,12,13,14' | split: ',' %}{% assign lesson_caption = 'Божественная литургия' %}
{% endif %}

### Занятие №{{ lesson_code }} — {{ lesson_caption }}
{: #lesson-{{ lesson_code }} }

[Лекция, схемы, образцы и домашняя работа](../practicum/materials/lesson-{{ lesson_code }}.html) · [План и задания занятия](../practicum/lessons/{{ lesson_code }}.html)

<table>
<thead><tr><th>ФОС и тема</th><th>Основной тренажёр</th><th>Вариант А</th><th>Разбор и теория</th></tr></thead>
<tbody>
{% for question in site.data.liturgics_trainers_2027.questions %}
{% if selected_ids contains question.id %}
 {% assign main_case = question.cases | first %}
 {% assign variant_a = question.cases | where: 'variant', 'А' | first %}
 <tr id="fos-{{ question.id }}">
 <td><strong>№{{ question.number }}. {{ question.title }}</strong></td>
 <td><a href="{{ trainer_prefix | append: main_case.path | relative_url }}">{{ main_case.label }}</a></td>
 <td>{% if variant_a %}<a href="{{ trainer_prefix | append: variant_a.path | relative_url }}">{{ variant_a.label }}</a>{% else %}—{% endif %}
 {% for slot in site.data.liturgics_trainers_2027.variant_slots %}{% if slot.question == question.number and slot.variant == 'А' %}<small>{{ slot.condition }}</small>{% endif %}{% endfor %}
 </td>
 <td><a href="{{ trainer_prefix | append: 'examples/q' | append: question.id | append: '.html' | relative_url }}">Задание преподавателя</a> · <a href="{{ trainer_prefix | append: 'q' | append: question.id | append: '-l3.html' | relative_url }}">L3</a></td>
 </tr>
{% endif %}
{% endfor %}
</tbody></table>
{% endfor %}

## Второй круг — уже опубликованные варианты Б и В

**Варианты Б и В существуют и доступны**, но новые лекции и комплектные задания занятий **№5–10 не разрабатываются до завершения первого круга и анализа его результатов**. Эти варианты можно открывать самостоятельно; их наличие не означает готовности методики второго круга.

<details>
<summary>Показать варианты Б и В всех 15 практических вопросов</summary>
<table><thead><tr><th>Вопрос ФОС</th><th>Вариант Б</th><th>Вариант В</th></tr></thead><tbody>
{% for question in site.data.liturgics_trainers_2027.questions %}
{% assign variant_b = question.cases | where: 'variant', 'Б' | first %}
{% assign variant_v = question.cases | where: 'variant', 'В' | first %}
<tr><td>№{{ question.number }}. {{ question.title }}</td><td><a href="{{ trainer_prefix | append: variant_b.path | relative_url }}">Вариант Б</a>{% for slot in site.data.liturgics_trainers_2027.variant_slots %}{% if slot.question == question.number and slot.variant == 'Б' %}<small>{{ slot.condition }}</small>{% endif %}{% endfor %}</td><td><a href="{{ trainer_prefix | append: variant_v.path | relative_url }}">Вариант В</a>{% for slot in site.data.liturgics_trainers_2027.variant_slots %}{% if slot.question == question.number and slot.variant == 'В' %}<small>{{ slot.condition }}</small>{% endif %}{% endfor %}</td></tr>
{% endfor %}
</tbody></table>
<p><a href="{{ '/subjects/liturgics/2027/sandbox-pyramid/q12-errors.html' | relative_url }}">Дополнительное диагностическое задание №12</a> — отдельная проверка последовательности Литургии оглашенных, не входящая в восемь заданий занятия №4.</p>
</details>

## Где искать нужный материал

| Требуется | Открыть |
|---|---|
| **Пройти занятие**: лекция → схема → образец → домашняя работа | [Программа №1–10](../practicum/index.html) |
| **Найти конкретный номер практического ФОС** | Таблицы первого круга выше: №1–15, с прямыми ссылками на основной и вариант А |
| **Найти все варианты одного вопроса** | Сначала открыть его тренажёр: внутри есть ссылки **«Основной / А / Б / В»** |
| **Пройти несколько заданий подряд в свободном порядке** | [Последовательная самопроверка](sequence.html) |
| **Проверить ответ и обоснование** | В каждой строке — **L3** и **задание преподавателя** |
| **Выбрать службу по периоду церковного года** | [Богослужебный год](year.html) |

**Правило проверки:** не домысливать условия, которых нет в задании; в диагностике исправлять конкретную ошибку, а не подменять её другим чином. Проверенные источниковые границы L3 остаются в силе.
