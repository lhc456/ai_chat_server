from datetime import date
from fastapi import APIRouter, Query
from app.models.schemas import WorkdayResponse
from app.services.workday_service import WorkdayService

router = APIRouter()


@router.get("/today", response_model=WorkdayResponse, summary="查询今天是否为工作日")
async def today_workday():
    result = await WorkdayService.is_workday(date.today())
    return WorkdayResponse(**result)


@router.get(
    "/check", response_model=WorkdayResponse, summary="查询指定日期是否为工作日"
)
async def check_workday(
    date: date = Query(..., description="查询日期，例如 2026-05-13")
):
    result = await WorkdayService.is_workday(date)
    return WorkdayResponse(**result)
