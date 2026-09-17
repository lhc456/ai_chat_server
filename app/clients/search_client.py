"""
联网搜索客户端（Exa，为 AI agent 设计的搜索 API）

- 用自然语言搜索，返回标题+URL+相关摘要（highlights）
- 需要联网 Key：https://dashboard.exa.ai/keys
- 用途：做饭/生活常识/专业知识等模型不确定的问题
"""
import time

import httpx

from app.core.config import settings

_API_URL = "https://api.exa.ai/search"

# 城市特色景点搜索缓存：{query → (过期时间, 结果)}，7 天
_poi_cache: dict[str, tuple[float, str]] = {}
_POI_TTL = 7 * 24 * 3600


async def search_web(query: str, num_results: int = 3) -> str:
    """
    联网搜索，返回拼好的中文结果文本（喂给 LLM 当工具结果）

    Args:
        query: 自然语言搜索词，如「红烧肉怎么做不腻」
        num_results: 返回条数（默认 3，语音场景不需要太多）
    """
    if not settings.exa_api_key:
        raise ValueError("未配置 EXA_API_KEY，无法联网搜索（.env 中添加后重启服务）")

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            _API_URL,
            headers={
                "Authorization": f"Bearer {settings.exa_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "numResults": num_results,
                "contents": {"highlights": True},
                "type": "auto",
            },
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results") or []
    if not results:
        return "没搜到相关内容"

    # 拼成紧凑文本：标题 + 最相关的一条摘要（截断，避免上下文爆炸）
    parts = []
    for item in results[:num_results]:
        title = (item.get("title") or "").strip()
        highlights = item.get("highlights") or []
        snippet = (highlights[0] if highlights else "").strip()[:150]
        if title:
            parts.append(f"《{title}》{snippet}")

    return "\n".join(parts) if parts else "没搜到相关内容"


async def search_local_spots(city: str, month: int) -> str | None:
    """
    搜「城市特色景点/时令去处」，供地点推荐层用（ROADMAP 建议系统三层化）

    - 结果缓存 7 天（景点不天天变；带当月关键词每月自然刷新）
    - 质量门控：结果为空或太短 → 返回 None，上层降级到静态库/生活建议

    Returns:
        一段拼接好的中文结果；无有效结果返回 None
    """
    if not settings.exa_api_key:
        return None

    query = f"{city} 特色景点 值得去的地方 {month}月"
    now = time.time()
    hit = _poi_cache.get(query)
    if hit and hit[0] > now:
        return hit[1]

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _API_URL,
                headers={
                    "Authorization": f"Bearer {settings.exa_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "numResults": 4,
                    "contents": {"highlights": True},
                    "type": "auto",
                },
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        return None  # 搜索失败不阻断主流程

    results = data.get("results") or []
    if not results:
        return None

    parts = []
    for item in results:
        title = (item.get("title") or "").strip()
        highlights = item.get("highlights") or []
        snippet = (highlights[0] if highlights else "").strip()[:80]
        if title:
            parts.append(f"{title}：{snippet}" if snippet else title)

    text = "".join(parts)
    # 质量门控：内容太少（可能是个小地方，搜不出特色）→ 判定无推荐
    if len(text) < 40:
        return None

    _poi_cache[query] = (now + _POI_TTL, text)
    return text
