---
layout: default
title: Литургика — экзаменационные тренажёры 2027
---

# Литургика — экзаменационные тренажёры

**[Богослужебный практикум — курс из 10 занятий](../practicum/index.html)** · учебный план и будущие лекции.


**[Последовательная экзаменационная тренировка: один, выбранные или все 15](sequence.html)**

Практические вопросы **№1–15 нового ФОС БПДС**. Два равноправных вида заданий: **«Составь богослужение»** и **«Найди и исправь ошибки»**. Готовые задания открываются сразу; отсутствующие пополняются по мере проверки источников. Это учебная самопроверка, не аттестованная оценка экзамена.

[Богослужебный год — готовые учебные случаи](year.html) · [Литургика — все 25 официальных вопросов](../index.html) · [Методика составления служб](../practice/methodology-a.html) · [Методика литургических чинов](../practice/methodology-b.html)

{% assign trainer_prefix = '/subjects/liturgics/2027/' %}
{% for question in site.data.liturgics_trainers_2027.questions %}
<p data-question="{{ question.id }}">
<strong>№{{ question.number }}. {{ question.title }}</strong>
{% if question.cases.size > 0 %}
{% for game in question.cases %}
{% assign link = trainer_prefix | append: game.path %}
· <a href="{{ link | relative_url }}">{{ game.label }}</a>
{% endfor %}

{% else %}
· <span>Игра готовится</span>
{% endif %}
· <a href="{{ trainer_prefix | append: 'practice/q' | append: question.id | append: '.html' | relative_url }}">Практикум</a>
· <a href="{{ trainer_prefix | append: 'examples/q' | append: question.id | append: '.html' | relative_url }}">Задания преподавателя</a>
· <a href="{{ trainer_prefix | append: 'q' | append: question.id | append: '-l3.html' | relative_url }}">L3</a>
</p>
{% endfor %}

После правильной сборки в каждой игре открывается ссылка на полный разбор L3 того же билета. Непроверенные варианты не получают автоматическую экзаменационную оценку.

<details>
<summary>Варианты А/Б/В: 45 паспортов — 14 игр доступны, 31 задание готово к изготовлению</summary>
{% for question in site.data.liturgics_trainers_2027.questions %}
{% if question.number <= 15 %}
<p><strong>Вопрос №{{ question.number }}. {{ question.title }}</strong></p>
{% for variant in site.data.liturgics_trainers_2027.variant_slots %}
{% if variant.question == question.number %}
<p>Вариант {{ variant.variant }} — {{ variant.condition }}.
{% if variant.status == 'published_training' %}
{% for game in question.cases %}{% if game.case_id == variant.case_id %}{% assign href = trainer_prefix | append: game.path %}<a href="{{ href | relative_url }}">Открыть игру</a>{% endif %}{% endfor %}
{% elsif variant.status == 'task_defined_key_pending' %}
Условия достаточны; игра по названным изменениям ещё не изготовлена.
{% else %}
Игра пока не опубликована.
{% endif %}</p>
{% endif %}
{% endfor %}
{% endif %}
{% endfor %}
</details>

Неуказанные в задании обстоятельства не нужно устанавливать или считать пробелом. Игры появляются после изготовления и проверки соответствующих кирпичиков. Статус всех 45 паспортов хранится в общем реестре, без дублирования службы.

