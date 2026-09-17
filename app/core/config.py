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
    tts_voice: str = "zh-CN-XiaoyiNeural"     # edge-tts 发音人：晓伊（活泼自然，比晓晓少播音腔）；备选 YunxiNeural/YunxiaNeural
    tts_rate: str = "+10%"                # 语速：微快一点更接近日常对话，+0% 偏新闻播报感
    tts_pitch: str = "+5Hz"               # 音调：微调让声音更轻快；也可用 "+0Hz" 恢复默认

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
