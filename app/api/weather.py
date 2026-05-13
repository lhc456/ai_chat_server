from datetime import date, timedelta
from fastapi import APIRouter, Query
from app.models.schemas import WeatherResponse, ForecastResponse, ForecastItem
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("/current", response_model=WeatherResponse, summary="查询当前天气")
async def current_weather(city: str = Query(..., description="城市名称")):
    data = await WeatherService.get_current_weather(city)
    return WeatherResponse(**data)


@router.get("/forecast", response_model=ForecastResponse, summary="查询天气预报")
async def forecast_weather(
    city: str = Query(..., description="城市名称"),
    days: int = Query(3, ge=1, le=7, description="预报天数，最多 7 天"),
):
    data = await WeatherService.get_forecast(city, days)
    forecast = [
        ForecastItem(
            date=date.fromisoformat(item["date"]),
            description=item["description"],
            high=item["high"],
            low=item["low"],
        )
        for item in data
    ]
    return ForecastResponse(city=city, forecast=forecast)
