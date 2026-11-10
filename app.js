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
const MARKS_KEY = "weiguo-sucai-marks";

const state = {
  data: null,
  category: "全部",
  stage: "全部",
  batch: "全部",
  collection: "全部",
  query: "",
  showPass: false,
  localMarks: { v: 1, marks: {} },
  openId: null,
};

const $ = (id) => document.getElementById(id);

function loadLocalMarks() {
  try {
    const raw = localStorage.getItem(MARKS_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    state.localMarks = normalizeExport(parsed) || { v: 1, marks: {} };
  } catch (err) {
    state.localMarks = { v: 1, marks: {} };
  }
}

function saveLocalMarks() {
  localStorage.setItem(MARKS_KEY, JSON.stringify(state.localMarks));
}

function normalizeExport(data) {
  if (!data || typeof data !== "object") return null;
  const marks = {};
  if (data.marks && typeof data.marks === "object") {
    Object.entries(data.marks).forEach(([id, val]) => {
      if (!id) return;
      const entry = {};
      if (val && typeof val === "object") {
        if (Object.prototype.hasOwnProperty.call(val, "favorite")) entry.favorite = !!val.favorite;
        if (Object.prototype.hasOwnProperty.call(val, "doing")) entry.doing = !!val.doing;
      }
      if (Object.keys(entry).length) marks[id] = entry;
    });
  }
  const applyList = (list, key, flagged) => {
    if (!Array.isArray(list)) return;
    list.forEach((id) => {
      if (!id) return;
      marks[id] = marks[id] || {};
      marks[id][key] = flagged;
    });
  };
  applyList(data.fav, "favorite", true);
  applyList(data.doing, "doing", true);
  applyList(data.unfav, "favorite", false);
  applyList(data.undoing, "doing", false);
  return { v: 1, marks };
}

function mergeImported(incoming) {
  const next = normalizeExport(incoming);
  if (!next) throw new Error("格式不对");
  Object.entries(next.marks).forEach(([id, entry]) => {
    state.localMarks.marks[id] = { ...(state.localMarks.marks[id] || {}), ...entry };
  });
  saveLocalMarks();
}

function isMarked(item, key) {
  const local = state.localMarks.marks[item.id];
  if (local && Object.prototype.hasOwnProperty.call(local, key)) return !!local[key];
  return !!item[key];
}

function toggleMark(id, key) {
  const item = state.data.items.find((it) => it.id === id);
  if (!item) return;
  const next = !isMarked(item, key);
  state.localMarks.marks[id] = { ...(state.localMarks.marks[id] || {}), [key]: next };
  saveLocalMarks();
  render();
  if (state.openId === id) fillDetail(item);
}

function markedItems(key) {
  if (!state.data) return [];
  return state.data.items.filter((item) => {
    if (!state.showPass && (item.hidden || item.rating === "pass")) return false;
    return isMarked(item, key);
  });
}

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
    if (state.collection === "favorite" && !isMarked(item, "favorite")) return false;
    if (state.collection === "doing" && !isMarked(item, "doing")) return false;
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

function chipRow(el, list, current, onPick) {
  el.innerHTML = "";
  list.forEach((item) => {
    const name = typeof item === "string" ? item : item.name;
    const label = typeof item === "string" ? item : item.label;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = label;
    btn.setAttribute("aria-pressed", name === current ? "true" : "false");
    btn.addEventListener("click", () => onPick(name));
    el.appendChild(btn);
  });
}

function renderControls() {
  const favN = markedItems("favorite").length;
  const doingN = markedItems("doing").length;
  chipRow($("markChips"), [
    { name: "全部", label: "全部" },
    { name: "favorite", label: `⭐ 我的收藏 (${favN})` },
    { name: "doing", label: `🛠 在做 (${doingN})` },
  ], state.collection, (name) => {
    state.collection = name;
    render();
  });

  const present = FILTER_CHIPS.filter((c) => state.data.items.some((it) => matchesChip(it, c)));
  chipRow($("catChips"), ["全部"].concat(present), state.category, (name) => {
    state.category = name;
    render();
  });
  chipRow($("stageChips"), ["全部"].concat(STAGE_CHIPS), state.stage, (name) => {
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

function markButtons(item) {
  const fav = isMarked(item, "favorite");
  const doing = isMarked(item, "doing");
  return `
    <div class="mark-row">
      <button type="button" class="mark-btn" data-mark="favorite" data-id="${item.id}" aria-pressed="${fav ? "true" : "false"}">⭐ 收藏</button>
      <button type="button" class="mark-btn" data-mark="doing" data-id="${item.id}" aria-pressed="${doing ? "true" : "false"}">🛠 在做</button>
    </div>`;
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
      ${markButtons(item)}
    </article>`;
}

function renderFeed() {
  const items = visibleItems();
  $("feed").innerHTML = items.map(cardHTML).join("");
  $("empty").hidden = items.length > 0;
  if (!items.length) {
    $("empty").textContent = state.collection === "favorite"
      ? "还没有收藏。点卡片上的 ⭐ 收藏就能加进来。"
      : state.collection === "doing"
        ? "还没有标记「在做」的条目。开始做的时候点一下 🛠 在做。"
        : "没有符合筛选的卡片。换个分类，或清空搜索再试试。";
  }
  $("count").textContent = `共 ${items.length} 条`;
  $("feed").querySelectorAll(".card").forEach((card) => {
    const open = () => openDetail(card.dataset.id);
    card.addEventListener("click", (e) => {
      if (e.target.closest(".mark-btn")) return;
      open();
    });
    card.addEventListener("keydown", (e) => {
      if (e.target.closest(".mark-btn")) return;
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
    });
    card.querySelectorAll(".mark-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleMark(btn.dataset.id, btn.dataset.mark);
      });
    });
  });
}

function field(title, body) {
  if (!body) return "";
  return `<div class="field"><h3>${title}</h3><p>${escapeHtml(body)}</p></div>`;
}

function fillDetail(item) {
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
  $("d-marks").innerHTML = markButtons(item);
  $("d-marks").querySelectorAll(".mark-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      toggleMark(btn.dataset.id, btn.dataset.mark);
    });
  });
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
}

function openDetail(id) {
  const item = state.data.items.find((it) => it.id === id);
  if (!item) return;
  state.openId = id;
  fillDetail(item);
  $("overlay").hidden = false;
  document.body.style.overflow = "hidden";
  history.replaceState(null, "", "#" + id);
  $("closeBtn").focus();
}

function closeDetail() {
  state.openId = null;
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

function showToast(message) {
  const el = $("toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { el.hidden = true; }, 2200);
}

function exportMarks() {
  const payload = JSON.stringify(state.localMarks);
  const done = () => showToast("已复制收藏代码，到另一台设备点「导入」贴上就行");
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(payload).then(done).catch(() => fallbackCopy(payload, done));
  } else {
    fallbackCopy(payload, done);
  }
}

function fallbackCopy(text, done) {
  $("importBox").value = text;
  $("syncPanel").hidden = false;
  $("importBox").focus();
  $("importBox").select();
  try {
    document.execCommand("copy");
    done();
  } catch (err) {
    showToast("复制失败，请手动选中代码再复制");
  }
}

function importMarks() {
  const raw = $("importBox").value.trim();
  if (!raw) {
    showToast("先贴上导出的代码");
    return;
  }
  try {
    mergeImported(JSON.parse(raw));
    $("syncPanel").hidden = true;
    $("importBox").value = "";
    render();
    if (state.openId) {
      const item = state.data.items.find((it) => it.id === state.openId);
      if (item) fillDetail(item);
    }
    showToast("已导入并与这台设备上的标记合并");
  } catch (err) {
    showToast("导入失败：请检查代码是不是完整的 JSON");
  }
}

function render() {
  renderControls();
  renderFeed();
}

async function init() {
  loadLocalMarks();
  const res = await fetch("./data/materials.json", { cache: "no-store" });
  state.data = await res.json();
  $("updated").textContent = `最近生成：${state.data.generated_at}（Asia/Seoul） · ${state.data.item_count} 条素材`;
  $("search").addEventListener("input", (e) => {
    state.query = e.target.value;
    renderFeed();
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
  $("exportBtn").addEventListener("click", exportMarks);
  $("importOpenBtn").addEventListener("click", () => {
    $("syncPanel").hidden = false;
    $("importBox").focus();
  });
  $("importBtn").addEventListener("click", importMarks);
  $("cancelImport").addEventListener("click", () => {
    $("syncPanel").hidden = true;
  });
  render();
  const hash = decodeURIComponent(location.hash.replace("#", ""));
  if (hash) openDetail(hash);
}

init().catch((err) => {
  $("empty").hidden = false;
  $("empty").textContent = "素材数据加载失败：" + err.message;
});
