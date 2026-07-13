const root = document.documentElement;
const savedTheme = localStorage.getItem("theme");
if (savedTheme) root.dataset.theme = savedTheme;
document.querySelector("#theme-toggle")?.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("theme", next);
});

