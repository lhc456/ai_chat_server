# 用户认证系统使用指南

## ✅ 已完成的功能

### 1. 用户注册
- **接口**: `POST /api/auth/register`
- **功能**: 创建新用户账号
- **参数**:
  - `username`: 用户名（3-128个字符，必填）
  - `email`: 邮箱地址（可选）
  - `password`: 密码（至少6位，必填）
- **返回**: 用户信息

### 2. 用户登录
- **接口**: `POST /api/auth/login`
- **功能**: 验证用户名密码，返回 JWT Token
- **参数**:
  - `username`: 用户名
  - `password`: 密码
- **返回**: 
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

### 3. 获取当前用户信息
- **接口**: `GET /api/auth/me`
- **功能**: 获取当前登录用户的详细信息
- **需要**: Authorization Header
  ```
  Authorization: Bearer <your_token>
  ```
- **返回**: 用户信息（id, username, email, is_active）

### 4. 用户登出
- **接口**: `POST /api/auth/logout`
- **功能**: 用户登出（客户端删除 Token 即可）
- **说明**: 由于使用 JWT，服务端无需额外操作

---

## 🔧 技术实现

### 使用的库
- **python-jose**: JWT Token 生成和验证
- **passlib[bcrypt]**: 密码加密（bcrypt 算法）
- **OAuth2PasswordBearer**: FastAPI 内置的 OAuth2 认证方案

### 安全特性
1. **密码加密**: 使用 bcrypt 算法，不可逆
2. **JWT Token**: 无状态认证，有效期 30 分钟
3. **Token 验证**: 每次请求自动验证 Token 有效性
4. **用户隔离**: 每个用户有独立的 ID 和数据

### 数据库变更
- `User` 表新增字段:
  - `email`: 邮箱地址（可选）
  - `hashed_password`: 加密后的密码（必填）

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
uvicorn app.main:app --reload
```

### 3. 访问 API 文档
打开浏览器访问: http://localhost:8000/docs

### 4. 测试流程

#### 步骤 1: 注册用户
在 Swagger UI 中找到 `/api/auth/register` 接口，点击 "Try it out"，填写：
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "123456"
}
```
点击 "Execute"，应该看到成功响应。

#### 步骤 2: 登录获取 Token
找到 `/api/auth/login` 接口，填写：
```json
{
  "username": "testuser",
  "password": "123456"
}
```
点击 "Execute"，会返回 access_token。

#### 步骤 3: 使用 Token 访问受保护的接口
找到 `/api/auth/me` 接口，点击 "Authorize" 按钮，输入：
```
Bearer <你的token>
```
然后点击 "Execute"，应该能看到当前用户信息。

---

## 📝 代码示例

### Python 示例（使用 requests）

```python
import requests

BASE_URL = "http://localhost:8000/api"

# 1. 注册用户
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "123456"
})
print("注册结果:", response.json())

# 2. 登录获取 Token
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "testuser",
    "password": "123456"
})
token = response.json()["access_token"]
print("Token:", token)

# 3. 使用 Token 访问受保护的接口
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print("用户信息:", response.json())
```

### cURL 示例

```bash
# 注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"123456"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"123456"}'

# 使用 Token 访问
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🔐 如何在其他接口中使用认证

### 方法 1: 添加依赖注入（推荐）

修改需要认证的接口，添加 `current_user` 参数：

```python
from fastapi import Depends
from app.core.security import get_current_active_user
from app.db.models import User

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)  # 新增
):
    # current_user 就是当前登录的用户
    print(f"用户 {current_user.username} 发送了消息")
    
    # 使用 current_user.id 替代 request.user_id
    reply = await ChatService.create_reply(request, current_user.id)
    return ChatResponse(reply=reply)
```

### 方法 2: 手动验证 Token

```python
from fastapi import Header, HTTPException
from app.core.security import get_current_user

@router.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(...)
):
    # 从 Header 中提取 Token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证方式")
    
    token = authorization.split(" ")[1]
    
    # 验证 Token（需要修改 get_current_user 以接受直接传入的 token）
    # ...
```

---

## 🧪 运行测试脚本

```bash
# 先启动服务
uvicorn app.main:app --reload

# 在另一个终端运行测试
chmod +x test_auth.sh
./test_auth.sh
```

测试脚本会自动执行：
1. ✅ 注册用户
2. ✅ 用户登录
3. ✅ 获取用户信息
4. ✅ 测试无效 Token
5. ✅ 测试重复注册
6. ✅ 测试错误密码

---

## ⚠️ 注意事项

### 1. 生产环境配置
在生产环境中，应该从环境变量读取 `SECRET_KEY`：

```python
# .env 文件
SECRET_KEY=your-super-secret-key-here

# config.py
secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
```

### 2. Token 有效期
当前设置为 30 分钟，可以在 `config.py` 中修改：
```python
access_token_expire_minutes: int = 60  # 改为 60 分钟
```

### 3. 密码强度
当前只要求最少 6 位，建议增加密码强度验证：
```python
class UserRegister(BaseModel):
    password: str = Field(..., min_length=8, description="密码（至少8位，包含大小写字母和数字）")
```

### 4. HTTPS
生产环境必须使用 HTTPS，否则 Token 可能被窃听。

---

## 📊 项目结构

```
app/
├── api/
│   └── auth.py              # 认证相关接口 ✨ 新增
├── services/
│   └── auth_service.py      # 认证业务逻辑 ✨ 新增
├── core/
│   ├── security.py          # 安全工具（JWT、密码加密）✨ 新增
│   └── config.py            # 配置（添加了 JWT 配置）✏️ 修改
├── models/
│   └── schemas.py           # 数据模型（添加了认证相关模型）✏️ 修改
└── db/
    └── models.py            # 数据库模型（User 表添加了密码字段）✏️ 修改
```

---

## 🎯 下一步建议

### 短期（必做）
1. ✅ ~~实现基本的注册登录~~ 已完成
2. ⏳ 为现有接口添加认证保护（chat、weather 等）
3. ⏳ 实现对话历史查询（基于 user_id）

### 中期（选做）
4. 实现密码找回功能（通过邮箱）
5. 添加用户资料编辑功能
6. 实现 Token 刷新机制

### 长期（进阶）
7. 添加角色权限系统（管理员、普通用户）
8. 实现第三方登录（微信、GitHub）
9. 添加登录日志和安全审计

---

## 💡 常见问题

### Q: Token 过期了怎么办？
A: 重新登录获取新的 Token。后续可以实现 refresh token 机制。

### Q: 如何修改 Token 有效期？
A: 修改 `app/core/config.py` 中的 `access_token_expire_minutes`。

### Q: 忘记密码怎么办？
A: 当前版本不支持密码找回，需要删除用户后重新注册。后续可以添加邮箱验证和密码重置功能。

### Q: 如何查看数据库中保存的密码？
A: 密码使用 bcrypt 加密，无法解密。这是正常的安全设计。

### Q: 多个用户可以同时登录吗？
A: 可以，JWT 是无状态的，每个 Token 独立有效。

---

## 📚 参考资料

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [bcrypt 密码加密](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html)
