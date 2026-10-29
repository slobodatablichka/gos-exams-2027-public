(() => {
  "use strict";
  const root = document.getElementById("roleplan");
  const group = document.getElementById("roleplan-size");
  const jump = document.getElementById("roleplan-jump");
  const note = document.getElementById("roleplan-note");
  if (!root || !group || !jump || !note) return;
  const info = {
    "5a": ["5", 0, "Группа 1: условные номера Студент 1–5."],
    "5b": ["5", 5, "Группа 2: условные номера Студент 6–10."],
    "6": ["6", 0, "Вариант на шестерых: номера 1–6 — позиции внутри группы."],
    "7": ["7", 0, "Вариант на семерых: номера 1–7 — позиции внутри группы."]
  };
  function refresh() {
    const item = info[group.value] || info["5a"];
    root.dataset.size = item[0];
    note.textContent = item[2];
    for (const el of root.querySelectorAll(".roleplan-person")) {
      const slot = Number(el.dataset.slot);
      el.textContent = "Студент " + (slot + item[1]);
    }
  }
  group.addEventListener("change", refresh);
  jump.addEventListener("change", () => {
    const target = document.getElementById(jump.value);
    if (!target) return;
    target.open = true;
    target.scrollIntoView({block:"start",behavior:"smooth"});
  });
  refresh();
})();