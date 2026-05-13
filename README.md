# AI对话小助手 后端服务

这是一个基于 Python 的 AI 对话小助手后端项目，使用 FastAPI 构建。

## 快速开始

1. 创建 Python 虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 运行后端服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 打开 API 文档

- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## 项目结构

- `app/main.py`：FastAPI 应用入口
- `app/api`：路由接口
- `app/services`：业务逻辑实现
- `app/clients`：第三方服务调用
- `app/models`：请求和响应模型
- `app/db`：数据库配置
- `app/core`：配置管理

## 环境配置

复制 `.env.example` 为 `.env`，并填写你的 API Key：

```bash
cp .env.example .env
```

## 说明

当前后端实现了基础接口骨架，后续可逐步添加：
- 天气查询
- 出门清单生成
- 工作日判断
- AI对话能力
- 本地文档问答
- 财经新闻采集
# ai_chat_server
