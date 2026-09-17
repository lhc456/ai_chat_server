import json
import time

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.clients import tts_client
from app.core.config import settings
from app.services.voice_chat_service import VoiceChatService

router = APIRouter()


@router.post(
    "/synthesize",
    summary="文字转语音（TTS，无需 AI）",
    description=(
        "把一段文字合成 mp3 语音，直接返回音频二进制。\n\n"
        "不依赖 AI 模型，当前始终可用。"
    ),
)
async def synthesize(text: str = Form(..., description="要合成的文字", min_length=1, max_length=1000)):
    try:
        result = await VoiceChatService.text_to_audio(text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"语音合成服务暂时不可用: {e}")

    return Response(
        content=result.audio,
        media_type="audio/mpeg",
        headers={
            "X-Elapsed-Ms": str(result.elapsed_ms),
            "Content-Disposition": 'inline; filename="tts.mp3"',
        },
    )


@router.get(
    "/synthesize/stream",
    summary="文字转语音（流式，边合成边返回）",
    description=(
        "把一段文字合成 mp3 语音，边合成边推送音频块。\n\n"
        "客户端拿到第一个音频块即可开始播放，首音延迟显著低于整段合成接口。\n"
        "响应头 X-TTFB-Ms 为首块音频的等待耗时（首音延迟）。"
    ),
)
async def synthesize_stream(text: str = Query(..., description="要合成的文字", min_length=1, max_length=1000)):
    start = time.time()

    # 先等第一块音频再返回响应：这一步的耗时就是首音延迟（TTFB），
    # 拿到后记进响应头；后续音频块由 StreamingResponse 边合成边推。
    try:
        gen = tts_client.stream_synthesize(text)
        first_chunk = await gen.__anext__()
    except StopAsyncIteration:
        raise HTTPException(status_code=503, detail="语音合成服务未返回音频")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"语音合成服务暂时不可用: {e}")

    ttfb_ms = int((time.time() - start) * 1000)

    async def audio_stream():
        yield first_chunk
        async for chunk in gen:
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "X-TTFB-Ms": str(ttfb_ms),
            "Content-Disposition": 'inline; filename="tts_stream.mp3"',
        },
    )


@router.post(
    "/transcribe",
    summary="语音识别（ASR，无需 AI）",
    description=(
        "上传录音文件，返回识别出的文字（JSON）。\n\n"
        "不依赖 AI 模型，当前始终可用。\n"
        "音频文件作为 multipart 的 audio 字段上传。"
    ),
)
async def transcribe(audio: UploadFile = File(..., description="录音音频文件（wav/mp3/webm 等）")):
    audio_bytes = _read_audio(audio)
    try:
        result = await VoiceChatService.audio_to_text(audio_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"语音识别服务暂时不可用: {e}")

    return {
        "text": result.text,
        "elapsed_ms": result.elapsed_ms,
    }


@router.post(
    "/interaction",
    summary="完整语音对话（ASR → AI → TTS）",
    description=(
        "完整管线：语音识别 → AI 生成回复 → 语音合成。\n\n"
        "**当前 AI 功能尚未开启**（voice_ai_enabled=false），调用会返回 503。"
        "等 AI 模型准备好后，在 .env 中设置 VOICE_AI_ENABLED=true 即可启用。"
    ),
)
async def voice_interaction(audio: UploadFile = File(..., description="录音音频文件（wav/mp3/webm 等）")):
    # AI 功能开关：训练好之前先关闭
    if not settings.voice_ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI对话功能尚未开启（voice_ai_enabled=false）。当前可使用 /api/voice/synthesize 和 /api/voice/transcribe。",
        )

    audio_bytes = _read_audio(audio)
    try:
        result = await VoiceChatService.process(audio_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"语音服务暂时不可用: {e}")

    # audio 是二进制，不能直接进 JSON；分开返回：
    # - X-User-Text / X-Reply-Text 头携带文字（JSON编码保证中文安全）
    # - 响应体是 mp3 音频流，客户端拿到就能直接播放
    return Response(
        content=result.audio,
        media_type="audio/mpeg",
        headers={
            "X-User-Text": json.dumps(result.user_text, ensure_ascii=False),
            "X-Reply-Text": json.dumps(result.reply_text, ensure_ascii=False),
            "X-Elapsed-Ms": str(result.elapsed_ms),
            "Content-Disposition": 'inline; filename="reply.mp3"',
        },
    )


def _read_audio(audio: UploadFile) -> bytes:
    """读取并校验上传的音频"""
    if not audio.filename:
        raise HTTPException(status_code=422, detail="缺少 audio 字段")
    audio_bytes = audio.file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="音频内容为空")
    # 简单限制 20MB，防止误传大文件
    if len(audio_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="音频文件过大（限制 20MB）")
    return audio_bytes
