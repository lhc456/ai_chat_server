from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户唯一标识")
    message: str = Field(..., description="用户输入消息")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="助手回复内容")


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
