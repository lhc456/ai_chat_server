# AI对话小助手后端设计文档

## 1. 设计目标

本后端设计基于你已有的产品需求，目标是：
- 以Python构建可靠、可扩展、易维护的接口层
- 为前端提供对话式AI能力、天气查询、出门清单、工作日判断等服务
- 留出本地文档问答、财经新闻搜集等后续扩展接口
- 使用模块化、清晰的架构，便于后续迭代和功能扩展

## 2. 技术栈建议

- Python版本：3.10+ 或 3.11+
- Web框架：FastAPI（推荐）
- 异步HTTP客户端：httpx / aiohttp
- 数据库：SQLite（开发阶段）/ PostgreSQL（生产推荐）
- ORM：SQLAlchemy + Pydantic
- 定时任务：APScheduler / Celery（后期扩展）
- AI能力：OpenAI API、Azure OpenAI、或本地大模型接口
- 文档向量搜索：FAISS / Weaviate / Chroma（本地文档功能）
- 部署：Docker / Uvicorn + Gunicorn

## 3. 系统架构

后端分为三层：
- API 层：接收前端请求并返回结果
- 业务层：处理对话逻辑、天气查询、清单生成、工作日判断等
- 数据层：存储用户配置、历史记录、文档索引、新闻缓存

### 3.1 核心模块

- `app.main`：FastAPI 应用入口
- `app.api`：路由与接口定义
- `app.services`：业务服务实现
- `app.models`：Pydantic 数据模型
- `app.db`：数据库连接与ORM模型
- `app.clients`：第三方API调用封装
- `app.tasks`：定时任务与异步任务管理
- `app.utils`：通用工具函数

## 4. API 设计

### 4.1 基础对话接口

- `POST /api/chat`：发送用户消息，返回AI助手回复
  - 请求体：`{ "user_id": "xxx", "message": "今天要带什么？" }`
  - 返回：`{ "reply": "根据天气，你需要带雨伞……" }`

### 4.2 天气查询接口

- `GET /api/weather/current?city=Beijing`
- `GET /api/weather/forecast?city=Beijing&days=3`

返回内容：城市、温度、湿度、风速、天气描述、建议

### 4.3 出门清单接口

- `POST /api/checklist`
  - 请求体：`{ "city": "Beijing", "date": "2026-05-13", "purpose": "上班" }`
  - 返回：`{ "items": ["雨伞", "口罩", "钥匙"] }`

### 4.4 工作日判断接口

- `GET /api/workday/today`
- `GET /api/workday/check?date=2026-06-01`

返回内容：是否工作日、节假日名称、说明

### 4.5 文档上传与问答接口（后期扩展）

- `POST /api/documents/upload`
- `POST /api/documents/query`

返回：文档摘要、问题回答、匹配段落

### 4.6 新闻搜集接口（后期扩展）

- `GET /api/news/finance/today`
- `GET /api/news/broadcast/today`

返回：摘要、热点列表、链接

## 5. 数据模型设计

### 5.1 用户与会话

- `User`：`id`, `name`, `created_at`, `settings`
- `ChatSession`：`id`, `user_id`, `message`, `reply`, `timestamp`

### 5.2 配置与缓存

- `WeatherCache`：最近天气查询结果缓存
- `DocumentMeta`：已上传文档元信息
- `NewsCache`：每日财经/新闻摘要缓存

### 5.3 文档索引（后期）

- `DocumentSegment`：文档分段内容、向量向量ID、元数据

## 6. 模块详细设计

### 6.1 API 层

使用FastAPI定义REST接口，自动生成OpenAPI文档。

- `app/api/chat.py`
- `app/api/weather.py`
- `app/api/checklist.py`
- `app/api/workday.py`
- `app/api/documents.py`
- `app/api/news.py`

### 6.2 服务层

- `ChatService`：处理对话逻辑、上下文管理、模型调用
- `WeatherService`：封装天气API调用、缓存策略
- `ChecklistService`：基于天气和出行目的生成清单
- `WorkdayService`：判断节假日、工作日逻辑
- `DocumentService`：文档上传、文本抽取、问答
- `NewsService`：财经新闻抓取与摘要

### 6.3 第三方客户端

- `WeatherClient`：调用OpenWeatherMap/和风天气API
- `AIClient`：调用GPT或大模型接口
- `NewsClient`：抓取或调用新闻API
- `HolidayClient`：判断法定节假日，可使用本地库或第三方API

### 6.4 任务与定时调度

- 定时任务：每天自动更新财经新闻、新闻联播摘要
- 可选实现：Celery + Redis 或 APScheduler

## 7. 局部示例流程

### 7.1 天气查询流程

1. 前端调用 `GET /api/weather/current?city=Beijing`
2. `WeatherService` 查询缓存
3. 如果缓存失效，`WeatherClient` 请求天气API
4. 服务层返回标准结果给前端

### 7.2 出门清单生成流程

1. 前端调用 `POST /api/checklist`
2. `ChecklistService` 获取当天天气
3. 结合出行目的、日期生成建议清单
4. 返回清单到前端

### 7.3 工作日判断流程

1. 前端调用 `GET /api/workday/check?date=2026-06-01`
2. `WorkdayService` 调用节假日判断函数
3. 返回是否工作日和备注

## 8. 安全与配置

- 敏感配置使用环境变量存储：API Key、模型Key、数据库URL
- 使用HTTPS部署（生产环境）
- 对接口加基础身份验证或令牌验证
- 限制第三方API请求频率，防止滥用

## 9. 扩展与迭代建议

- 后期将`DocumentService`与向量数据库结合，实现语义检索
- `NewsService`可加入多源抓取与关键词订阅
- `ChatService`增加用户身份、会话记忆、个性化回复
- 将核心模块拆分为独立服务（微服务）以提升可维护性

## 10. 交付成果

- FastAPI 后端应用
- API 文档与接口说明
- 模块化业务层与可插拔服务
- 可扩展的本地文档问答与新闻采集入口

---

文件路径：`backend_design.md`

这个设计文档已经为你后端开发提供清晰方向。你可以直接在此基础上开始搭建FastAPI项目结构，并逐步实现核心功能。