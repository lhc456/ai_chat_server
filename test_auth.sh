#!/bin/bash

echo "🔐 测试用户认证系统"
echo "===================="
echo ""

BASE_URL="http://localhost:8000/api"

# 1. 注册用户
echo "1️⃣  注册新用户..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456"
  }')

echo "注册响应:"
echo "$REGISTER_RESPONSE" | python3 -m json.tool
echo ""

# 检查是否成功
if echo "$REGISTER_RESPONSE" | grep -q "username"; then
    echo "✅ 注册成功"
else
    echo "❌ 注册失败"
    exit 1
fi
echo ""

# 2. 用户登录
echo "2️⃣  用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "123456"
  }')

echo "登录响应:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# 提取 Token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -n "$TOKEN" ]; then
    echo "✅ 登录成功，获取到 Token"
    echo "Token: ${TOKEN:0:50}..."
else
    echo "❌ 登录失败"
    exit 1
fi
echo ""

# 3. 获取当前用户信息
echo "3️⃣  获取当前用户信息（使用 Token）..."
USER_INFO=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

echo "用户信息:"
echo "$USER_INFO" | python3 -m json.tool
echo ""

if echo "$USER_INFO" | grep -q "testuser"; then
    echo "✅ 成功获取用户信息"
else
    echo "❌ 获取用户信息失败"
    exit 1
fi
echo ""

# 4. 测试无效 Token
echo "4️⃣  测试无效 Token..."
INVALID_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer invalid_token_12345")

echo "无效 Token 响应:"
echo "$INVALID_RESPONSE" | python3 -m json.tool
echo ""

if echo "$INVALID_RESPONSE" | grep -q "401\|invalid"; then
    echo "✅ 正确拒绝了无效 Token"
else
    echo "⚠️  未正确拒绝无效 Token"
fi
echo ""

# 5. 测试重复注册
echo "5️⃣  测试重复注册..."
DUPLICATE_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "123456"
  }')

echo "重复注册响应:"
echo "$DUPLICATE_RESPONSE" | python3 -m json.tool
echo ""

if echo "$DUPLICATE_RESPONSE" | grep -q "400\|已存在"; then
    echo "✅ 正确拒绝了重复注册"
else
    echo "⚠️  未正确拒绝重复注册"
fi
echo ""

# 6. 测试错误密码
echo "6️⃣  测试错误密码登录..."
WRONG_PASSWORD_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "wrong_password"
  }')

echo "错误密码响应:"
echo "$WRONG_PASSWORD_RESPONSE" | python3 -m json.tool
echo ""

if echo "$WRONG_PASSWORD_RESPONSE" | grep -q "401\|错误"; then
    echo "✅ 正确拒绝了错误密码"
else
    echo "⚠️  未正确拒绝错误密码"
fi
echo ""

echo "===================="
echo "✅ 所有测试完成！"
echo ""
echo "📝 使用说明："
echo "   1. 启动服务: uvicorn app.main:app --reload"
echo "   2. 访问 API 文档: http://localhost:8000/docs"
echo "   3. 在 /api/auth/register 注册用户"
echo "   4. 在 /api/auth/login 登录获取 Token"
echo "   5. 在其他接口使用 Token: Authorization: Bearer <token>"
