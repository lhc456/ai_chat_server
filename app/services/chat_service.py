from app.models.schemas import ChatRequest


class ChatService:
    @staticmethod
    async def create_reply(request: ChatRequest) -> str:
        # TODO: 集成AI模型调用，将用户输入传给模型并返回生成的文本
        return f"这是助手的默认回复，已收到：{request.message}"
