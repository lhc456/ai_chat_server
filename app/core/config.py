from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI语音对话助手后端"
    debug: bool = True
    # Ollama 本地大模型配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"          # 本机已拉取的模型
    # 语音对话配置
    voice_ai_enabled: bool = False        # AI对话开关：AI就绪前先关闭，只开放 TTS/ASR 两个基础功能
    asr_model_size: str = "base"          # faster-whisper 模型: tiny/base/small/medium/large-v3
    asr_device: str = "auto"              # auto / cpu / cuda
    asr_compute_type: str = "int8"        # int8 适合CPU，float16 适合GPU
    tts_voice: str = "zh-CN-XiaoxiaoNeural"   # edge-tts 中文语音（晓晓）
    tts_rate: str = "+0%"                 # 语速，如 "+10%"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
