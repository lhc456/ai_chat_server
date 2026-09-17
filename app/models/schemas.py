from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    """语音识别响应"""
    text: str = Field(..., description="识别出的文字")
    elapsed_ms: int = Field(..., description="耗时（毫秒）")


class SynthesizeResponse(BaseModel):
    """语音合成响应（JSON 部分，音频以 mp3 二进制单独返回）"""
    audio: bytes = Field(..., description="合成语音（mp3 二进制）")
    elapsed_ms: int = Field(..., description="耗时（毫秒）")


class VoiceChatResponse(BaseModel):
    """语音对话响应（/api/voice/interaction 返回的 JSON 部分）"""
    user_text: str = Field(..., description="语音识别出的用户文字")
    reply_text: str = Field(..., description="AI 回复文字")
    audio: bytes = Field(..., description="AI 回复语音（mp3 二进制）")
    elapsed_ms: int = Field(..., description="整条管线耗时（毫秒）")
