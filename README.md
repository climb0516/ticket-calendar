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

## 数据来源

| 来源 | 内容 |
|---|---|
| [12306 起售时间表](https://kyfw.12306.cn/otn/resources/js/query/qss.js) | 各车站起售时间 |
| [12306 车站名](https://kyfw.12306.cn/otn/resources/js/framework/station_name.js) | 车站拼音、首字母、所属城市（用于搜索） |
| [拼假攻略 data.json](https://climb0516.github.io/holiday-planner/data.json) | 节假日；依赖字段 `cn[年].days[].{date,name,off}`、`announce`、`summary.plan_year`、`summary.plan_official`。爬虫会把相连的周末并入假期（调休上班日除外） |
| Google News RSS | 预售期调整、春运火车票、春运机票 |

---

## 技术架构

```
GitHub Actions（每天北京时间 08:20 / 手动 / 修改爬虫后 push）
  ↓ python scraper.py（只用标准库）
  ↓ 12306 起售时间表 + 车站名 → stations；拼假攻略 → holidays；新闻
  ↓ 写入 data.json 并 commit（updated 每次都变 = 心跳，防止定时任务 60 天不活跃被停用）
       ↓
GitHub Pages（index.html）
  ↓ 开售日期推算、春运推算、.ics 生成全部在前端完成
```

### data.json 结构

```
{
  "updated": "...",
  "rule": { "presale_days": 15, "note": "..." },
  "stations": [ ["杭州东", "11:30", "hangzhoudong", "hzd", "杭州"], ... ],   // [站名, 起售时间, 全拼, 首字母, 城市]
  "holidays": [ { "name": "元旦", "start": "2027-01-01", "end": "2027-01-03", "year": 2027, "est": true } ],
  "news": [ { "title", "url", "source", "time", "topic": "规则|火车票|机票" } ],
  "sources": [ { "name", "ok", "count", "error?", "updated" } ]
}
```

---

## 本地预览

```
python3 scraper.py
python3 -m http.server 8794
# 打开 http://localhost:8794
```
