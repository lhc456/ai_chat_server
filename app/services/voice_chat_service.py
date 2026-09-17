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
# 情感要点：文本的情绪决定语音的感情——带语气词、口语断句，合成出来才不像机器人
SYSTEM_PROMPT = (
    "你是家里智能音箱的语音助手，性格热情开朗，像一个熟悉的朋友在聊天。"
    "要求："
    "① 简短口语化，不超过40个字，一般就一两句话；"
    "② 适当用语气词（呀、哦、呢、嘛、哈、嗯）和口语表达（特好、特棒、没问题、放心吧）；"
    "③ 语调有起伏，重要的话可以带点感叹，遇到安慰、提醒时语气放轻放暖；"
    "④ 不要 emoji、不要 markdown、不要书面语和长句堆叠，断句要符合说话节奏。"
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
        # 后续优化点：让 LLM 同时输出情绪标签，配合 Azure express-as 切换情感风格

        return VoiceChatResponse(
            user_text=user_text,
            reply_text=reply_text,
            audio=audio_out,
            elapsed_ms=int((time.time() - start) * 1000),
        )
