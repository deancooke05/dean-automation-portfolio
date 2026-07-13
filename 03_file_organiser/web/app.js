const views = ["setupView", "previewView", "successView"];
const $ = (id) => document.getElementById(id);
let defaults = {};

function showView(id) {
  views.forEach((view) => $(view).classList.toggle("active", view === id));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toast(message) {
  const box = $("toast");
  box.textContent = message;
  box.classList.add("show");
  setTimeout(() => box.classList.remove("show"), 4200);
}

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request could not be completed");
  return data;
}

function loadDefaults() {
  $("source").value = defaults.source;
  $("destination").value = defaults.destination;
}

function renderPreview(plan) {
  const summary = plan.summary;
  $("fileCount").textContent = summary.files;
  $("categoryCount").textContent = summary.categories;
  $("dataSize").textContent = summary.formatted_size;
  $("collisionCount").textContent = summary.collisions;
  $("modeBadge").textContent = plan.mode.toUpperCase();
  $("actionCount").textContent = `${summary.files} planned action${summary.files === 1 ? "" : "s"}`;
  $("previewPath").textContent = `${plan.source_root}  →  ${plan.destination_root}`;
  $("approvalText").textContent = plan.mode === "copy" ? "Your originals will remain untouched." : "Every move is recorded and can be undone.";
  $("categoryList").innerHTML = Object.entries(summary.category_counts).map(([name, count]) => `
    <div class="category-item"><span class="folder-icon">▱</span><span><b>${escapeHtml(name)}</b><small>automatic folder</small></span><span>${count}</span></div>`).join("");
  $("actionRows").innerHTML = plan.actions.map((action) => `
    <tr><td>${escapeHtml(action.file_name)}${action.collision ? " · safe rename" : ""}</td><td>${escapeHtml(action.category)}</td><td>${action.formatted_size}</td><td class="destination-cell" title="${escapeHtml(action.destination_display)}">${escapeHtml(action.destination_display)}</td></tr>`).join("");
  showView("previewView");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

document.querySelectorAll(".choice input").forEach((input) => input.addEventListener("change", () => {
  document.querySelectorAll(".choice").forEach((choice) => choice.classList.remove("selected"));
  input.closest(".choice").classList.add("selected");
}));

$("demoButton").addEventListener("click", loadDefaults);
document.querySelectorAll(".browse-button").forEach((button) => button.addEventListener("click", async () => {
  const target = $(button.dataset.target);
  button.disabled = true;
  try {
    const result = await request("/api/choose-folder", { method: "POST", body: JSON.stringify({ initial: target.value }) });
    if (result.path) target.value = result.path;
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
}));
$("backButton").addEventListener("click", () => showView("setupView"));
$("againButton").addEventListener("click", () => { loadDefaults(); showView("setupView"); });

$("setupForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true; button.querySelector("span").textContent = "Reviewing files…";
  try {
    const plan = await request("/api/preview", { method: "POST", body: JSON.stringify({
      source: $("source").value.trim(), destination: $("destination").value.trim(),
      mode: document.querySelector('input[name="mode"]:checked').value, recursive: $("recursive").checked,
    }) });
    renderPreview(plan);
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.querySelector("span").textContent = "Create safe preview"; }
});

$("applyButton").addEventListener("click", async () => {
  const button = $("applyButton"); button.disabled = true; button.querySelector("span").textContent = "Organising…";
  try {
    const result = await request("/api/apply", { method: "POST", body: "{}" });
    $("successCopy").textContent = `${result.summary.completed} file${result.summary.completed === 1 ? "" : "s"} organised across ${result.summary.categories} categories. A complete local audit record is ready.`;
    $("receiptText").textContent = `${result.summary.formatted_size} · ${result.mode.toUpperCase()} MODE · ${result.summary.completed} COMPLETE`;
    showView("successView");
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.querySelector("span").textContent = "Organise these files"; }
});

request("/api/defaults").then((data) => { defaults = data; loadDefaults(); }).catch((error) => toast(error.message));
