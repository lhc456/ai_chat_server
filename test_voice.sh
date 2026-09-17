#!/bin/bash

echo "🎙️  测试语音功能（TTS / ASR）"
echo "============================="
echo ""

BASE_URL="http://localhost:8000/api/voice"
TMP_DIR=$(mktemp -d)

# 0. 检查服务是否运行
echo "0️⃣  检查服务状态..."
if ! curl -s -m 5 http://localhost:8000/ > /dev/null; then
    echo "❌ 服务未启动，请先运行:"
    echo "   uvicorn app.main:app --reload --port 8000"
    exit 1
fi
echo "✅ 服务运行中"
echo ""

# 1. 文字转语音（TTS）
echo "1️⃣  测试文字转语音（TTS）..."
TTS_TEXT="你好，我是你的语音助手，欢迎使用语音对话功能"
HTTP_CODE=$(curl -s -m 60 -X POST "$BASE_URL/synthesize" \
  -F "text=$TTS_TEXT" \
  -o "$TMP_DIR/tts.mp3" \
  -w "%{http_code}")

if [ "$HTTP_CODE" = "200" ] && [ -s "$TMP_DIR/tts.mp3" ]; then
    SIZE=$(du -k "$TMP_DIR/tts.mp3" | cut -f1)
    echo "✅ TTS 成功，音频已保存: $TMP_DIR/tts.mp3 (${SIZE}KB)"
    # macOS 可以直接播放听效果
    if command -v afplay > /dev/null; then
        echo "🔊 播放合成的语音..."
        afplay "$TMP_DIR/tts.mp3"
    fi
else
    echo "❌ TTS 失败 (HTTP $HTTP_CODE)"
    cat "$TMP_DIR/tts.mp3" 2>/dev/null
fi
echo ""

# 2. 语音识别（ASR）—— 用 TTS 生成的音频做回环测试
echo "2️⃣  测试语音识别（ASR）..."
ASR_RESPONSE=$(curl -s -m 120 -X POST "$BASE_URL/transcribe" \
  -F "audio=@$TMP_DIR/tts.mp3")
echo "识别响应: $ASR_RESPONSE"

if echo "$ASR_RESPONSE" | grep -q "text"; then
    echo "✅ ASR 成功"
    # 显示识别出的文字
    echo "$ASR_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'   识别文字: {d[\"text\"]}'); print(f'   耗时: {d[\"elapsed_ms\"]}ms')" 2>/dev/null
else
    echo "❌ ASR 失败"
fi
echo ""

# 3. 用自己的录音测试（可选）
echo "3️⃣  用自己的录音测试 ASR（可选）..."
RECORD_FILE="$TMP_DIR/my_recording.wav"
if command -v sox > /dev/null; then
    echo "🎤 按 Enter 后开始录音 5 秒（对着麦克风说点什么）..."
    read
    rec -q "$RECORD_FILE" trim 0 5 2>/dev/null
    ASR_RESPONSE=$(curl -s -m 120 -X POST "$BASE_URL/transcribe" \
      -F "audio=@$RECORD_FILE")
    echo "识别结果: $ASR_RESPONSE"
elif command -v ffmpeg > /dev/null; then
    echo "🎤 按 Enter 后开始录音 5 秒（对着麦克风说点什么）..."
    read
    ffmpeg -y -f avfoundation -i ":0" -t 5 "$RECORD_FILE" 2>/dev/null
    ASR_RESPONSE=$(curl -s -m 120 -X POST "$BASE_URL/transcribe" \
      -F "audio=@$RECORD_FILE")
    echo "识别结果: $ASR_RESPONSE"
else
    echo "⏭️  跳过（未安装 sox 或 ffmpeg，可手动上传录音文件测试）"
    echo "   手动测试: curl -X POST $BASE_URL/transcribe -F \"audio=@你的录音.wav\""
fi
echo ""

# 4. 测试 AI 对话接口（当前应返回 503）
echo "4️⃣  测试 AI 对话接口（当前应被开关拦截）..."
AI_RESPONSE=$(curl -s -m 30 -X POST "$BASE_URL/interaction" \
  -F "audio=@$TMP_DIR/tts.mp3")
HTTP_CODE=$(curl -s -o /dev/null -m 30 -w "%{http_code}" -X POST "$BASE_URL/interaction" \
  -F "audio=@$TMP_DIR/tts.mp3")

if [ "$HTTP_CODE" = "503" ]; then
    echo "✅ AI 开关生效（HTTP $HTTP_CODE）: $AI_RESPONSE"
else
    echo "⚠️  预期 503，实际 $HTTP_CODE: $AI_RESPONSE"
fi
echo ""

# 清理临时文件
rm -rf "$TMP_DIR"

echo "============================="
echo "✅ 语音功能测试完成！"
echo ""
echo "📝 更多测试方式："
echo "   1. Swagger UI 在线测试: http://localhost:8000/docs （找 voice 标签）"
echo "   2. 手动测试 TTS: curl -X POST $BASE_URL/synthesize -F \"text=你好\" -o out.mp3"
echo "   3. 手动测试 ASR: curl -X POST $BASE_URL/transcribe -F \"audio=@录音文件\""
