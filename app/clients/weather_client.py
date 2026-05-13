import httpx
from app.core.config import settings


class WeatherClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    @classmethod
    async def fetch_current(cls, city: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{cls.BASE_URL}/weather",
                params={
                    "q": city,
                    "appid": settings.weather_api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            )
            response.raise_for_status()
            return response.json()

    @classmethod
    async def fetch_forecast(cls, city: str, days: int) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{cls.BASE_URL}/forecast",
                params={
                    "q": city,
                    "appid": settings.weather_api_key,
                    "units": "metric",
                    "lang": "zh_cn",
                },
            )
            response.raise_for_status()
            return response.json()
