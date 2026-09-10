from __future__ import annotations

from html import escape
import json
from pathlib import Path


def load_packages(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Video package data must be a list.")
    return data


def render_dashboard(packages: list[dict]) -> str:
    fallback_json = escape(json.dumps(packages))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local Voice Engine</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <p class="eyebrow">Neuse News</p>
        <h1>Local Voice Engine</h1>
      </div>
      <label class="brand-switcher">
        <span>Brand workspace</span>
        <select id="workspaceBrandSelect"></select>
      </label>
      <div class="workflow">
        <span>1. Pick story</span>
        <span>2. Select template</span>
        <span>3. Approve text</span>
        <span>4. Create video</span>
      </div>
    </header>

    <section class="studio">
      <aside class="story-list">
        <div class="panel-heading">
          <h2>News articles</h2>
          <div class="panel-actions">
            <button id="importButton" type="button">Import all</button>
            <button id="refreshButton" type="button">Refresh</button>
          </div>
        </div>
        <div id="storyList"></div>
      </aside>

      <section class="workspace">
        <div id="emptyState" class="empty-state">
          <h2>Select a story</h2>
          <p>Choose an article to load its template, review the script and create a video.</p>
        </div>

        <article id="storyWorkspace" class="story-workspace hidden">
          <div class="story-header">
            <div>
              <p id="storyMeta" class="eyebrow"></p>
              <h2 id="storyHeadline"></h2>
            </div>
            <a id="sourceLink" class="source-link" href="#" target="_blank" rel="noreferrer">Source story</a>
          </div>

          <label class="field">
            <span>Brand kit</span>
            <select id="brandSelect"></select>
          </label>

          <label class="field">
            <span>Video template</span>
            <select id="templateSelect"></select>
          </label>

          <div class="template-summary" id="templateSummary"></div>

          <label class="field">
            <span>Voiceover text</span>
            <textarea id="scriptEditor" spellcheck="true"></textarea>
          </label>
          <button id="draftVoiceoverButton" class="secondary-action wide-action" type="button">Draft voiceover from article</button>

          <div class="visual-beats-panel">
            <div class="visual-beats-header">
              <div>
                <h3>Visual text</h3>
                <p>Write each screen as its own short visual beat.</p>
              </div>
              <button id="syncVisualTextButton" class="secondary-action" type="button">Draft from voiceover</button>
            </div>
            <div id="visualBeatFields" class="visual-beat-fields"></div>
          </div>

          <div class="media-panel">
            <div>
              <h3>Images</h3>
              <p>Upload one headshot and up to three article images. These will be used before the RSS image.</p>
            </div>
            <label class="file-field">
              <span>Headshot</span>
              <input id="headshotInput" type="file" accept="image/*">
            </label>
            <label class="file-field">
              <span>Article images</span>
              <input id="articleImagesInput" type="file" accept="image/*" multiple>
            </label>
            <button id="uploadImagesButton" type="button">Save images</button>
            <div id="mediaStatus" class="media-status"></div>
          </div>

          <div class="actions">
            <button id="approveButton" type="button">Approve text</button>
            <button id="renderButton" type="button">Create video</button>
          </div>

          <div id="statusBox" class="status-box"></div>
          <video id="videoPreview" class="video-preview hidden" controls></video>
        </article>
      </section>
    </section>
  </main>

  <script>
    window.FALLBACK_PACKAGES = JSON.parse("{fallback_json}".replace(/&quot;/g, '"'));
  </script>
  <script src="studio.js"></script>
</body>
</html>
"""


def write_dashboard(data_path: Path, output_dir: Path) -> Path:
    packages = load_packages(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "index.html"
    css_path = output_dir / "style.css"
    js_path = output_dir / "studio.js"
    html_path.write_text(render_dashboard(packages), encoding="utf-8")
    css_path.write_text(STYLES, encoding="utf-8")
    js_path.write_text(SCRIPT, encoding="utf-8")
    return html_path


STYLES = """
:root {
  color-scheme: light;
  --ink: #1f252b;
  --muted: #62707a;
  --line: #d9e0e5;
  --paper: #f6f8f9;
  --panel: #ffffff;
  --green: #275f50;
  --blue: #2e5f8a;
  --red: #9b3d38;
  --gold: #b27825;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Arial, Helvetica, sans-serif;
}

main {
  max-width: 1380px;
  margin: 0 auto;
  padding: 24px;
}

.topbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--green);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1, h2, h3, p { margin-top: 0; }
h1 { margin-bottom: 0; font-size: 34px; line-height: 1.1; }
h2 { margin-bottom: 10px; font-size: 22px; line-height: 1.2; }

.workflow {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.brand-switcher {
  display: grid;
  gap: 6px;
  min-width: 260px;
}

.brand-switcher span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.workflow span,
button,
select,
textarea,
.source-link { border-radius: 8px; }

.workflow span {
  padding: 8px 10px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--muted);
  font-size: 13px;
}

.studio {
  display: grid;
  grid-template-columns: 410px minmax(0, 1fr);
  gap: 18px;
  padding-top: 20px;
}

.story-list,
.workspace,
.template-summary,
.media-panel,
.visual-beats-panel,
.status-box {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 8px;
}

.story-list {
  max-height: calc(100vh - 130px);
  overflow: auto;
}

.panel-heading {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--line);
  background: #fff;
}

.panel-heading h2 { margin-bottom: 0; }

.story-button {
  display: block;
  width: 100%;
  padding: 14px 16px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.story-button:hover,
.story-button.active { background: #eef6f2; }

.story-button strong {
  display: block;
  margin-bottom: 6px;
  font-size: 15px;
  line-height: 1.25;
}

.story-button span {
  color: var(--muted);
  font-size: 13px;
}

.empty-list {
  padding: 18px;
  color: var(--muted);
  line-height: 1.45;
}

.workspace {
  min-height: calc(100vh - 130px);
  padding: 22px;
}

.empty-state {
  display: grid;
  place-content: center;
  min-height: 520px;
  color: var(--muted);
  text-align: center;
}

.hidden { display: none; }

.story-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 20px;
}

.source-link,
button {
  min-height: 40px;
  padding: 10px 14px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--blue);
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

button {
  color: #fff;
  border-color: var(--green);
  background: var(--green);
}

#refreshButton {
  color: var(--blue);
  border-color: var(--line);
  background: #fff;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

#importButton {
  color: #fff;
  border-color: var(--red);
  background: var(--red);
}

.field {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.field span {
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
}

select,
textarea {
  width: 100%;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  font: inherit;
}

select {
  min-height: 44px;
  padding: 0 12px;
}

textarea {
  min-height: 300px;
  padding: 14px;
  line-height: 1.5;
  resize: vertical;
}

.secondary-action {
  width: fit-content;
  color: var(--blue);
  border-color: var(--line);
  background: #fff;
}

.wide-action {
  margin: -4px 0 16px;
}

.visual-beats-panel {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
}

.visual-beats-header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 14px;
}

.visual-beats-header h3 {
  margin-bottom: 6px;
  font-size: 17px;
}

.visual-beats-header p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.4;
}

.visual-beat-fields {
  display: grid;
  gap: 10px;
}

.visual-beat {
  display: grid;
  gap: 6px;
}

.visual-beat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.visual-beat textarea {
  min-height: 86px;
}

.media-panel {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
}

.media-panel h3 {
  margin-bottom: 6px;
  font-size: 17px;
}

.media-panel p,
.media-status {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.4;
}

.file-field {
  display: grid;
  gap: 7px;
}

.file-field span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.template-summary {
  margin-bottom: 16px;
  padding: 14px;
  color: var(--muted);
  line-height: 1.45;
}

.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

#renderButton {
  background: var(--red);
  border-color: var(--red);
}

.status-box {
  min-height: 48px;
  padding: 14px;
  color: var(--muted);
}

.video-preview {
  width: min(360px, 100%);
  margin-top: 16px;
  background: #000;
  border-radius: 8px;
}

@media (max-width: 900px) {
  .topbar,
  .story-header { display: block; }
  .workflow { justify-content: flex-start; margin-top: 14px; }
  .studio { grid-template-columns: 1fr; }
  .story-list { max-height: 360px; }
}
"""


SCRIPT = r"""
const state = {
  packages: window.FALLBACK_PACKAGES || [],
  templates: {},
  brands: {},
  selected: null,
  visualTextDirty: false,
};

const templateNameToId = {
  "Meeting in a minute": "meeting_in_a_minute",
  "Crime story": "crime_story",
  "What happened next": "crime_story",
  "News story": "news_story",
  "Three things to know": "news_story",
  "Featured story": "featured_story",
  "Faces of the story": "featured_story",
};

const storyList = document.querySelector("#storyList");
const emptyState = document.querySelector("#emptyState");
const storyWorkspace = document.querySelector("#storyWorkspace");
const storyMeta = document.querySelector("#storyMeta");
const storyHeadline = document.querySelector("#storyHeadline");
const sourceLink = document.querySelector("#sourceLink");
const workspaceBrandSelect = document.querySelector("#workspaceBrandSelect");
const brandSelect = document.querySelector("#brandSelect");
const templateSelect = document.querySelector("#templateSelect");
const templateSummary = document.querySelector("#templateSummary");
const scriptEditor = document.querySelector("#scriptEditor");
const visualBeatFields = document.querySelector("#visualBeatFields");
const statusBox = document.querySelector("#statusBox");
const videoPreview = document.querySelector("#videoPreview");
const renderButton = document.querySelector("#renderButton");
const approveButton = document.querySelector("#approveButton");
const uploadImagesButton = document.querySelector("#uploadImagesButton");
const draftVoiceoverButton = document.querySelector("#draftVoiceoverButton");
const syncVisualTextButton = document.querySelector("#syncVisualTextButton");
const headshotInput = document.querySelector("#headshotInput");
const articleImagesInput = document.querySelector("#articleImagesInput");
const mediaStatus = document.querySelector("#mediaStatus");

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function loadData() {
  try {
    const [packages, templates, brands] = await Promise.all([
      fetchJson("/api/packages"),
      fetchJson("/api/templates"),
      fetchJson("/api/brands"),
    ]);
    state.packages = packages;
    state.templates = templates;
    state.brands = brands;
  } catch (error) {
    statusBox.textContent = "Open with ./run_studio.sh to approve text and create video.";
  }
  renderTemplateOptions();
  renderBrandOptions();
  renderStories();
}

function renderBrandOptions() {
  workspaceBrandSelect.innerHTML = Object.entries(state.brands).map(([id, brand]) => (
    `<option value="${id}">${brand.name}</option>`
  )).join("");
  if (!workspaceBrandSelect.value) {
    workspaceBrandSelect.value = "neuse-news";
  }
  brandSelect.innerHTML = Object.entries(state.brands).map(([id, brand]) => (
    `<option value="${id}">${brand.name}</option>`
  )).join("");
}

function renderTemplateOptions() {
  templateSelect.innerHTML = Object.entries(state.templates).map(([id, template]) => (
    `<option value="${id}">${template.name}</option>`
  )).join("");
}

function renderStories() {
  const brandId = workspaceBrandSelect.value || "neuse-news";
  const filtered = state.packages
    .filter((story) => (story.brand_id || "neuse-news") === brandId)
    .sort((a, b) => storyTime(b) - storyTime(a));
  const brand = state.brands[brandId];
  document.querySelector(".topbar .eyebrow").textContent = brand ? brand.name : "Neuse News";
  if (!filtered.length) {
    storyList.innerHTML = `<div class="empty-list">No stories in this brand workspace yet.</div>`;
    emptyState.classList.remove("hidden");
    storyWorkspace.classList.add("hidden");
    return;
  }
  storyList.innerHTML = filtered.map((story) => `
    <button class="story-button" type="button" data-id="${story.id}">
      <strong>${escapeHtml(story.headline || "Untitled story")}</strong>
      <span>${escapeHtml(story.county || "Local")} | ${escapeHtml(story.format || "News story")}</span>
    </button>
  `).join("");
}

function storyTime(story) {
  const parsed = Date.parse(story.pub_date || "");
  if (!Number.isNaN(parsed)) return parsed;
  const match = String(story.id || "").match(/-(mon|tue|wed|thu|fri|sat|sun)-(\d{2})-([a-z]{3})-(\d{4})/i);
  if (!match) return 0;
  const months = {jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11};
  return new Date(Number(match[4]), months[match[3].toLowerCase()] || 0, Number(match[2])).getTime();
}

function selectStory(id) {
  state.selected = state.packages.find((story) => story.id === id);
  if (!state.selected) return;

  document.querySelectorAll(".story-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.id === id);
  });

  emptyState.classList.add("hidden");
  storyWorkspace.classList.remove("hidden");
  storyMeta.textContent = `${state.selected.county || "Local"} | ${state.selected.status || "idea"}`;
  storyHeadline.textContent = state.selected.headline || "Untitled story";
  sourceLink.href = state.selected.source_url || "#";
  brandSelect.value = state.selected.brand_id || "neuse-news";

  const templateId = templateNameToId[state.selected.format] || "news_story";
  templateSelect.value = templateId;
  scriptEditor.value = (state.selected.approved_script_lines || state.selected.suggested_script_lines || []).join("\n\n");
  const visualLines = state.selected.visual_text_mode === "manual"
    ? (state.selected.approved_visual_lines || [])
    : makeVisualLines(scriptEditor.value);
  renderVisualBeatFields(visualLines, splitBlocks(scriptEditor.value).length);
  state.visualTextDirty = false;
  renderMediaStatus();
  updateTemplateSummary();
  statusBox.textContent = "Review the text, make edits, then approve it.";
  videoPreview.classList.add("hidden");
}

function switchWorkspaceBrand() {
  state.selected = null;
  videoPreview.classList.add("hidden");
  statusBox.textContent = "";
  renderStories();
}

function updateScriptBrandEnding() {
  if (!state.selected) return;
  const brand = state.brands[brandSelect.value];
  if (!brand) return;
  const lines = scriptEditor.value.split(/\n\s*\n/).map((line) => line.trim()).filter(Boolean);
  if (!lines.length) return;
  const lastIndex = lines.length - 1;
  if (/^Read the full .+ at .+\.$/.test(lines[lastIndex])) {
    if ((templateSelect.value || "").includes("meeting")) {
      lines[lastIndex] = `Read the full meeting recap at ${brand.site}.`;
    } else if ((templateSelect.value || "").includes("featured")) {
      lines[lastIndex] = `Read the full feature at ${brand.site}.`;
    } else {
      lines[lastIndex] = `Read the full story at ${brand.site}.`;
    }
    scriptEditor.value = lines.join("\n\n");
  }
}

function splitBlocks(text) {
  return text
    .split(/\n\s*\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function makeVisualLines(text) {
  return splitBlocks(text)
    .map((line) => {
      const withoutCta = line.replace(/^Read the full .+$/i, "").trim();
      if (!withoutCta) return "";
      const sentence = withoutCta.split(/(?<=[.!?])\s+/)[0].trim();
      if (sentence.length <= 120) return sentence;
      const words = sentence.split(/\s+/);
      let result = "";
      for (const word of words) {
        if ((result + " " + word).trim().length > 86) break;
        result = (result + " " + word).trim();
      }
      const weakEndings = new Set(["a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "additional"]);
      const resultWords = result.replace(/[.,;:]$/, "").split(/\s+/).filter(Boolean);
      while (resultWords.length && weakEndings.has(resultWords[resultWords.length - 1].toLowerCase())) {
        resultWords.pop();
      }
      return resultWords.join(" ") || result.replace(/[.,;:]$/, "");
    })
    .filter(Boolean);
}

function getVisualLines() {
  return Array.from(visualBeatFields.querySelectorAll("textarea"))
    .map((field) => field.value.trim());
}

function currentVisualLines() {
  return Array.from(visualBeatFields.querySelectorAll("textarea"))
    .map((field) => field.value);
}

function renderVisualBeatFields(lines, desiredCount) {
  const count = Math.max(desiredCount || 0, lines.length, 1);
  visualBeatFields.innerHTML = Array.from({ length: count }, (_, index) => `
    <label class="visual-beat">
      <span>Screen ${index + 1}</span>
      <textarea data-index="${index}" spellcheck="true">${escapeHtml(lines[index] || "")}</textarea>
    </label>
  `).join("");
  visualBeatFields.querySelectorAll("textarea").forEach((field) => {
    field.addEventListener("input", () => {
      state.visualTextDirty = true;
    });
  });
}

function matchVisualBeatsToVoiceover() {
  const desiredCount = splitBlocks(scriptEditor.value).length;
  if (!state.visualTextDirty) {
    renderVisualBeatFields(makeVisualLines(scriptEditor.value), desiredCount);
    return;
  }
  renderVisualBeatFields(currentVisualLines(), desiredCount);
  state.visualTextDirty = true;
}

function syncVisualTextFromVoiceover() {
  renderVisualBeatFields(makeVisualLines(scriptEditor.value), splitBlocks(scriptEditor.value).length);
  state.visualTextDirty = false;
}

async function draftVoiceoverFromArticle() {
  if (!state.selected) return;
  const template = state.templates[templateSelect.value];
  draftVoiceoverButton.disabled = true;
  statusBox.textContent = "Drafting from the full article...";
  try {
    const result = await fetchJson("/api/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: state.selected.id,
        brand_id: brandSelect.value,
        format: template ? template.name : state.selected.format,
      }),
    });
    scriptEditor.value = (result.script_lines || []).join("\n\n");
    renderVisualBeatFields(result.visual_lines || makeVisualLines(scriptEditor.value), splitBlocks(scriptEditor.value).length);
    state.visualTextDirty = false;
    statusBox.textContent = "Draft refreshed from the article. Review it before approving.";
  } catch (error) {
    statusBox.textContent = "Could not draft from the article. Try importing stories, then try again.";
  } finally {
    draftVoiceoverButton.disabled = false;
  }
}

function updateTemplateSummary() {
  const template = state.templates[templateSelect.value];
  if (!template) {
    templateSummary.textContent = "";
    return;
  }
  templateSummary.innerHTML = `
    <strong>${template.name}</strong><br>
    Target: ${template.target_seconds} seconds<br>
    ${escapeHtml(template.best_for)}
  `;
}

async function approveText() {
  if (!state.selected) return;
  const template = state.templates[templateSelect.value];
  const scriptLines = splitBlocks(scriptEditor.value);
  const visualLines = getVisualLines();
  statusBox.textContent = "Saving approved text...";
  const result = await fetchJson("/api/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: state.selected.id,
      brand_id: brandSelect.value,
      format: template ? template.name : state.selected.format,
      script_lines: scriptLines,
      visual_lines: visualLines,
      visual_text_mode: state.visualTextDirty ? "manual" : "auto",
    }),
  });
  state.selected = result.package;
  renderMediaStatus();
  statusBox.textContent = "Text approved. Ready to create video.";
}

async function uploadImages() {
  if (!state.selected) return;
  const formData = new FormData();
  formData.append("id", state.selected.id);
  if (headshotInput.files[0]) {
    formData.append("headshot", headshotInput.files[0]);
  }
  Array.from(articleImagesInput.files).slice(0, 3).forEach((file) => {
    formData.append("article_images", file);
  });
  mediaStatus.textContent = "Saving images...";
  const result = await fetchJson("/api/upload-images", {
    method: "POST",
    body: formData,
  });
  state.selected = result.package;
  headshotInput.value = "";
  articleImagesInput.value = "";
  renderMediaStatus();
}

function renderMediaStatus() {
  if (!state.selected) return;
  const articleCount = (state.selected.article_image_paths || []).length;
  const hasHeadshot = Boolean(state.selected.headshot_image_path);
  mediaStatus.textContent = `${hasHeadshot ? "Headshot saved" : "No headshot"} | ${articleCount} article image${articleCount === 1 ? "" : "s"} saved`;
}

async function renderVideo() {
  if (!state.selected) return;
  renderButton.disabled = true;
  approveButton.disabled = true;
  try {
    await approveText();
    statusBox.textContent = "Creating video. This can take a minute...";
    videoPreview.classList.add("hidden");
    const result = await fetchJson("/api/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: state.selected.id }),
    });
    statusBox.innerHTML = `Video created: <a href="${result.video_url}" target="_blank" rel="noreferrer">open video</a>`;
    videoPreview.src = result.video_url;
    videoPreview.classList.remove("hidden");
  } catch (error) {
    statusBox.textContent = "Video did not finish. Refresh the page and try Create video again.";
  } finally {
    renderButton.disabled = false;
    approveButton.disabled = false;
  }
}

async function importAllBrands() {
  statusBox.textContent = "Importing stories from all brand feeds...";
  await fetchJson("/api/import-all", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit: 5 }),
  });
  await loadData();
  statusBox.textContent = "Stories imported. Switch brands from the top menu.";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

storyList.addEventListener("click", (event) => {
  const button = event.target.closest(".story-button");
  if (button) selectStory(button.dataset.id);
});

templateSelect.addEventListener("change", updateTemplateSummary);
brandSelect.addEventListener("change", updateScriptBrandEnding);
scriptEditor.addEventListener("input", () => {
  matchVisualBeatsToVoiceover();
});
syncVisualTextButton.addEventListener("click", syncVisualTextFromVoiceover);
draftVoiceoverButton.addEventListener("click", draftVoiceoverFromArticle);
workspaceBrandSelect.addEventListener("change", switchWorkspaceBrand);
document.querySelector("#refreshButton").addEventListener("click", loadData);
document.querySelector("#importButton").addEventListener("click", importAllBrands);
approveButton.addEventListener("click", approveText);
renderButton.addEventListener("click", renderVideo);
uploadImagesButton.addEventListener("click", uploadImages);

loadData();
"""
