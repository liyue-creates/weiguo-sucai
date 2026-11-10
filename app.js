const FILTER_CHIPS = [
  "小而美作品",
  "细分人群",
  "大佬观点·爆款型",
  "好玩产品",
  "求职测评可用",
  "二次元",
  "应季",
  "GitHub对你自己有用",
  "国外火国内未火",
];
const STAGE_CHIPS = ["萌芽", "爆发", "衰退", "常青", "扩散"];

const state = {
  data: null,
  category: "全部",
  stage: "全部",
  batch: "全部",
  query: "",
  showPass: false,
};

const $ = (id) => document.getElementById(id);

function matchesChip(item, chip) {
  if (chip === "全部") return true;
  return (item.filter_tags || []).includes(chip) || item.category === chip || (item.tags || []).includes(chip);
}

function stageOf(item) {
  return item.stage_norm || (STAGE_CHIPS.find((s) => (item.stage || "").includes(s)) || "");
}

function visibleItems() {
  if (!state.data) return [];
  const q = state.query.trim().toLowerCase();
  return state.data.items.filter((item) => {
    if (!state.showPass && (item.hidden || item.rating === "pass")) return false;
    if (state.category !== "全部" && !matchesChip(item, state.category)) return false;
    if (state.stage !== "全部" && stageOf(item) !== state.stage) return false;
    if (state.batch !== "全部" && String(item.batch) !== String(state.batch)) return false;
    if (!q) return true;
    const blob = [
      item.id, item.title, item.viewer_moment, item.why_popular, item.idea,
      item.data, item.category, ...(item.tags || []), ...(item.filter_tags || []),
      ...(item.links || []).map((l) => `${l.url} ${l.label}`),
    ].join(" ").toLowerCase();
    return blob.includes(q);
  });
}

function chipRow(el, list, current, onPick, extra = ["全部"]) {
  el.innerHTML = "";
  extra.concat(list).forEach((name) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = name;
    btn.setAttribute("aria-pressed", name === current ? "true" : "false");
    btn.addEventListener("click", () => onPick(name));
    el.appendChild(btn);
  });
}

function renderControls() {
  const present = FILTER_CHIPS.filter((c) => state.data.items.some((it) => matchesChip(it, c)));
  chipRow($("catChips"), present, state.category, (name) => {
    state.category = name;
    render();
  });
  chipRow($("stageChips"), STAGE_CHIPS, state.stage, (name) => {
    state.stage = name;
    render();
  });

  const batches = [...new Set(state.data.items.map((it) => it.batch).filter(Boolean))].sort((a, b) => b - a);
  const select = $("batchSelect");
  const prev = state.batch;
  select.innerHTML = `<option value="全部">全部批次</option>` + batches.map((b) => {
    const date = (state.data.items.find((it) => it.batch === b) || {}).date || "";
    return `<option value="${b}">第 ${b} 批${date ? " · " + date : ""}</option>`;
  }).join("");
  select.value = prev;
}

function cardHTML(item) {
  const stage = stageOf(item);
  const viewer = item.viewer_moment ? `<p class="viewer">「${escapeHtml(trimText(item.viewer_moment, 90))}」</p>` : "";
  const data = item.data ? `<p class="data">${escapeHtml(trimText(item.data, 88))}</p>` : "";
  const tags = (item.tags || []).slice(0, 3).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("");
  const rating = (item.rating && !["待反馈", "pass"].includes(item.rating))
    ? `<span class="pill rating">${escapeHtml(item.rating)}</span>` : "";
  const unpushed = item.pushed === false ? `<span class="pill warn">备选未推</span>` : "";
  const date = item.date ? item.date.slice(5) : "";
  return `
    <article class="card" tabindex="0" data-id="${item.id}" role="button" aria-label="${escapeHtml(item.id + " " + item.title)}">
      <div class="card-top">
        <span class="pid">${item.id}</span>
        ${stage ? `<span class="pill stage-${stage}">${escapeHtml(item.stage || stage)}</span>` : ""}
        ${rating}${unpushed}
      </div>
      <h2>${escapeHtml(item.title)}</h2>
      ${viewer}
      ${data}
      <div class="meta">
        <span class="cat">${escapeHtml(item.category || "")}</span>
        <span>${item.batch ? "第 " + item.batch + " 批" : ""}${date ? " · " + date : ""}</span>
      </div>
      ${tags ? `<div class="tags">${tags}</div>` : ""}
    </article>`;
}

function renderFeed() {
  const items = visibleItems();
  $("feed").innerHTML = items.map(cardHTML).join("");
  $("empty").hidden = items.length > 0;
  $("count").textContent = `共 ${items.length} 条`;
  $("feed").querySelectorAll(".card").forEach((card) => {
    const open = () => openDetail(card.dataset.id);
    card.addEventListener("click", open);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
    });
  });
}

function field(title, body) {
  if (!body) return "";
  return `<div class="field"><h3>${title}</h3><p>${escapeHtml(body)}</p></div>`;
}

function openDetail(id) {
  const item = state.data.items.find((it) => it.id === id);
  if (!item) return;
  $("d-kicker").textContent = `${item.id}  ·  第 ${item.batch || "?"} 批  ·  ${item.date || "日期未知"}`;
  $("d-title").textContent = item.title;
  const pills = [
    item.category,
    item.stage,
    item.difficulty ? "难度 " + item.difficulty : "",
    item.rating && item.rating !== "待反馈" ? "评价 " + item.rating : "",
    ...(item.tags || []),
  ].filter(Boolean);
  $("d-pills").innerHTML = pills.map((p) => `<span class="pill">${escapeHtml(p)}</span>`).join("");
  const viewer = item.viewer_moment;
  $("d-viewer").hidden = !viewer;
  $("d-viewer").textContent = viewer ? `「${viewer}」` : "";
  $("d-fields").innerHTML = [
    field("数据", item.data),
    field("为什么火", item.why_popular),
    field("可以做什么", item.idea),
    item.pushed === false ? field("备注", "当时找到，但没有放进当天的推送。") : "",
  ].join("");
  $("d-links").innerHTML = (item.links || []).map((lk) =>
    `<a class="link-btn" href="${encodeURI(lk.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(lk.label)} ↗</a>`
  ).join("") || `<p class="data">这条没有记录到可点开的原始链接。</p>`;
  $("overlay").hidden = false;
  document.body.style.overflow = "hidden";
  history.replaceState(null, "", "#" + id);
  $("closeBtn").focus();
}

function closeDetail() {
  $("overlay").hidden = true;
  document.body.style.overflow = "";
  if (location.hash) history.replaceState(null, "", location.pathname + location.search);
}

function escapeHtml(str) {
  return String(str || "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function trimText(str, n) {
  const s = String(str || "").replace(/\s+/g, " ").trim();
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function render() {
  renderControls();
  renderFeed();
}

async function init() {
  const res = await fetch("./data/materials.json", { cache: "no-store" });
  state.data = await res.json();
  $("updated").textContent = `最近生成：${state.data.generated_at}（Asia/Seoul） · ${state.data.item_count} 条素材`;
  $("search").addEventListener("input", (e) => {
    state.query = e.target.value;
    renderFeed();
    renderControls();
    $("count").textContent = `共 ${visibleItems().length} 条`;
  });
  $("batchSelect").addEventListener("change", (e) => {
    state.batch = e.target.value;
    render();
  });
  $("showPass").addEventListener("change", (e) => {
    state.showPass = e.target.checked;
    render();
  });
  $("closeBtn").addEventListener("click", closeDetail);
  $("overlay").addEventListener("click", (e) => {
    if (e.target.id === "overlay") closeDetail();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("overlay").hidden) closeDetail();
  });
  render();
  const hash = decodeURIComponent(location.hash.replace("#", ""));
  if (hash) openDetail(hash);
}

init().catch((err) => {
  $("empty").hidden = false;
  $("empty").textContent = "素材数据加载失败：" + err.message;
});
