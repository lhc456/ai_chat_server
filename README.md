# AI对话小助手 后端服务

这是一个基于 Python 的 AI 对话小助手后端项目，使用 FastAPI 构建。
当前已实现 **智能音箱式语音能力**（语音识别 + 语音合成），为软硬件结合的对话机器人提供后端支撑。

## 🎙️ 语音功能（新增）

类似天猫精灵 / 小爱音箱的对话流程：

```
录音上传 → ASR语音识别(faster-whisper) → AI分析(Ollama) → TTS语音合成(edge-tts) → 返回语音播放
           └─────────── 当前已可用 ───────────┘   └─ AI未就绪，暂时关闭 ─┘
```

**当前状态**：语音识别（ASR）和语音合成（TTS）两个基础能力已可用；
AI 对话环节（Ollama）因模型尚未准备好，已通过开关关闭（`VOICE_AI_ENABLED=false`），
准备好后在 `.env` 中改为 `true` 即可启用完整对话。

### 接口一览

#### 1. `POST /api/voice/synthesize` — 文字转语音（✅ 当前可用）

把文字合成 mp3 语音，响应体就是音频，可直接播放：

```bash
curl -X POST http://localhost:8000/api/voice/synthesize \
  -F "text=今天天气真不错" \
  -o tts.mp3
```

#### 2. `POST /api/voice/transcribe` — 语音识别（✅ 当前可用）

上传录音，返回识别出的文字（JSON）：

```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@recording.wav"
# 返回: {"text": "今天天气真不错", "elapsed_ms": 850}
```

#### 3. `POST /api/voice/interaction` — 完整语音对话（🔒 AI 就绪后开放）

录音上传 → 识别 → AI 生成回复 → 返回 mp3 语音。当前调用会返回 503 提示。

启用方法：`.env` 中设置 `VOICE_AI_ENABLED=true`，并确保 Ollama 已启动。

响应头附带文字信息：

| 响应头 | 说明 |
|--------|------|
| `X-User-Text` | 语音识别出的用户文字 |
| `X-Reply-Text` | AI 回复的文字 |
| `X-Elapsed-Ms` | 整条管线耗时（毫秒） |
| 响应体 | mp3 音频二进制（`audio/mpeg`） |

### 语音配置（`.env` 可选）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `VOICE_AI_ENABLED` | `false` | AI 对话开关，AI 就绪后改为 `true` |
| `ASR_MODEL_SIZE` | `base` | faster-whisper 模型：tiny / base / small / medium / large-v3，越大越准越慢 |
| `ASR_DEVICE` | `auto` | auto / cpu / cuda |
| `ASR_COMPUTE_TYPE` | `int8` | int8 适合 CPU，float16 适合 GPU |
| `TTS_VOICE` | `zh-CN-XiaoxiaoNeural` | edge-tts 发音人（晓晓），TTS 需要联网 |
| `TTS_RATE` | `+0%` | 语速，如 `+10%` |

> 说明：faster-whisper 首次运行会自动下载模型（约 100MB+），之后走本地缓存；服务启动时会预加载模型。

### 语音管线代码结构

| 文件 | 职责 |
|------|------|
| `app/clients/asr_client.py` | 语音识别（本地 faster-whisper） |
| `app/clients/tts_client.py` | 语音合成（edge-tts） |
| `app/services/voice_chat_service.py` | 服务编排：ASR / TTS / 完整管线 |
| `app/api/voice.py` | 语音相关接口 |

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
- `app/clients`：第三方服务调用（AI、ASR、TTS）
- `app/models`：请求和响应模型
- `app/db`：数据库配置
- `app/core`：配置管理

## 环境配置

复制 `.env.example` 为 `.env`，并填写你的 API Key：

```bash
cp .env.example .env
```

语音功能使用本地方案（faster-whisper + edge-tts），不需要额外的 API Key。

## 说明

当前后端实现了基础接口骨架，后续可逐步添加：
- 天气查询
- 出门清单生成
- 工作日判断
- AI对话能力
- 本地文档问答
- 财经新闻采集

## 🗺️ 语音机器人开发路线

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第1步 | 服务端语音对话 MVP（电脑可测，无需硬件） | ✅ 本次完成 |
| 第2步 | 对话上下文 + WebSocket 流式传输 | ⬜ |
| 第3步 | 设备端客户端（录音、播放、唤醒词） | ⬜ |
| 第4步 | LED 显示屏驱动 + 文字/表情推送协议 | ⬜ |
