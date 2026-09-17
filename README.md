# AI语音对话助手 后端服务

基于 Python + FastAPI 构建的语音对话机器人后端，为软硬件结合的对话机器人（智能音箱式交互）提供后端支撑。

**本地/局域网单用户部署**：服务运行在个人电脑或局域网设备上，无需登录认证，设备端直接调用接口即可。

```
录音上传 → ASR语音识别(faster-whisper) → AI分析(Ollama) → TTS语音合成(edge-tts) → 返回语音播放
```

## ✨ 功能一览

| 功能 | 说明 | 接口 |
|------|------|------|
| 🎙️ 语音识别（ASR） | 本地 faster-whisper 模型，上传录音返回文字 | `POST /api/voice/transcribe` |
| 🔊 语音合成（TTS） | edge-tts 中文发音人，文字合成 mp3 音频 | `POST /api/voice/synthesize` |
| ⚡ 流式语音合成 | 边合成边返回，首音延迟实测 ~1.3s（整段模式 ~1.7~2.4s）；剩余 1.3s 为 edge-tts 云端握手下限，后续可用本地引擎进一步压低 | `GET /api/voice/synthesize/stream` |
| 🤖 完整语音对话 | 录音 → 识别 → AI 回复 → 合成语音返回 | `POST /api/voice/interaction` 🔒 |
| 🌊 流式语音对话 | WebSocket：LLM 按句生成边合成边推，支持上下文连续对话 | `WS /api/voice/ws` 🔒 |
| ❤️ 健康检查 | 服务状态确认 | `GET /` |

> 🔒 `/interaction` 需要 `.env` 中设置 `VOICE_AI_ENABLED=true` 且本地 Ollama 已就绪，否则返回 503。

## 📁 项目结构

```
ai-server/
├── app/
│   ├── main.py                    # 应用入口：创建 FastAPI 实例、注册路由、启动时预加载 ASR 模型
│   │
│   ├── api/
│   │   └── voice.py               # 语音接口：TTS 合成 / ASR 识别 / 完整对话管线
│   │
│   ├── services/
│   │   └── voice_chat_service.py  # 业务编排：ASR / TTS / 完整对话管线（核心服务）
│   │
│   ├── clients/                   # 底层能力封装
│   │   ├── asr_client.py          # 语音识别：本地 faster-whisper（模型懒加载+缓存）
│   │   ├── tts_client.py          # 语音合成：edge-tts（微软云端，需联网）
│   │   └── ollama_client.py       # AI 对话：调用本地 Ollama 服务（qwen3:8b）
│   │
│   ├── models/schemas.py          # Pydantic 响应模型（语音接口的数据结构定义）
│   ├── static/voice_test.html     # 语音功能测试页面（浏览器访问 /test 打开）
│   └── core/config.py             # 配置管理：.env 读取、语音/大模型等所有配置项
│
├── requirements.txt               # Python 依赖清单
├── .env.example                   # 环境变量模板（复制为 .env 使用）
└── test_voice.sh                  # 语音功能集成测试脚本（TTS→ASR 回环测试）
```

### 请求处理链路（完整语音对话）

```
客户端上传录音
    ↓
app/api/voice.py          接收文件、校验大小、检查 AI 开关
    ↓
app/services/voice_chat_service.py   编排整条管线
    ↓
app/clients/asr_client.py     faster-whisper 本地识别出文字
    ↓
app/clients/ollama_client.py  Ollama 本地大模型生成回复
    ↓
app/clients/tts_client.py     edge-tts 合成回复语音 (mp3)
    ↓
响应：mp3 音频流 + X-User-Text / X-Reply-Text 响应头携带文字
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- macOS / Linux / Windows
- 可选：[Ollama](https://ollama.com/)（启用完整 AI 对话时需要）

### 1. 安装依赖

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate        # Windows 用: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

```bash
cp .env.example .env
```

默认配置即可运行 TTS / ASR；语音功能使用本地方案（faster-whisper + edge-tts），不需要任何 API Key。

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

看到 `Application startup complete.` 即启动成功。首次启动会预加载 ASR 模型（自动下载约 100MB+，之后走本地缓存）。

### 4. 验证服务

```bash
curl http://localhost:8000/
# {"status":"ok","message":"AI语音对话助手后端已启动"}
```

## 📖 使用方法

### 网页测试页面（推荐）

启动后用浏览器打开，可视化测试文字转语音和语音转文字：

**http://localhost:8000/test**

- 🔄 文字转语音：输入文字 → 点击按钮 → 浏览器直接播放合成的语音
- 🎤 语音转文字：点击按钮录音（浏览器授权麦克风）→ 显示识别结果，也支持上传本地音频文件

页面由服务同源托管，无需额外配置。

### 在线 API 文档

启动后打开 Swagger UI，可直接在网页上调试所有接口：

- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

### 语音接口示例

**文字转语音**（返回 mp3 音频）：

```bash
curl -X POST http://localhost:8000/api/voice/synthesize \
  -F "text=今天天气真不错" \
  -o tts.mp3
```

**流式语音合成**（边合成边返回，响应头 X-TTFB-Ms 是首音延迟）：

```bash
curl "http://localhost:8000/api/voice/synthesize/stream?text=今天天气真不错" \
  -o tts_stream.mp3 -D -
```

**语音识别**（上传录音返回文字）：

```bash
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@recording.wav"
# {"text": "今天天气真不错", "elapsed_ms": 850}
```

**流式语音对话**（WebSocket，边生成边播放，支持上下文）：

```js
const ws = new WebSocket('ws://localhost:8000/api/voice/ws');
// 上行：二进制帧 = 一段完整录音；文本帧 {"type":"reset"} 清空上下文
// 下行：{type:"user"} 识别结果 / {type:"sentence",audio_b64} 逐句语音(base64 mp3)
//       / {type:"done",text,elapsed_ms} 本轮完成 / {type:"error",message}
```

**完整语音对话**（需先启用 AI，见下文）：

```bash
curl -X POST http://localhost:8000/api/voice/interaction \
  -F "audio=@recording.wav" \
  -o reply.mp3
# 响应体: mp3 音频；响应头: X-User-Text / X-Reply-Text / X-Elapsed-Ms
```

### 运行集成测试

```bash
# 终端 1：启动服务
uvicorn app.main:app --reload --port 8000

# 终端 2：运行测试
bash test_voice.sh   # TTS 合成并播放 → ASR 回环识别 → AI 开关检查
```

> `test_voice.sh` 中途会提示按 Enter 用麦克风录音 5 秒（需要 sox 或 ffmpeg），直接按回车跳过也可以。

## ⚙️ 配置说明（.env）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `VOICE_AI_ENABLED` | `false` | AI 对话开关，Ollama 就绪后改为 `true` |
| `ASR_MODEL_SIZE` | `base` | faster-whisper 模型：tiny / base / small / medium / large-v3，越大越准越慢 |
| `ASR_DEVICE` | `auto` | auto / cpu / cuda |
| `ASR_COMPUTE_TYPE` | `int8` | int8 适合 CPU，float16 适合 GPU |
| `TTS_VOICE` | `zh-CN-XiaoyiNeural` | edge-tts 发音人（晓伊，活泼自然），TTS 需要联网；备选 YunxiNeural / YunxiaNeural / XiaoxiaoNeural |
| `TTS_RATE` | `+10%` | 语速，微快更像日常对话 |
| `TTS_PITCH` | `+5Hz` | 音调微调，轻快一些；`+0Hz` 恢复默认 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `OLLAMA_MODEL` | `qwen3:8b` | 使用的本地大模型 |

## 🔓 启用完整 AI 语音对话

1. 安装并启动 [Ollama](https://ollama.com/)，拉取模型：

   ```bash
   ollama pull qwen3:8b
   ollama serve
   ```

2. 编辑 `.env`：

   ```
   VOICE_AI_ENABLED=true
   ```

3. 重启服务，`POST /api/voice/interaction` 即可正常工作（不再返回 503）。

## 🗺️ 开发路线

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第1步 | 服务端语音对话 MVP（电脑可测，无需硬件） | ✅ 已完成 |
| 第2步 | 对话上下文 + WebSocket 流式传输（按句边生成边播） | ✅ 已完成 |
| 第3步 | 设备端客户端（录音、播放、唤醒词，ESP32 走同一 WS 协议） | ⬜ |
| 第4步 | LED 显示屏驱动 + 文字/表情推送协议 | ⬜ |
