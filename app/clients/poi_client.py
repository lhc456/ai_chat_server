"""
本地景点/去处推荐库（垂直业务点第一块拼图：不依赖高德，离线可用）

结构：城市 → 区 → 地点列表
  name:   地点名（口语播报用）
  desc:   一句话推荐语
  vibe:   scenic=游玩景点 / park=公园散步 / food=美食聚餐 / indoor=室内逛街看展
  indoor: True=室内（雨天/酷暑推荐）
  best_months: 最适合月份；空 = 全年皆宜

推荐逻辑（recommend）：按「就近同区优先 + 天气晴雨 + 星期/时段场景」筛选，
让 LLM 拿到有场景针对性的候选，而不是一套死建议。
"""

# WMO 降水类代码（出现即算"有雨"）
_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}

_LIBRARY: dict[str, dict[str, list[dict]]] = {
    "杭州": {
        "西湖区": [
            {"name": "西湖", "desc": "沿苏堤白堤走走，湖光山色最经典", "vibe": "scenic", "indoor": False, "best_months": [3, 4, 5, 9, 10, 11]},
            {"name": "灵隐寺", "desc": "古刹清净，秋天桂花香一路", "vibe": "scenic", "indoor": False, "best_months": [9, 10, 11]},
            {"name": "西溪湿地", "desc": "坐摇橹船穿水道，比西湖清静", "vibe": "scenic", "indoor": False, "best_months": [4, 5, 9, 10]},
            {"name": "浙江省博物馆", "desc": "看展览长知识，免费又凉快", "vibe": "indoor", "indoor": True, "best_months": []},
        ],
        "上城区": [
            {"name": "湖滨银泰in77", "desc": "西湖边逛街吃饭一站式", "vibe": "indoor", "indoor": True, "best_months": []},
            {"name": "清河坊街", "desc": "老字号小吃一条街，晚上最热闹", "vibe": "food", "indoor": False, "best_months": []},
        ],
        "拱墅区": [
            {"name": "京杭大运河夜游", "desc": "坐船看两岸灯光，晚上特别舒服", "vibe": "scenic", "indoor": False, "best_months": [5, 6, 7, 8, 9]},
            {"name": "胜利河美食街", "desc": "本地人也爱去的大排档一条街", "vibe": "food", "indoor": False, "best_months": []},
        ],
        "滨江区": [
            {"name": "白马湖公园", "desc": "开阔草坪湖景，人少适合遛弯", "vibe": "park", "indoor": False, "best_months": []},
            {"name": "滨江宝龙城", "desc": "吃饭看电影都方便", "vibe": "indoor", "indoor": True, "best_months": []},
        ],
        "钱塘区": [
            {"name": "金沙湖公园", "desc": "湖景草坪，散步野餐都合适", "vibe": "park", "indoor": False, "best_months": []},
            {"name": "金沙湖龙湖天街", "desc": "下沙最热闹的商场，吃喝玩乐全有", "vibe": "indoor", "indoor": True, "best_months": []},
        ],
        "余杭区": [
            {"name": "良渚古城遗址公园", "desc": "五千年文明的鹿苑草地，秋天芦苇超美", "vibe": "scenic", "indoor": False, "best_months": [9, 10, 11]},
            {"name": "西溪印象城", "desc": "逛吃逛吃，带娃也合适", "vibe": "indoor", "indoor": True, "best_months": []},
        ],
    },
}


def _context_vibes(weekday: int, hour: int, rainy: bool, hot: bool) -> list[str]:
    """按场景给出 vibe 优先级：周五晚聚餐、工作日晚轻休闲、周末白天出游…"""
    if rainy or hot:
        return ["indoor", "food", "park"]      # 恶劣天气：室内优先
    if weekday == 4 and hour >= 16:            # 周五下午/晚上：周末临近，聚餐聚会
        return ["food", "scenic", "indoor"]
    if weekday >= 5:                           # 周末白天：出游
        return ["scenic", "park", "indoor"]
    if weekday < 5 and hour >= 17:             # 工作日晚上：下班后轻松安排
        return ["park", "food", "indoor"]
    return ["scenic", "park", "indoor"]        # 其他时段


def recommend(
    city: str,
    district: str | None,
    weather_code_today: int,
    temp_max_today: float,
    month: int,
    weekday: int,
    hour: int,
) -> str:
    """
    按天气 + 区 + 星期/时段筛选 1~2 个去处，返回口语化推荐句；没有合适项返回空串

    Args:
        city: 城市（"杭州市"或"杭州"均可）
        district: 用户所在区（如"西湖区"），未知传 None（跨区推荐）
        weather_code_today: 今日 WMO 天气代码
        temp_max_today: 今日最高温
        month: 当前月份 1~12
        weekday: 星期 0=周一 … 6=周日
        hour: 当前小时 0~23
    """
    city_lib = _LIBRARY.get(city.rstrip("市"))
    if not city_lib:
        return ""

    rainy = int(weather_code_today or 0) in _RAIN_CODES
    hot = temp_max_today is not None and temp_max_today >= 32
    vibes = _context_vibes(weekday, hour, rainy, hot)

    def _eligible(s: dict) -> bool:
        return s["indoor"] == rainy and (not s["best_months"] or month in s["best_months"])

    def _score(s: dict, same_district: bool) -> tuple:
        # 就近优先级最高，其次场景 vibe，最后季节匹配
        vibe_rank = vibes.index(s["vibe"]) if s["vibe"] in vibes else len(vibes)
        season_ok = 0 if (not s["best_months"] or month in s["best_months"]) else 1
        return (not same_district, vibe_rank, season_ok)

    pool = []
    if district:
        same = city_lib.get(district, [])
        pool += [(s, True) for s in same]
    for d, spots in city_lib.items():
        if d != district:
            pool += [(s, False) for s in spots]

    pool = [(s, near) for s, near in pool if _eligible(s)]
    if not pool:  # 季节筛没结果 → 放宽季节
        pool = [(s, near) for s, near in pool] or []
        pool = [(s, near) for s, near in pool if s["indoor"] == rainy]
    if not pool:
        return ""

    pool.sort(key=lambda x: _score(x[0], x[1]))
    picks = pool[:2]
    names = "、".join(s["name"] for s, _ in picks)
    detail = picks[0][0]["desc"]

    where = f"{district}附近的" if (district and picks[0][1]) else ""
    if rainy:
        lead = "雨天适合室内安排"
    elif hot:
        lead = "天热注意防晒补水"
    elif weekday == 4 and hour >= 16:
        lead = "周五了，可以约上朋友"
    elif weekday < 5 and hour >= 17:
        lead = "下班后正好放松一下"
    else:
        lead = "天气不错"

    return f"{lead}，{where}{names}可以去看看，{detail}"
