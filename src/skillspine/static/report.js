const layout = document.getElementById("layout"),
  search = document.getElementById("search"),
  affected = document.getElementById("affected");
function update() {
  let visible = 0;
  document
    .querySelectorAll(".mode-panel")
    .forEach((p) => (p.hidden = p.dataset.mode !== layout.value));
  document.querySelectorAll(".skill").forEach((s) => {
    s.hidden = !(
      s.textContent.toLowerCase().includes(search.value.toLowerCase()) &&
      (!affected.checked || s.dataset.affected === "true")
    );
    if (!s.hidden) visible++;
  });
  document.getElementById("empty").hidden = visible !== 0;
  document.getElementById("visible-count").textContent =
    visible + " skills shown";
}
[layout, search, affected].forEach((e) => e.addEventListener("input", update));
update();
document.getElementById("download").addEventListener("click", () => {
  const blob = new Blob([document.getElementById("report-data").textContent], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "skillspine-report.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
