# 每日灵感

一套可以像刷信息流一样翻的公开素材库，也方便其他 AI 直接读取。

- 浏览页：`index.html`
- 结构化数据：`data/materials.json`
- 全文：`materials.md`
- 给 AI 的入口：`llms.txt`

页面是纯静态的，不用打包。用本地文件打开时，部分浏览器会拦住 `fetch`，请用任意静态服务器，或看 GitHub Pages 上的地址。

## 每天怎么更新

素材原文仍写在上一级目录（`/workspace/mirror/`）里：

1. 把当天的条目追加进 `素材池_总整理.md`（沿用现有的 `Sxxx 标题｜链接｜数据｜分类｜…` 格式，或写成 `每日素材_YYYY-MM-DD.md` 那种分条字段）。
2. 同时保存一份 `每日素材_YYYY-MM-DD.md`。
3. 如果有新的评价，改 `site/data/ratings.json`，例如 `{ "S134": "值得做" }`。评价写成 `pass` 的条目会在页面里默认隐藏。
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

每条素材大致包含：`id`、`batch`、`date`、`title`、`category`、`filter_tags`、`links`、`data`、`why_popular`、`viewer_moment`、`stage`、`idea`、`difficulty`、`tags`、`rating`、`hidden`、`pushed`。

没有核实过的链接会如实留空，不会补造。风向标等二手数据会保留原文里的“自述 / 未核验”提示。
