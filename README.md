# 🚄 抢票日历 · 哪天几点开售

> 按出行日倒推 12306 哪天、几点开售（各站起售时间不同），节假日和春运抢票日历，一键加入手机日历提醒

**🌐 在线访问：[https://climb0516.github.io/ticket-calendar/](https://climb0516.github.io/ticket-calendar/)**

---

## 功能

- **今天开售什么**：「今天开售的是 X 月 X 日的车票」，以及你出发站的起售时间；右侧是下一个春运（预计）的日期和首日车票开售倒计时
- **倒推计算器**：选出发日期 + 出发站（支持站名 / 全拼 / 首字母搜索，例如 `hzd`），算出「X 月 X 日 HH:MM 开售」和状态（N 天后 / 明天 / 今天 / 已开售）；**一键下载 .ics 日历提醒**，开售前 10 分钟提醒；最近用过的出发站记在本机
- **节假日抢票日历**：读取[拼假攻略](https://climb0516.github.io/holiday-planner/)的节假日数据，每个假期列出去程高峰（前一天、第一天）和返程高峰（最后一天）的车票开售日期，每格可单独加提醒；春运按「正月初一前 15 天到后 24 天」推算，标「预计」
- **各站起售时间**：2011 个车站，默认显示 16 个大站，可搜索；点击即设为出发站
- **候补购票与抢票技巧**：候补订单数量、日期、车次限制等官方规则
- **相关动态**：预售期调整、春运购票、春运机票新闻
- 深色 / 浅色主题，手机适配

## 规则

| 规则 | 说明 | 来源 |
|---|---|---|
| 预售期 | 15 天（含当天），即出发日 − 14 天开售 | [12306 官方说明](https://kyfw.12306.cn/otn/gonggao/gsggp.html) |
| 起售时间 | 按出发站，08:00–18:00 不等 | 12306 官方起售时间表 `qss.js` |
| 春运 | 正月初一前 15 天至后 24 天，共 40 天（推算） | 往年惯例，正式日程以官方公布为准 |
| 机票 | 没有统一开售规则，不做推算 | 以各航司公告为准 |

节假日、春运期间如有预售期调整，以 12306 官方公告为准。

---

## 技术架构

```
GitHub Actions（定时：每天北京时间 08:20 / 手动 dispatch / push 修改 scraper.py 或 workflow）
  ↓ python scraper.py（Python 3.12，只用标准库）
  ↓ stations()：12306 qss.js 起售时间 + station_name.js 车站名 → stations
  ↓ holidays()：拼假攻略 data.json → 合并连续假日、并入相连周末 → holidays
  ↓ news()：Google News RSS × 3 个关键词 → 去重取前 40 条 → news
  ↓ 写入 data.json（updated 每次都变 = 心跳），git commit + push
       ↓
GitHub Pages（index.html）
  ↓ fetch('data.json', no-cache) 读取数据
  ↓ 开售日推算（出发日 − 14 天）、春运推算、.ics 生成全部在前端完成
  ↓ kit 详情抽屉 #/item/<类型>/<id> + 列表页 #/list/<key>
```

---

## 数据来源

| 来源 | 方式 | 每次条数 / 范围 | 备注 |
|---|---|---|---|
| [12306 起售时间表 qss.js](https://kyfw.12306.cn/otn/resources/js/query/qss.js) | 接口（JS 文件，正则解析 `"站名":"HH:MM"`） | 全量车站（当前 2011 个） | 少于 500 条视为异常并抛错 |
| [12306 车站名 station_name.js](https://kyfw.12306.cn/otn/resources/js/framework/station_name.js) | 接口（JS 文件，按 `@` / `\|` 切分） | 全量 | 取第 2/4/5/8 段：站名、全拼、首字母、所属城市（城市为空时用站名） |
| [拼假攻略 data.json](https://climb0516.github.io/holiday-planner/data.json) | 接口（JSON） | `cn` 下所有年份（当前 20 个假期） | 依赖字段 `cn[年].days[].{date,name,off}`、`announce`、`summary.plan_year`、`summary.plan_official` |
| Google News RSS | RSS | 3 个关键词合并去重后最多 40 条 | `hl=zh-CN&gl=CN`，关键词见下 |

Google News 关键词（`news()` 内的元组，格式：查询语句, topic）：

| 查询 | topic |
|---|---|
| `12306 预售期 when:60d` | 规则 |
| `火车票 开售 春运 OR 国庆 OR 元旦 when:30d` | 火车票 |
| `春运 机票 开售 OR 预订 when:60d` | 机票 |

**新增 / 删除来源**：
- 新闻关键词：编辑 `scraper.py` 的 `news()` 里的 `(查询, topic)` 元组；新增 topic 时同步改 `index.html` 的 `TOPICS` 数组和 `TOPIC_ICON` 映射
- 整个数据源：在 `main()` 的 `data` 字典里加一行 `run("显示名", 函数, "字段名")`，`run()` 会自动记录到 `sources`，失败时沿用上次 data.json 中该字段的旧值
- 请求统一走 `fetch()`，带浏览器 UA 和 `Referer: https://kyfw.12306.cn/`，超时 20 秒

---

## 数据处理规则

**车站（`stations()`）**
- `qss.js` 正则 `"([^"]+)"\s*:\s*"(\d{2}:\d{2})"` 抽出「站名 → 起售时间」，不足 500 条直接报错（防止接口改版写入空数据）
- 与 `station_name.js` 按站名关联，精简为数组 `[站名, 起售时间, 全拼, 首字母, 城市]` 以减小体积；按全拼排序（无全拼按站名）

**节假日（`holidays()`）**
- 只取 `off: true` 的放假日，按日期排序；**同名且日期相差 1 天**的连成一个假期
- `est`（预计）= 年份等于 `summary.plan_year` 且 `plan_official` 为 false 且该年不在 `announce` 中
- 拼假数据只列法定放假日，`weekend_off()` 把假期前后**相连的周六/周日**并入（被调休成上班日 `off: false` 的周末除外）。例：国庆 10-01 ~ 10-07 若 09-30 前是周末且未调休，则 start 前移
- 一个假期都没有时抛错

**新闻（`news()`）**
- 去掉标题末尾的「 - 来源名」，HTML 反转义；`pubDate` 解析失败的条目丢弃，时间转为 UTC ISO
- 按时间倒序，标题去掉非文字字符后取**前 18 个字符**作为去重键，保留最新一条，最多 **40** 条

**容错（`main()` 里的 `run()`）**
- 每个来源独立 try/except；失败时 `sources` 记 `ok: false` 和前 120 字符的 `error`，`updated` 保留上次成功时间，数据沿用旧 data.json 中对应字段

**前端推算（`index.html`）**
- 预售期 `PRESALE = 15`（含当天），开售日 = 出发日 − `OFFSET`（14）天；全部按北京时间（UTC+8）计算
- 开售状态 `status()`：已开售 / 今天 HH:MM 开售（过了起售时间则「今天已开售」）/ 明天 / ≤7 天为「N 天后」（高亮）/ 更远为「N 天后」
- 春运 `springRush()`：按 `LUNAR_NY` 中写死的正月初一（2027-02-06、2028-01-26、2029-02-13），取「初一前 15 天 ~ 后 24 天」，返回第一个尚未结束的春运；更新年份需手动维护该表
- 节假日详情列出的出行日：普通假期为开始前两天到最后一天；春运只列关键 8 天（首日、除夕前三天、前两天、除夕、初六、初七、初八、末日）
- 车站搜索 `matchStations()` 打分：站名全等 0 > 站名前缀 1 > 首字母前缀 2 > 全拼前缀 3 > 城市前缀 4 > 站名包含 5 > 城市包含 6，同分按站名长度；下拉最多 8 条

---

## 数据结构

`data.json`（单文件，紧凑 JSON，无缩进）：

```
{
  "updated": "2026-10-22T12:51:40+08:00",   // 北京时间，每次运行都变 = 心跳
  "rule": { "presale_days": 15, "note": "预售期 15 天（含当天），即出发日前 14 天开售；起售时间以出发站为准" },
  "stations": [ ["杭州东", "11:30", "hangzhoudong", "hzd", "杭州"], ... ],   // [站名, 起售时间, 全拼, 首字母, 城市]
  "holidays": [ ... ],
  "news": [ ... ],
  "sources": [ ... ]
}
```

单条结构：

```
holidays[i]
{ "name": "春节", "start": "2025-01-28", "end": "2025-02-04", "year": 2025, "est": false }

news[i]
{ "title": "...", "url": "https://news.google.com/rss/articles/...", "source": "新浪网",
  "time": "2026-10-21T02:56:00+00:00", "topic": "规则|火车票|机票" }

sources[i]
{ "name": "12306 起售时间", "ok": true, "count": 2011, "updated": "..." }
{ "name": "Google News", "ok": false, "error": "前 120 字符", "updated": "上次成功时间" }
```

本项目没有其他 json、快照或图片目录；春运不在 data.json 中，由前端按 `LUNAR_NY` 推算。浏览器本地存储（`localStorage`，前缀 `tk:`）：`station` 当前出发站、`recent` 最近 4 个出发站、`theme` 主题。

---

## 前端

**详情抽屉 + 列表页（通用组件 kit）**：电脑端右侧滑出，手机端从底部升起；打开详情会写进地址栏，分享链接可直接打开对应条目，浏览器返回即关闭。条目已不在当前数据里（已下榜 / 过期 / 旧链接）时弹出提示「这条内容已不在当前数据里」。

| 条目类型 | 地址 | id 规则 | 内容 |
|---|---|---|---|
| station | `#/item/station/<站名>` | 站名 | 起售时间、所属城市、同城其他车站 |
| holiday | `#/item/holiday/<年份>-<名称>` | `holId()`，如 `2026-国庆节`；春运为 `2027-春运` | 每个出行日的开售日期和状态，每天可单独加提醒 |
| news | `#/item/news/<序号>` | 在 `news` 数组中的下标 | 来源、时间、同 topic 相关新闻 |

| 列表 key | 地址 | 筛选参数 |
|---|---|---|
| holidays | `#/list/holidays` | `f=up`（未结束）/ `f=past`（已过） |
| stations | `#/list/stations` | `time=HH:MM` 起售时段、`city=` 城市、`q=` 搜索、`sort=py\|time`；每页 30 个（`LPAGE`），加载更多 |
| news | `#/list/news` | `topic=规则\|火车票\|机票` |

**项目特有功能**：
- 倒推计算器：选出发日期 + 出发站，算出开售日期、时间与状态
- `.ics` 日历提醒：`ics()` 生成 30 分钟日程，`VALARM TRIGGER:-PT10M` 即开售前 10 分钟提醒；无起售时间时默认 08:00；文件名 `抢票提醒-<开售日>.ics`
- 起售时段分布条：按起售时间统计车站数，点击跳 `#/list/stations?time=`
- 首页默认显示 16 个大站（`HOT`），快捷按钮为当前站 + 最近用过的站 + 北京南 / 上海虹桥（最多 5 个）
- 深色 / 浅色主题切换并记住选择

---

## 本地运行

```
python3 scraper.py              # 只用标准库，无需 pip install，无需环境变量
python3 -m http.server 8794
# 打开 http://localhost:8794
```

- 依赖：Python 3（Actions 使用 3.12），需能访问 12306、climb0516.github.io、news.google.com
- 不需要任何密钥 / 环境变量
- 运行后终端会打印车站数、假期列表和失败的来源

---

## 自动更新机制

| 触发方式 | 时机 |
|---|---|
| GitHub Actions 定时任务 | 每天 08:20 北京时间（cron `20 0 * * *` UTC；各站最早 08:00 起售，每天更新一次即可） |
| push 到 main 分支 | 仅当修改了 `scraper.py` 或 `.github/workflows/scrape.yml` 时 |
| GitHub Actions 手动 dispatch | 按需触发 |

- 工作流：`.github/workflows/scrape.yml`，`concurrency: scrape`（不取消进行中的任务），提交者为 `github-actions[bot]`，提交信息 `data: update YYYY-MM-DD HH:MM`（北京时间），提交前 `git pull --rebase`
- **心跳**：`data.json` 的 `updated` 字段每次运行都变，所以每次都会产生提交，保持仓库活跃。GitHub 会在仓库 **60 天无提交**时自动停用定时任务，若被停用需到 Actions 页面重新启用
- 前端以 `cache: 'no-cache'` 读取 data.json，Pages 部署完成后刷新即可看到新数据
