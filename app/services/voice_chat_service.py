"""
语音对话服务

提供两条独立的基础能力（不依赖 AI）：
- audio → text  语音识别（ASR）
- text → audio  语音合成（TTS）

以及一条完整管线（依赖 Ollama AI，需要配置开启）：
- audio → text → AI → audio  语音对话
"""
import re
import time
from typing import AsyncGenerator

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


# 按句切分：中文标点后断句，问号/叹号/省略号都算句尾；
# 逗号过长时也切（避免长句迟迟不出的情况）
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？；!?;~～…])(?=[^\s])")
_MAX_SUB_LEN = 22  # 单个分段超过这个长度时在逗号处再切一刀


def _split_sentences(buffer: str) -> list[str]:
    """把累计文本切成「完整句 + 未完部分」两段，返回 [完整句列表, 剩余文本]"""
    parts = _SENTENCE_SPLIT.split(buffer)
    done, tail = parts[:-1], parts[-1]
    # 长句在逗号处补切，让首句更快出来
    out: list[str] = []
    for seg in done:
        seg = seg.strip()
        if not seg:
            continue
        while len(seg) > _MAX_SUB_LEN:
            cut = seg.rfind("，", 0, _MAX_SUB_LEN)
            if cut <= 0:
                break
            out.append(seg[: cut + 1])
            seg = seg[cut + 1 :]
        if seg:
            out.append(seg)
    return out, tail.strip()


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
    async def streaming_conversation(
        audio_bytes: bytes,
        history: list[dict] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        全链路流式对话：ASR → LLM 逐 token → 按句切分 → 每句立刻 TTS

        事件流（dict）:
            {"type": "user",     "text": str}                  识别结果
            {"type": "sentence", "text": str, "audio": bytes}  一句话及其语音
            {"type": "done",     "text": str, "elapsed_ms": int} 全文与总耗时

        Args:
            history: 历史消息（[{role, content}]），可为空
        """
        from app.clients.ollama_client import OllamaClient

        start = time.time()

        # 1. ASR：语音 → 文字
        user_text = await asr_client.transcribe(audio_bytes)
        if not user_text:
            raise ValueError("未能识别出有效语音内容")
        yield {"type": "user", "text": user_text}

        # 2. LLM 流式生成 + 按句切分
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += (history or [])[-6:]
        messages.append({"role": "user", "content": user_text})

        buffer = ""
        full_text = ""
        async for delta in OllamaClient.stream_chat_reply(messages):
            buffer += delta
            sentences, buffer = _split_sentences(buffer)
            for sentence in sentences:
                full_text += sentence
                # 3. 每凑齐一句立刻合成，不等全文
                audio = await tts_client.synthesize(sentence)
                yield {"type": "sentence", "text": sentence, "audio": audio}

        # 收尾：把最后没凑齐一句的余量也合成播出去
        tail = buffer.strip()
        if tail:
            full_text += tail
            audio = await tts_client.synthesize(tail)
            yield {"type": "sentence", "text": tail, "audio": audio}

        yield {
            "type": "done",
            "text": full_text,
            "elapsed_ms": int((time.time() - start) * 1000),
        }

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
