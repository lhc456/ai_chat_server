"""
地点/去处推荐（建议系统第 2 层）：动态搜索为主 → 静态库兑底 → 自定义地点优先

查找链路（见 ROADMAP.md「建议系统三层化」）：
  ① data/my_places.json 用户自定义（最高优先，乡下也能自己加）
  ② Exa 动态搜「当前城市 特色景点 当季」（任意城市自动覆盖，7天缓存+质量门控）
  ③ 内置静态库（杭州等，断网可用）
  → 全都没有返回 None，上层降级到第 1 层活动建议

地点条目统一结构：
  name / desc / vibe(scenic|park|food|indoor) / indoor / best_months
"""
import json
import random
from pathlib import Path

# WMO 降水类代码（出现即算"有雨"）
_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}

# 最近两次已推荐的地名（跨请求轮换，避免每次都同一处）
_recent_picks: list[str] = []

# 用户自定义地点缓存（文件加载一次）
_custom_places: dict | None = None
_CUSTOM_PATH = Path("data/my_places.json")


def _load_custom() -> dict:
    """加载用户自定义地点文件；不存在/格式错返回空结构"""
    global _custom_places
    if _custom_places is not None:
        return _custom_places
    try:
        _custom_places = json.loads(_CUSTOM_PATH.read_text(encoding="utf-8"))
        _custom_places.pop("_说明", None)
    except Exception:
        _custom_places = {}
    return _custom_places

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


def _context_lead(weekday: int, hour: int, rainy: bool, hot: bool, is_tomorrow: bool) -> str:
    """生成场景化开头：问明天时按「明天的场景」来说"""
    if is_tomorrow:
        tm_weekday = (weekday + 1) % 7
        if rainy:
            return "明天有雨，安排室内比较稳妥"
        if tm_weekday == 4 and hour >= 16:
            return "明天周五，晚上可以约上朋友聚一聚"
        if tm_weekday >= 5:
            return "明天周末，时间充裕，可以去远一点的地方"
        if tm_weekday < 5 and hour >= 17:
            return "明天工作日，下班后就近放松一下就好"
        return "明天是工作日"
    # 今天：沿用原有场景
    if rainy:
        return "雨天适合室内安排"
    if hot:
        return "天热注意防晒补水"
    if weekday == 4 and hour >= 16:
        return "周五了，可以约上朋友"
    if weekday < 5 and hour >= 17:
        return "下班后正好放松一下"
    return "天气不错"


def _pick_from_pool(
    pool: list[tuple[dict, bool]],
    district: str | None,
    weekday: int,
    hour: int,
    rainy: bool,
    hot: bool,
    month: int,
    is_tomorrow: bool,
) -> str | None:
    """从候选池按场景打分+轮换随机选出推荐句；池空返回 None"""
    vibes = _context_vibes(weekday, hour, rainy, hot)

    def _eligible(s: dict) -> bool:
        return s["indoor"] == rainy and (not s["best_months"] or month in s["best_months"])

    def _score(s: dict, same_district: bool) -> tuple:
        vibe_rank = vibes.index(s["vibe"]) if s["vibe"] in vibes else len(vibes)
        season_ok = 0 if (not s["best_months"] or month in s["best_months"]) else 1
        return (not same_district, vibe_rank, season_ok)

    pool = [(s, near) for s, near in pool if _eligible(s)]
    if not pool:  # 季节筛没结果 → 放宽季节
        pool = [(s, near) for s, near in pool if s["indoor"] == rainy]
    if not pool:
        return None

    # 排序后取前 5 做随机池，避开最近推过的：有变化但不至于推太偏
    pool.sort(key=lambda x: _score(x[0], x[1]))
    top = [x for x in pool[:5] if x[0]["name"] not in _recent_picks] or pool[:5]
    picks = random.sample(top, min(2, len(top)))

    global _recent_picks
    _recent_picks = [s["name"] for s, _ in picks] + _recent_picks
    _recent_picks = _recent_picks[:2]

    names = "、".join(s["name"] for s, _ in picks)
    detail = picks[0][0]["desc"]
    near_pick = picks[0][1]
    where = f"{district}附近的" if (district and near_pick) else ""
    lead = _context_lead(weekday, hour, rainy, hot, is_tomorrow)
    far_hint = (
        "，虽然有点远，但值得跑一趟"
        if (not near_pick and (is_tomorrow or weekday >= 4))
        else ""
    )
    return f"{lead}，{where}{names}可以去看看，{detail}{far_hint}"


def recommend(
    city: str,
    district: str | None,
    weather_code_today: int,
    temp_max_today: float,
    month: int,
    weekday: int,
    hour: int,
    is_tomorrow: bool = False,
    custom_only: bool = False,
) -> str | None:
    """
    地点推荐（第 2 层）：自定义地点 → 静态库筛选

    动态搜索由上层（voice_chat_service）先行尝试，搜到就把结果传进来；
    本函数只负责结构化地点的筛选与轮换。

    Returns:
        推荐句；无合适地点返回 None（上层降级到第 1 层活动建议）

    Args:
        custom_only: True 时只用用户自定义地点（乡下场景：库里没这个城市）
    """
    rainy = int(weather_code_today or 0) in _RAIN_CODES
    hot = temp_max_today is not None and temp_max_today >= 32

    # ① 用户自定义地点（最高优先级）：城市匹配 + 不限区匹配（区对不上也给全国性候选）
    custom = _load_custom().get(city) or _load_custom().get(city.rstrip("市")) or {}
    if custom:
        pool: list[tuple[dict, bool]] = []
        for d, spots in custom.items():
            pool += [(s, d == district) for s in spots]
        got = _pick_from_pool(pool, district, weekday, hour, rainy, hot, month, is_tomorrow)
        if got:
            return got

    if custom_only:
        return None  # 乡下模式：没有自定义地点就不硬凑

    # ② 内置静态库
    city_lib = _LIBRARY.get(city.rstrip("市"))
    if not city_lib:
        return None

    pool = []
    if district:
        pool += [(s, True) for s in city_lib.get(district, [])]
    for d, spots in city_lib.items():
        if d != district:
            pool += [(s, False) for s in spots]

    return _pick_from_pool(pool, district, weekday, hour, rainy, hot, month, is_tomorrow)
