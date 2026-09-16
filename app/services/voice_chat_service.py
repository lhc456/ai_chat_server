"""
语音对话服务

提供两条独立的基础能力（不依赖 AI）：
- audio → text  语音识别（ASR）
- text → audio  语音合成（TTS）

以及一条完整管线（依赖 Ollama AI，需要配置开启）：
- audio → text → AI → audio  语音对话
"""
import time

from app.clients import asr_client, tts_client
from app.models.schemas import SynthesizeResponse, TranscribeResponse, VoiceChatResponse

# 系统提示词：把 AI 定位成音箱助手，回复简短口语化（语音播报太长体验差）
SYSTEM_PROMPT = (
    "你是一个智能音箱助手，通过语音和用户对话。"
    "请用简短、口语化的中文回答，一般不超过50个字，不要使用 emoji 和 markdown 格式。"
)


class VoiceChatService:
    @staticmethod
    async def audio_to_text(audio_bytes: bytes) -> TranscribeResponse:
        """语音识别：录音 → 文字（不依赖 AI，始终可用）"""
        start = time.time()
        text = await asr_client.transcribe(audio_bytes)
        if not text:
            raise ValueError("未能识别出有效语音内容")
        return TranscribeResponse(
            text=text,
            elapsed_ms=int((time.time() - start) * 1000),
        )

    @staticmethod
    async def text_to_audio(text: str) -> SynthesizeResponse:
        """语音合成：文字 → 语音（不依赖 AI，始终可用）"""
        start = time.time()
        audio = await tts_client.synthesize(text)
        return SynthesizeResponse(
            audio=audio,
            elapsed_ms=int((time.time() - start) * 1000),
        )

    @staticmethod
    async def process(audio_bytes: bytes) -> VoiceChatResponse:
        """
        完整语音对话管线（需要 AI，配置 voice_ai_enabled=true 才能调用）

        录音 → ASR → Ollama 生成回复 → TTS → 返回语音
        """
        from app.clients.ollama_client import OllamaClient

        start = time.time()

        # 1. ASR：语音 → 文字
        user_text = await asr_client.transcribe(audio_bytes)
        if not user_text:
            raise ValueError("未能识别出有效语音内容")

        # 2. LLM：文字 → AI回复
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]
        reply_text = await OllamaClient.create_chat_reply(messages)

        # 3. TTS：回复文字 → 语音
        audio_out = await tts_client.synthesize(reply_text)

        return VoiceChatResponse(
            user_text=user_text,
            reply_text=reply_text,
            audio=audio_out,
            elapsed_ms=int((time.time() - start) * 1000),
        )
