"""
天气查询客户端（Open-Meteo，免费无需 Key）

- geocoding-api.open-meteo.com : 城市名 → 经纬度
- api.open-meteo.com/v1/forecast : 经纬度 → 实时天气 + 今明两天预报

带进程内缓存：天气 20 分钟、城市坐标永久，避免频繁外网请求。
"""
import time

import httpx

# WMO 天气代码 → 中文描述
_WMO_DESC = {
    0: "晴", 1: "基本晴", 2: "多云", 3: "阴",
    45: "有雾", 48: "雾凇",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    56: "冻毛毛雨", 57: "强冻毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "强冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
    80: "阵雨", 81: "中阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷阵雨伴冰雹",
}


def _desc(code) -> str:
    return _WMO_DESC.get(int(code or 0), "未知天气")


_geo_cache: dict[str, tuple[float, float]] = {}
_reverse_cache: dict[tuple, tuple[str, str] | None] = {}  # 坐标 → (城市, 区)， keyed by 约1km精度
_weather_cache: dict[str, tuple[float, dict]] = {}  # key → (过期时间, 数据)
_WEATHER_TTL = 20 * 60  # 天气缓存 20 分钟


async def _fetch(url: str, params: dict) -> dict:
    """带一次重试的 GET：外网偶发抖动时不至于整轮失败"""
    last_err = None
    for _ in range(2):
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json()
        except (httpx.TimeoutException, httpx.HTTPError) as e:
            last_err = e
    raise last_err


async def geocode(city: str) -> tuple[float, float] | None:
    """城市名 → (纬度, 经度)，进程内缓存"""
    if city in _geo_cache:
        return _geo_cache[city]

    results = (await _fetch(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 1, "language": "zh", "format": "json"},
    )).get("results") or []
    if not results:
        return None
    loc = (results[0]["latitude"], results[0]["longitude"])

    _geo_cache[city] = loc
    return loc


async def reverse_district(lat: float, lon: float) -> tuple[str, str] | None:
    """
    坐标 → (城市, 区)，就近推荐的依据（OSM Nominatim，免费无 Key）

    返回如 ("杭州", "西湖区")；失败返回 None（推荐降级为全市范围）
    """
    key = (round(lat, 2), round(lon, 2))
    if key in _reverse_cache:
        return _reverse_cache[key]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={"lat": lat, "lon": lon, "zoom": 10, "accept-language": "zh-CN", "format": "json"},
                headers={"User-Agent": "ai-server-voice-box/0.1"},  # Nominatim 要求带 UA
            )
            r.raise_for_status()
            addr = r.json().get("address", {})
    except Exception:
        _reverse_cache[key] = None
        return None

    # 中国行政区划在 OSM 里的层级不统一：区可能出现在 city 字段（如"西湖区"），
    # 街道在 city_district；做兼容解析
    city_raw = addr.get("city") or ""
    if city_raw.endswith("区"):
        district, city = city_raw, ""
    else:
        city = city_raw.rstrip("市")
        district = (
            addr.get("city_district") or addr.get("suburb")
            or addr.get("district") or addr.get("county")
        )
    val = (city or None, district) if district else None
    _reverse_cache[key] = val
    return val


async def get_weather(city: str, lat: float = None, lon: float = None) -> dict:
    """
    查询实时天气 + 今明两天预报

    Args:
        city: 城市名（用于展示和地理编码）
        lat/lon: 设备定位的经纬度；给了就直接用，跳过地理编码
    """
    cache_key = f"loc:{lat:.3f},{lon:.3f}" if lat is not None else f"city:{city}"
    now = time.time()
    hit = _weather_cache.get(cache_key)
    if hit and hit[0] > now:
        return hit[1]

    if lat is None:
        loc = await geocode(city)
        if loc is None:
            raise ValueError(f"找不到城市：{city}")
        lat, lon = loc

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 2,
    }
    d = await _fetch("https://api.open-meteo.com/v1/forecast", params)

    cur, daily = d["current"], d["daily"]
    data = {
        "city": city,
        "current": {
            "temp": cur["temperature_2m"],
            "feels": cur["apparent_temperature"],
            "desc": _desc(cur["weather_code"]),
            "wind": cur["wind_speed_10m"],
            "humidity": cur["relative_humidity_2m"],
        },
        "today": {
            "desc": _desc(daily["weather_code"][0]),
            "code": int(daily["weather_code"][0]),
            "max": daily["temperature_2m_max"][0],
            "min": daily["temperature_2m_min"][0],
            "precip_prob": daily["precipitation_probability_max"][0],
        },
        "tomorrow": {
            "desc": _desc(daily["weather_code"][1]),
            "max": daily["temperature_2m_max"][1],
            "min": daily["temperature_2m_min"][1],
            "precip_prob": daily["precipitation_probability_max"][1],
        },
    }
    _weather_cache[cache_key] = (now + _WEATHER_TTL, data)
    return data


def format_weather(w: dict) -> str:
    """把天气数据压成一段中文，喂给 LLM 当工具结果（含环境线索，供模型灵活生成建议）"""
    import datetime

    c, t, m = w["current"], w["today"], w["tomorrow"]

    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=周一 … 6=周日
    day_type = "周末" if weekday >= 5 else "工作日"
    hour = now.hour
    if 6 <= hour < 11:
        period = "上午"
    elif 11 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 23:
        period = "晚上"
    else:
        period = "深夜"

    # 温差与舒适度线索
    temp_span = round(t["max"] - t["min"], 1)
    comfort = "温度舒适" if 18 <= t["max"] <= 28 else ("偏热" if t["max"] > 32 else "偏凉")

    return (
        f"{w['city']}当前{c['desc']}，湿度{c['humidity']}%，风速{c['wind']}km/h；"
        f"今天{t['desc']}，气温{t['min']}~{t['max']}°C（{comfort}，温差{temp_span}度），"
        f"降水概率{t['precip_prob']}%；"
        f"明天{m['desc']}，{m['min']}~{m['max']}°C，降水概率{m['precip_prob']}%；"
        f"现在是{day_type}{period}。请结合周末/工作日、时段、温度舒适度、降水概率给出针对性建议"
    )
