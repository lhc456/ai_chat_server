"""
活动建议库（建议系统第 1 层：天气/季节/时段驱动，城乡通用，零地点依赖）

设计原则（见 ROADMAP.md「建议系统三层化」）：
- 活动建议永远可得——乡下/小城镇没有地点数据也能给出贴生活的建议
- 按「天气现象 + 温度区间 + 季节/时段」匹配，输出口语化短句
- LLM 拿到后用自己的语气组织，不照抄
"""

# 天气现象 → 生活活动建议（数组，随机/合并取用）
_BY_CONDITION = {
    "clear": [
        "适合把被子衣物拿出去晒晒",
        "开窗通通风，屋里换换空气",
        "傍晚凉快了出去走走正舒服",
    ],
    "cloudy": [
        "不晒不闷，出门活动正合适",
        "适合出门办办事、走一走",
    ],
    "rain": [
        "出门记得带伞",
        "晾在外面的衣服记得收",
        "雨天路滑，骑车开车慢一点",
    ],
    "snow": [
        "路面可能结冰，出门当心滑",
        "记得多穿点，注意保暖",
    ],
    "fog": [
        "有雾看不远，开车骑车慢点",
        "早晚能见度低，出行注意安全",
    ],
}

# 温度区间 → 提示
_BY_TEMP = [
    (32, "天热，多喝水防晒，正午尽量别在太阳下待"),
    (28, "白天有点热，活动安排在早晚更舒服"),
    (18, "温度挺舒服的"),
    (8, "有点凉，出门加件外套"),
    (-99, "天冷，注意保暖防感冒"),
]

# 季节/月份 → 时令提示（month → 提示）
_BY_SEASON = {
    3: "春天来了，万物复苏，是踏青的好时节",
    4: "春光正好，适合踏青赏花",
    5: "初夏不冷不热，户外活动好时候",
    6: "梅雨季，出门随身带伞",
    7: "三伏天，防暑降温是头等大事",
    8: "秋老虎还在，防暑别松懈",
    9: "入秋了，早晚渐凉，早晚加件薄外套",
    10: "秋高气爽，一年里最适合出门的月份",
    11: "深秋渐冷，注意添衣",
    12: "入冬了，保暖第一，屋里记得通风",
    1: "数九寒天，防寒保暖，小心路滑",
    2: "乍暖还寒，春捂秋冻，别急着减衣",
}


def _condition_key(desc: str) -> str:
    """WMO 中文描述 → 条件键"""
    if any(k in desc for k in ("雨",)):
        return "rain"
    if "雪" in desc:
        return "snow"
    if "雾" in desc:
        return "fog"
    if "晴" in desc:
        return "clear"
    return "cloudy"  # 多云/阴


def get_activity_tips(desc: str, temp: float, month: int, weekday: int, hour: int) -> str:
    """
    生成活动/生活建议（第 1 层，任何地方都成立）

    Args:
        desc: 天气中文描述（晴/多云/小雨…）
        temp: 当前温度 °C
        month: 月份 1~12
        weekday: 星期 0=周一…6=周日
        hour: 小时 0~23
    """
    import random

    parts = []

    # 天气现象建议（随机取一条，避免每次一样）
    tips = _BY_CONDITION.get(_condition_key(desc), _BY_CONDITION["cloudy"])
    parts.append(random.choice(tips))

    # 温度提示（阈值从高到低，命中第一条区间就停）
    for threshold, tip in _BY_TEMP:
        if temp >= threshold:
            if tip not in parts:
                parts.append(tip)
            break

    # 时令提示（一半概率带出，避免太长）
    season_tip = _BY_SEASON.get(month)
    if season_tip and random.random() < 0.5 and season_tip not in parts:
        parts.append(season_tip)

    # 时段补充
    if weekday < 5 and 7 <= hour <= 9:
        parts.append("通勤路上注意安全")
    elif weekday >= 5 and 9 <= hour <= 18:
        parts.append("周末有空可以好好放松下")

    return "；".join(parts[:3])  # 最多三段，控制长度
