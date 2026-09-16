import httpx
from app.core.config import settings


class OllamaClient:
    """Ollama 本地大模型客户端"""

    # Ollama API 默认地址
    BASE_URL = "http://localhost:11434"

    @classmethod
    async def create_chat_reply(
        cls,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7
    ) -> str:
        """
        调用 Ollama API 生成对话回复

        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 使用的模型名称，默认从配置读取
            temperature: 温度参数，控制随机性

        Returns:
            AI 生成的回复文本
        """
        if model is None:
            model = settings.ollama_model

        url = f"{cls.BASE_URL}/api/chat"

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,  # 不使用流式响应
            "options": {
                "temperature": temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                # 提取回复内容
                reply = data.get("message", {}).get("content", "")
                return reply.strip()

        except httpx.ConnectError:
            raise Exception("无法连接到 Ollama 服务，请确保 ollama serve 正在运行")
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Ollama API 请求失败: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"调用 Ollama 失败: {str(e)}")

    @classmethod
    async def check_health(cls) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{cls.BASE_URL}/api/tags")
                return response.status_code == 200
        except:
            return False

    @classmethod
    async def list_models(cls) -> list[str]:
        """获取可用的模型列表"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{cls.BASE_URL}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise Exception(f"获取模型列表失败: {str(e)}")
