# CodeGraph 索引更新记录

## 📅 更新时间
2026-05-25 19:24

## ✅ 本次更新内容

### 新增文件（3个）
1. **app/api/auth.py** - 用户认证 API 路由
   - POST /api/auth/register - 用户注册
   - POST /api/auth/login - 用户登录
   - GET /api/auth/me - 获取当前用户信息
   - POST /api/auth/logout - 用户登出

2. **app/services/auth_service.py** - 认证业务逻辑
   - AuthService.register() - 用户注册逻辑
   - AuthService.login() - 用户登录逻辑
   - AuthService.get_user_info() - 获取用户信息

3. **app/core/security.py** - 安全工具模块
   - verify_password() - 密码验证
   - get_password_hash() - 密码哈希
   - create_access_token() - JWT Token 生成
   - authenticate_user() - 用户身份验证
   - get_current_user() - 获取当前登录用户（依赖注入）
   - get_current_active_user() - 获取活跃用户

### 修改文件（4个）
1. **app/models/schemas.py** - 添加认证相关模型
   - UserRegister - 用户注册请求模型
   - UserLogin - 用户登录请求模型
   - Token - Token 响应模型
   - UserResponse - 用户信息响应模型

2. **app/db/models.py** - 扩展 User 表
   - 添加 email 字段
   - 添加 hashed_password 字段

3. **app/core/config.py** - 添加 JWT 配置
   - secret_key - JWT 密钥
   - algorithm - 加密算法（HS256）
   - access_token_expire_minutes - Token 有效期（30分钟）

4. **app/main.py** - 注册认证路由
   - 导入 auth_router
   - 注册到 FastAPI 应用

### 索引统计变化

**更新前**:
- 文件数: 22
- 节点数: 128
- 边数: 165
- 数据库大小: 0.26 MB

**更新后**:
- 文件数: 25 (+3)
- 节点数: 183 (+55)
- 边数: 243 (+78)
- 数据库大小: 0.32 MB (+0.06 MB)

### 新增节点类型分布
- import: 69 (+26) - 新增的导入语句
- class: 25 (+6) - AuthService, Token, UserRegister 等
- function: 22 (+10) - 认证相关函数
- route: 15 (+4) - 4个新的认证路由
- method: 13 (+3) - AuthService 的方法

---

## 🔍 CodeGraph 已索引的关键符号

### 认证相关类
- `AuthService` - 认证服务类
- `Token` - Token 响应模型
- `UserRegister` - 用户注册模型
- `UserLogin` - 用户登录模型
- `UserResponse` - 用户信息模型

### 认证相关函数
- `create_access_token()` - 创建 JWT Token
- `verify_password()` - 验证密码
- `get_password_hash()` - 生成密码哈希
- `authenticate_user()` - 验证用户身份
- `get_current_user()` - 获取当前用户（依赖注入）
- `get_current_active_user()` - 获取活跃用户

### 认证相关路由
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取用户信息
- `POST /api/auth/logout` - 用户登出

---

## 💡 使用示例

现在你可以用 CodeGraph 查询认证系统的各种信息：

### 1. 搜索认证相关代码
```bash
codegraph query "auth"
codegraph query "login"
codegraph query "token"
codegraph query "password"
```

### 2. 查看调用关系
```bash
# 查看谁调用了 create_access_token
codegraph callers "create_access_token"

# 查看 login 函数调用了哪些其他函数
codegraph callees "login"
```

### 3. 构建上下文
```bash
# 分析认证流程
codegraph context "分析用户认证的完整流程"

# 了解 Token 生成机制
codegraph context "JWT Token 是如何生成和验证的"

# 查看密码加密实现
codegraph context "密码是如何加密和验证的"
```

### 4. 影响分析
```bash
# 如果修改 User 模型，会影响哪些地方
codegraph impact "User"

# 修改 create_access_token 的影响
codegraph impact "create_access_token"
```

---

## 🎯 在通义灵码中使用

重启通义灵码后，你可以这样提问：

1. **"帮我分析一下认证系统的实现"**
   - CodeGraph 会返回完整的认证流程和关键代码

2. **"用户登录时发生了什么？"**
   - 会展示从 API → Service → Security 的完整调用链

3. **"JWT Token 是如何工作的？"**
   - 会解释 Token 的生成、验证和刷新机制

4. **"如果要添加邮箱验证，需要修改哪些地方？"**
   - 会列出所有相关的文件和函数

5. **"显示所有认证相关的路由"**
   - 会列出 4 个认证端点及其实现

---

## 🔄 后续更新

当你继续开发时，记得定期同步 CodeGraph 索引：

```bash
# 增量同步（推荐，速度快）
codegraph sync

# 完全重新索引（必要时使用）
codegraph init -i

# 查看状态
codegraph status
```

---

## 📊 索引健康检查

运行以下命令验证索引是否正常：

```bash
# 1. 检查状态
codegraph status

# 2. 测试搜索
codegraph query "auth"

# 3. 测试上下文构建
codegraph context "认证系统"

# 4. 运行测试脚本
./test_codegraph.sh
```

---

## ✨ 总结

CodeGraph 现在已经完整索引了你的 AI 对话小助手项目，包括：
- ✅ 原有的 6 个功能模块（chat, weather, checklist, workday, documents, news）
- ✅ 新增的用户认证系统（register, login, token validation）
- ✅ 完整的调用关系和依赖图
- ✅ 183 个代码节点，243 条关系边

这使得通义灵码能够更智能地理解你的代码，提供更准确的建议和更快的响应！🚀
