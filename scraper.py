# Created by 青云 on 2026/10/21.
"""抢票日历 数据抓取。只用标准库。

- 12306 各车站起售时间（qss.js）+ 车站名 / 拼音 / 城市（station_name.js）
- 节假日：读取拼假攻略站点的 data.json（climb0516.github.io/holiday-planner）
- 新闻：Google News RSS（预售期调整、春运购票、春运机票）
开售日期本身是规则推算（出发日 − 14 天），在前端完成。
"""
import html, json, re, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta, date
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
CST = timezone(timedelta(hours=8))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://kyfw.12306.cn/"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8-sig", "ignore")


# ── 12306 车站与起售时间 ─────────────────────────────────
def stations():
    times = dict(re.findall(r'"([^"]+)"\s*:\s*"(\d{2}:\d{2})"', fetch("https://kyfw.12306.cn/otn/resources/js/query/qss.js")))
    if len(times) < 500:
        raise ValueError(f"only {len(times)} sale times")
    meta = {}
    raw = fetch("https://kyfw.12306.cn/otn/resources/js/framework/station_name.js")
    for rec in raw.split("@")[1:]:
        f = rec.split("|")
        if len(f) >= 8:
            meta[f[1]] = {"pinyin": f[3], "short": f[4], "city": f[7] or f[1]}
    # 精简成数组省体积：[站名, 起售时间, 全拼, 首字母, 所属城市]
    out = [[n, t, meta.get(n, {}).get("pinyin", ""), meta.get(n, {}).get("short", ""), meta.get(n, {}).get("city", "")]
           for n, t in times.items()]
    return sorted(out, key=lambda x: x[2] or x[0])


# ── 节假日（拼假攻略联动）───────────────────────────────
def holidays():
    d = json.loads(fetch("https://climb0516.github.io/holiday-planner/data.json"))
    official_years = {y for y, v in (d.get("announce") or {}).items()}
    plan_year, plan_official = d.get("summary", {}).get("plan_year"), d.get("summary", {}).get("plan_official", True)
    out = []
    for year, v in (d.get("cn") or {}).items():
        days = sorted((x for x in v.get("days", []) if x.get("off")), key=lambda x: x["date"])
        # 连续放假且同名的日子合成一个假期
        cur = None
        for x in days:
            if cur and x["name"] == cur["name"] and (date.fromisoformat(x["date"]) - date.fromisoformat(cur["end"])).days == 1:
                cur["end"] = x["date"]
            else:
                if cur:
                    out.append(cur)
                cur = {"name": x["name"], "start": x["date"], "end": x["date"], "year": int(year),
                       "est": int(year) == plan_year and not plan_official and year not in official_years}
        if cur:
            out.append(cur)
    # 拼假数据只列法定放假日，把前后相连的周末并进来（被调休成上班日的周末除外）
    work = {x["date"] for v in (d.get("cn") or {}).values() for x in v.get("days", []) if not x.get("off")}
    def weekend_off(day):
        return day.weekday() >= 5 and day.isoformat() not in work
    for h in out:
        s, e = date.fromisoformat(h["start"]), date.fromisoformat(h["end"])
        while weekend_off(s - timedelta(days=1)):
            s -= timedelta(days=1)
        while weekend_off(e + timedelta(days=1)):
            e += timedelta(days=1)
        h["start"], h["end"] = s.isoformat(), e.isoformat()
    if not out:
        raise ValueError("no holidays")
    return sorted(out, key=lambda h: h["start"])


# ── 新闻 ────────────────────────────────────────────────
def news():
    out = []
    for q, topic in (("12306 预售期 when:60d", "规则"), ("火车票 开售 春运 OR 国庆 OR 元旦 when:30d", "火车票"),
                     ("春运 机票 开售 OR 预订 when:60d", "机票")):
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"})
        root = ET.fromstring(fetch(url))
        for it in root.iter("item"):
            title, src = it.findtext("title") or "", it.find("source")
            source = (src.text or "") if src is not None else ""
            if source and title.endswith(" - " + source):
                title = title[: -len(source) - 3]
            try:
                t = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).isoformat()
            except Exception:
                continue
            out.append({"title": html.unescape(title), "url": it.findtext("link"), "source": source, "time": t, "topic": topic})
    seen, uniq = set(), []
    for n in sorted(out, key=lambda x: x["time"], reverse=True):
        key = re.sub(r"\W", "", n["title"])[:18]
        if key not in seen:
            seen.add(key)
            uniq.append(n)
    return uniq[:40]


def main():
    old = {}
    if DATA_FILE.exists():
        try:
            old = json.loads(DATA_FILE.read_text("utf-8"))
        except Exception:
            old = {}
    now = datetime.now(CST).isoformat(timespec="seconds")
    sources = []

    def run(name, fn, key):
        try:
            res = fn()
            sources.append({"name": name, "ok": True, "count": len(res), "updated": now})
            return res
        except Exception as e:
            prev = next((s for s in old.get("sources", []) if s["name"] == name), {})
            sources.append({"name": name, "ok": False, "error": str(e)[:120], "updated": prev.get("updated")})
            return old.get(key, [])

    data = {
        "updated": now,                       # 每次都变 = 心跳，保证每次运行都有提交
        "rule": {"presale_days": 15, "note": "预售期 15 天（含当天），即出发日前 14 天开售；起售时间以出发站为准"},
        "stations": run("12306 起售时间", stations, "stations"),
        "holidays": run("拼假攻略 节假日", holidays, "holidays"),
        "news": run("Google News", news, "news"),
        "sources": sources,
    }
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print("stations", len(data["stations"]), data["stations"][:2])
    print("holidays", [(h["name"], h["start"], h["end"], h["est"]) for h in data["holidays"]])
    print("news", len(data["news"]), "failed", [s["name"] for s in sources if not s["ok"]])


if __name__ == "__main__":
    main()
