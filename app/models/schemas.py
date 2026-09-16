from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=128, description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码（至少6位）")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户唯一标识")
    message: str = Field(..., description="用户输入消息")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="助手回复内容")


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


class ForecastItem(BaseModel):
    date: date
    description: str = Field(..., description="天气描述")
    high: float = Field(..., description="最高温度")
    low: float = Field(..., description="最低温度")


class WeatherResponse(BaseModel):
    city: str = Field(..., description="城市名称")
    temperature: float = Field(..., description="当前温度")
    humidity: int = Field(..., description="湿度百分比")
    wind_speed: float = Field(..., description="风速")
    description: str = Field(..., description="天气描述")
    advice: str = Field(..., description="出行建议")


class ForecastResponse(BaseModel):
    city: str = Field(..., description="城市名称")
    forecast: List[ForecastItem]


class ChecklistRequest(BaseModel):
    city: str = Field(..., description="城市名称")
    date: date
    purpose: str = Field(..., description="出行目的，如上班/旅游/购物")
    additional: Optional[str] = Field(None, description="补充说明，例如特殊需求")


class ChecklistResponse(BaseModel):
    items: List[str]


class WorkdayResponse(BaseModel):
    date: date
    is_workday: bool = Field(..., description="是否为工作日")
    holiday_name: Optional[str] = Field(
        None, description="节假日名称，如果不是工作日则返回"
    )
    note: str = Field(..., description="简要说明")
