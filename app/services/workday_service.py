from datetime import date


class WorkdayService:
    @staticmethod
    async def is_workday(check_date: date) -> dict:
        # TODO: 这里可以接入节假日 API 或本地节假日规则库
        weekday = check_date.weekday()
        is_workday = weekday < 5
        return {
            "date": check_date,
            "is_workday": is_workday,
            "holiday_name": None if is_workday else "周末",
            "note": "工作日" if is_workday else "休息日",
        }
