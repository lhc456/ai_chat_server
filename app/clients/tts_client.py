"""
TTS 语音合成客户端（基于 edge-tts，微软 Edge 浏览器的在线 TTS 服务，免费无需 Key）

优点：中文自然度高、免费
限制：需要联网；个别网络环境下可能不稳定，后续可换成本地 TTS（如 piper）
"""
import uuid
from pathlib import Path

import edge_tts

from app.core.config import settings

# 合成音频临时存放目录
AUDIO_OUT_DIR = Path("data/audio_tmp")
AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)


async def synthesize(text: str, voice: str = None) -> bytes:
    """
    把文字合成语音，返回 mp3 音频数据

    Args:
        text: 要合成的文字
        voice: 发音人，默认用配置里的（zh-CN-XiaoxiaoNeural 晓晓）

    Returns:
        mp3 格式的音频二进制
    """
    if not text.strip():
        raise ValueError("合成内容不能为空")

    voice = voice or settings.tts_voice
    communicate = edge_tts.Communicate(text, voice, rate=settings.tts_rate)

    audio_path = AUDIO_OUT_DIR / f"tts_{uuid.uuid4().hex}.mp3"
    try:
        await communicate.save(str(audio_path))
        return audio_path.read_bytes()
    finally:
        audio_path.unlink(missing_ok=True)
