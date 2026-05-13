from app.core.config import settings


class WeatherService:
    @staticmethod
    async def get_current_weather(city: str) -> dict:
        # TODO: 使用 WeatherClient 获取真实天气数据
        return {
            "city": city,
            "temperature": 23.5,
            "humidity": 55,
            "wind_speed": 4.2,
            "description": "多云",
            "advice": "天气适宜，建议携带薄外套。",
        }

    @staticmethod
    async def get_forecast(city: str, days: int) -> list[dict]:
        # TODO: 使用 WeatherClient 获取真实天气预报数据
        return [
            {
                "date": f"2026-05-{13 + i}",
                "description": "晴转多云",
                "high": 25.0 + i,
                "low": 16.0 + i,
            }
            for i in range(days)
        ]
