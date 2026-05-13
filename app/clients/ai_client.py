import httpx
from app.core.config import settings


class AIClient:
    OPENAI_URL = "https://api.openai.com/v1/chat/completions"

    @classmethod
    async def create_chat_reply(cls, messages: list[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(cls.OPENAI_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
