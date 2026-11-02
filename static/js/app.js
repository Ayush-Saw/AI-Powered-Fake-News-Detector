document.addEventListener("DOMContentLoaded", () => {
  const area = document.getElementById("article_text"),
    count = document.getElementById("char-count");
  if (area && count) {
    const update = () =>
      (count.textContent = area.value.length.toLocaleString());
    area.addEventListener("input", update);
    update();
  }
  const filter = document.getElementById("history-filter"),
    table = document.getElementById("history-table");
  if (filter && table)
    filter.addEventListener("input", () => {
      const q = filter.value.toLowerCase();
      table
        .querySelectorAll("tr:not(:first-child)")
        .forEach((r) => (r.hidden = !r.innerText.toLowerCase().includes(q)));
    });
  const canvas = document.getElementById("prediction-chart");
  if (canvas && window.Chart)
    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: ["Likely Fake output", "Likely Real output"],
        datasets: [{ data: [+canvas.dataset.fake, +canvas.dataset.real] }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
      },
    });
  const quiz = document.getElementById("quiz-form");
  if (quiz)
    quiz.addEventListener("submit", (e) => {
      e.preventDefault();
      const a = new FormData(quiz).get("answer"),
        p = document.getElementById("quiz-feedback");
      p.textContent =
        a === "b"
          ? "Correct. Original evidence and independent reliable sources are stronger verification."
          : "Not quite. Popularity and AI confidence are not proof. Check original evidence and independent sources.";
      p.className = a === "b" ? "success-text" : "danger-text";
    });
});
