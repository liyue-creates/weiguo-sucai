# 每日灵感

一套可以像刷信息流一样翻的公开素材库，也方便其他 AI 直接读取。

- 网站：https://liyue-creates.github.io/weiguo-sucai/
- JSON：https://liyue-creates.github.io/weiguo-sucai/data/materials.json
- 给 AI：https://liyue-creates.github.io/weiguo-sucai/llms.txt
- 全文：https://liyue-creates.github.io/weiguo-sucai/materials.md
- 仓库：https://github.com/liyue-creates/weiguo-sucai

- 浏览页：`index.html`
- 结构化数据：`data/materials.json`
- 全文：`materials.md`
- 给 AI 的入口：`llms.txt`

页面是纯静态的，不用打包。用本地文件打开时，部分浏览器会拦住 `fetch`，请用任意静态服务器，或看 GitHub Pages 上的地址。

## 每天怎么更新

素材原文仍写在上一级目录（`/workspace/mirror/`）里：

1. 把当天的条目追加进 `素材池_总整理.md`（沿用现有的 `Sxxx 标题｜链接｜数据｜分类｜…` 格式，或写成 `每日素材_YYYY-MM-DD.md` 那种分条字段）。
2. 同时保存一份 `每日素材_YYYY-MM-DD.md`。
3. 如果有新的评价或要记下「收藏 / 在做」，改 `site/data/ratings.json`（格式见下面）。评价写成 `pass` 的条目会在页面里默认隐藏。
4. 重新生成站点数据：

```bash
cd /workspace/mirror/site
python3 generate.py
```

也可以指定原文目录：

```bash
SUCAI_SOURCE=/workspace/mirror python3 /workspace/mirror/site/generate.py
```

5. 把生成结果推到 GitHub，Pages 会自动更新：

```bash
cd /workspace/mirror/site
git add data/materials.json materials.md llms.txt
git add -u
git commit -m "Update materials for YYYY-MM-DD"
git push origin main
```

`generate.py` 会重建 `data/materials.json`、`materials.md` 和 `llms.txt`，并去掉不宜公开的个人细节（合作商单、私人路径、内部助手名称等）。

## 数据字段

每条素材大致包含：`id`、`batch`、`date`、`title`、`category`、`filter_tags`、`links`、`data`、`why_popular`、`viewer_moment`、`stage`、`idea`、`difficulty`、`tags`、`rating`、`hidden`、`pushed`、`favorite`、`doing`。

没有核实过的链接会如实留空，不会补造。风向标等二手数据会保留原文里的“自述 / 未核验”提示。

## 收藏和「在做」

页面上每张卡（和详情里）有两个独立按钮：`⭐ 收藏`、`🛠 在做`。这两个标记存在浏览器的 `localStorage` 里（键名 `weiguo-sucai-marks`），换浏览器或换设备不会自动带过去。

顶部筛选「全部 / ⭐ 我的收藏 / 🛠 在做」可以和分类、阶段、批次、搜索一起用。`值得做` 只是评价徽章，**不会**自动标成「在做」。

### 在设备之间同步

点「导出收藏」会复制一段 JSON。到另一台设备点「导入收藏」贴上即可。导入会与当前设备已有的本地标记合并，同一条以导入的为准。

导出格式：

```json
{"v":1,"marks":{"S122":{"favorite":true},"S126":{"favorite":true,"doing":true}}}
```

`favorite` / `doing` 为 `false` 表示在这台设备上明确取消过（也会覆盖服务端标记）。

### 写进数据文件，让其他 AI 也能读到

如果她在对话里说某条要收藏或已经开始做，把标记写进 `data/ratings.json`，再运行 `python3 generate.py`。`materials.json` 和 `materials.md` 会带上 `favorite` / `doing`，其他 AI 就能读到。

`ratings.json` 兼容两种写法：

```json
{
  "S047": "值得做",
  "S064": {
    "rating": "值得做"
  },
  "S122": {
    "favorite": true,
    "doing": false
  },
  "S126": {
    "rating": "待反馈",
    "favorite": true,
    "doing": true
  }
}
```

- 只写字符串时，只更新评价，不会改收藏/在做。
- 对象里的 `rating`、`favorite`、`doing` 都是可选的。
- 页面上的本地勾选会覆盖这些服务端字段；取消勾选只改本地，不会写回 `ratings.json`。
