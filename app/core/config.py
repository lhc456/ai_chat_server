from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI语音对话助手后端"
    debug: bool = True
    # Ollama 本地大模型配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"          # 本机已拉取的模型
    ollama_keep_alive: str = "30m"        # 模型在内存中的保活时长，避免频繁冷启动（首次加载要 ~20s）
    # 天气工具
    default_city: str = "杭州"             # 问天气没说城市且无定位时的默认城市
    # 语音对话配置
    voice_ai_enabled: bool = False        # AI对话开关：AI就绪前先关闭，只开放 TTS/ASR 两个基础功能
    asr_model_size: str = "base"          # faster-whisper 模型: tiny/base/small/medium/large-v3
    asr_device: str = "auto"              # auto / cpu / cuda
    asr_compute_type: str = "int8"        # int8 适合CPU，float16 适合GPU
    tts_voice: str = "zh-CN-XiaoxiaoNeural"   # edge-tts 发音人：晓晓（自然耐听，实测用户反馈好于晓伊）；备选 YunxiNeural/YunxiaNeural
    tts_rate: str = "+0%"                 # 语速：+0% 最自然；调太快容易显得赶
    tts_pitch: str = "+0Hz"               # 音调：+0Hz 默认；晓伊等音色调高会显得假

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
