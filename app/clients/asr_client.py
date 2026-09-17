"""
ASR 语音识别客户端（基于 faster-whisper，本地运行，免费）

faster-whisper 是 Whisper 的 CTranslate2 加速版，首次运行会自动下载模型。
模型加载比较耗时（几秒到十几秒），所以做成全局单例，服务启动后只加载一次。
"""
import asyncio
import threading
import uuid
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings

# 音频片段临时存放目录
AUDIO_TMP_DIR = Path("data/audio_tmp")
AUDIO_TMP_DIR.mkdir(parents=True, exist_ok=True)

# 模型单例（faster-whisper 的模型加载慢，全局只加载一份）
_model: WhisperModel | None = None
_model_lock = threading.Lock()


def _get_model() -> WhisperModel:
    """懒加载模型，首次调用时才下载/加载（进程内只做一次）"""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                device = settings.asr_device  # "auto" 会自动选择 CPU/GPU
                _model = WhisperModel(
                    settings.asr_model_size,
                    device=device,
                    compute_type=settings.asr_compute_type,
                )
    return _model


async def transcribe(audio_bytes: bytes, language: str = "zh") -> str:
    """
    把音频数据转成文字

    Args:
        audio_bytes: 音频文件内容（wav/mp3/webm 等常见格式均可）
        language: 语言代码，中文用 zh

    Returns:
        识别出的文字
    """
    # 保存到临时文件（faster-whisper 需要文件路径）
    audio_path = AUDIO_TMP_DIR / f"asr_{uuid.uuid4().hex}.wav"
    try:
        audio_path.write_bytes(audio_bytes)

        # 模型推理是 CPU/GPU 密集型操作，放到线程池避免阻塞事件循环
        model = _get_model()
        loop = asyncio.get_running_loop()
        segments, _info = await loop.run_in_executor(
            None,
            lambda: model.transcribe(
                str(audio_path),
                language=language,
                vad_filter=True,
                # 提示模型输出简体中文（base/small 模型容易输出繁体）
                initial_prompt="以下是普通话的句子，请用简体中文输出。",
                # 热词偏置：专有名词优先匹配，避免同音字错（周杰伦→周年轮）
                hotwords=settings.asr_hotwords or None,
            ),
        )

        # segments 是生成器，逐段拼接文本
        text = "".join(segment.text for segment in segments).strip()
        return text
    finally:
        # 用完即删，不堆积临时文件
        audio_path.unlink(missing_ok=True)
