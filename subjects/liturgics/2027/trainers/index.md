---
layout: default
title: Литургика — экзаменационные тренажёры 2027
---

# Литургика — экзаменационные тренажёры

Практические вопросы **№1–15 нового ФОС БПДС**. Два равноправных вида заданий: **«Составь богослужение»** и **«Найди и исправь ошибки»**. Готовые задания открываются сразу; отсутствующие пополняются по мере проверки источников. Это учебная самопроверка, не аттестованная оценка экзамена.

[Литургика — все 25 официальных вопросов](../index.html) · [Методика составления служб](../practice/methodology-a.html) · [Методика литургических чинов](../practice/methodology-b.html)

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
