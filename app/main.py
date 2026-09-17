from fastapi import FastAPI
from app.api.voice import router as voice_router

app = FastAPI(
    title="AI语音对话助手后端",
    description="Python FastAPI 后端服务，提供语音识别（ASR）、语音合成（TTS）与 AI 语音对话能力，面向本地/局域网单用户场景。",
    version="0.1.0",
)

# 语音对话（音箱式交互）
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])


@app.on_event("startup")
async def preload_asr_model():
    """启动时预加载 ASR 模型，避免第一个请求等太久"""
    from app.clients import asr_client
    asr_client._get_model()


@app.get("/", summary="服务健康检查")
async def root():
    return {"status": "ok", "message": "AI语音对话助手后端已启动"}
