from fastapi import APIRouter

router = APIRouter()


@router.get("/finance/today", summary="获取当天财经新闻摘要")
async def finance_news_today():
    return {
        "date": "2026-05-13",
        "headline": "今日财经热点汇总（占位）",
        "items": [
            {"title": "市场概况", "summary": "股市稳中有升，科技股领涨。"},
            {"title": "宏观政策", "summary": "央行维持利率不变。"},
        ],
    }


@router.get("/broadcast/today", summary="获取当日新闻联播摘要")
async def broadcast_news_today():
    return {
        "date": "2026-05-13",
        "headline": "新闻联播要点（占位）",
        "items": [
            {"title": "要闻一", "summary": "重要政策发布。"},
            {"title": "要闻二", "summary": "经济形势分析。"},
        ],
    }
