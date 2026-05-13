from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse, summary="Chat with the AI assistant")
async def chat(request: ChatRequest):
    reply = await ChatService.create_reply(request)
    return ChatResponse(reply=reply)
