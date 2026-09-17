"""
联网搜索客户端（Exa，为 AI agent 设计的搜索 API）

- 用自然语言搜索，返回标题+URL+相关摘要（highlights）
- 需要联网 Key：https://dashboard.exa.ai/keys
- 用途：做饭/生活常识/专业知识等模型不确定的问题
"""
import httpx

from app.core.config import settings

_API_URL = "https://api.exa.ai/search"


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
