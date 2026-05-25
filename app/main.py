from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.weather import router as weather_router
from app.api.checklist import router as checklist_router
from app.api.workday import router as workday_router
from app.api.documents import router as documents_router
from app.api.news import router as news_router

app = FastAPI(
    title="AI对话小助手后端",
    description="Python FastAPI 后端服务，提供天气查询、出门清单、工作日判断等接口。",
    version="0.1.0",
)

# 认证相关路由（无需登录即可访问）
app.include_router(auth_router, prefix="/api", tags=["authentication"])

# 业务功能路由（后续可以添加认证保护）
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(weather_router, prefix="/api/weather", tags=["weather"])
app.include_router(
    checklist_router, prefix="/api/checklist", tags=["checklist"])
app.include_router(workday_router, prefix="/api/workday", tags=["workday"])
app.include_router(
    documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(news_router, prefix="/api/news", tags=["news"])


@app.get("/", summary="服务健康检查")
async def root():
    return {"status": "ok", "message": "AI对话小助手后端已启动"}
