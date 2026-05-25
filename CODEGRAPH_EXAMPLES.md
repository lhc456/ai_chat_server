# CodeGraph 使用示例

## 🎯 在通义灵码中的实际使用场景

### 场景 1: 理解代码结构

**提问**: "这个项目的整体架构是怎样的？主要模块有哪些？"

**CodeGraph 会提供**:
- 项目文件结构
- 主要模块列表
- 模块间的依赖关系

---

### 场景 2: 追踪函数调用

**提问**: "`chat_service.py` 中的 `create_reply` 方法被哪些地方调用了？"

**CodeGraph 会提供**:
- 所有调用 `create_reply` 的位置
- 调用链路径
- 相关代码片段

---

### 场景 3: 分析影响范围

**提问**: "如果我修改了 `WeatherService`，会影响哪些模块？"

**CodeGraph 会提供**:
- 直接依赖 `WeatherService` 的模块
- 间接影响的模块
- 可能需要修改的测试文件

---

### 场景 4: 快速定位代码

**提问**: "项目中有哪些 API 路由？它们分别对应哪些处理函数？"

**CodeGraph 会提供**:
- 所有路由列表（11 个路由）
- 每个路由对应的处理函数
- 路由所在的文件位置

---

### 场景 5: 理解数据库模型

**提问**: "这个项目使用了哪些数据库模型？它们之间有什么关系？"

**CodeGraph 会提供**:
- 所有模型类列表
- 模型间的关联关系
- 字段定义

---

## 💻 命令行使用示例

### 1. 查看项目状态
```bash
cd /Users/lihanchao/Documents/other/ai-server
codegraph status
```

输出示例：
```
CodeGraph Status

Project: /Users/lihanchao/Documents/other/ai-server

Index Statistics:
  Files:     22
  Nodes:     128
  Edges:     165
  DB Size:   0.26 MB

Nodes by Kind:
  import          43
  file            22
  class           19
  function        12
  route           11
  variable        11
  method          10
```

---

### 2. 搜索特定符号
```bash
# 搜索包含 "weather" 的符号
codegraph query "weather"

# 搜索包含 "database" 或 "db" 的符号
codegraph query "database"
```

---

### 3. 查找调用关系
```bash
# 查找谁调用了 ChatService
codegraph callers "ChatService"

# 查找 chat 函数调用了哪些其他函数
codegraph callees "chat"
```

---

### 4. 影响分析
```bash
# 分析修改 create_reply 方法的影响
codegraph impact "create_reply"
```

---

### 5. 查看文件结构
```bash
# 查看所有文件
codegraph files

# 只查看 Python 文件
codegraph files --pattern "*.py"

# 查看 app/api 目录下的文件
codegraph files --path "app/api"
```

---

### 6. 构建上下文（适合 AI 助手）
```bash
# 为某个任务构建完整的上下文
codegraph context "帮我实现一个新的新闻采集功能"

# 输出会是 markdown 格式，包含：
# - 相关文件列表
# - 现有类似功能的实现
# - 需要修改的模块
# - 建议的实现步骤
```

---

## 🚀 实际工作流示例

### 示例 1: 添加新功能

假设你要添加一个"股票查询"功能：

1. **先了解现有结构**
   ```bash
   codegraph context "分析现有的 weather 和 news 功能是如何实现的"
   ```

2. **查看类似的 API 路由**
   ```bash
   codegraph query "route"
   ```

3. **了解服务层的模式**
   ```bash
   codegraph context "weather_service 和 news_service 的实现模式"
   ```

4. **在通义灵码中提问**
   ```
   "基于现有的 weather 和 news 功能模式，帮我设计一个 stock 查询功能"
   ```

---

### 示例 2: 重构代码

假设你要重构 `chat_service.py`：

1. **分析当前使用情况**
   ```bash
   codegraph callers "ChatService"
   codegraph impact "create_reply"
   ```

2. **了解依赖关系**
   ```bash
   codegraph callees "ChatService"
   ```

3. **在通义灵码中提问**
   ```
   "我要重构 ChatService，列出所有可能受影响的地方和需要注意的事项"
   ```

---

### 示例 3: Debug 问题

假设聊天功能出现问题：

1. **定位相关代码**
   ```bash
   codegraph query "chat"
   ```

2. **追踪调用链**
   ```bash
   codegraph context "从 API 路由到最终响应的完整调用链"
   ```

3. **在通义灵码中提问**
   ```
   "帮我分析 chat API 的完整执行流程，从请求进入到响应返回"
   ```

---

## 📊 你的项目特有信息

根据你的 `ai-server` 项目，以下是一些特别有用的查询：

### 查看所有 API 路由
```bash
codegraph query "route"
```
你会看到 11 个路由，包括：
- POST /api/chat
- GET /api/weather
- POST /api/checklist
- GET /api/workday
- 等等...

### 查看服务层结构
```bash
codegraph query "Service"
```
你会看到：
- ChatService
- WeatherService
- ChecklistService
- DocumentService
- WorkdayService

### 查看数据库模型
```bash
codegraph query "class" | grep -i "model\|session"
```

---

## 💡 高级技巧

### 1. 组合使用多个命令
```bash
# 先搜索，再分析影响
codegraph query "weather" && codegraph impact "WeatherService"
```

### 2. 使用 context 进行深度分析
```bash
# 获取某个功能的完整实现细节
codegraph context "天气查询功能从 API 到数据库的完整实现"
```

### 3. 定期同步索引
```bash
# 在提交代码前同步索引
codegraph sync
```

### 4. 检查索引健康状态
```bash
# 确保索引是最新的
codegraph status
```

---

## ⚡ 性能提示

1. **首次启动**: 通义灵码重启后，第一次使用 CodeGraph 可能会有几秒延迟
2. **大型查询**: 复杂的 context 查询可能需要 5-10 秒
3. **日常使用**: 大多数查询都是毫秒级响应
4. **索引更新**: 文件保存后会自动同步，无需手动操作

---

## 🎓 学习路径

### 第 1 天: 基础探索
- 运行 `codegraph status` 了解项目概况
- 尝试 `codegraph query` 搜索你感兴趣的符号
- 在通义灵码中问一些简单的代码结构问题

### 第 2-3 天: 深入使用
- 使用 `callers` 和 `callees` 分析调用关系
- 尝试 `impact` 分析修改的影响
- 在重构代码时使用 CodeGraph 辅助决策

### 第 1 周后: 高效工作流
- 将 CodeGraph 融入日常开发流程
- 使用 `context` 快速获取任务相关信息
- 在代码审查时使用影响分析

---

## 🔗 相关资源

- 完整配置说明: `CODEGRAPH_SETUP.md`
- 官方文档: https://github.com/colbymchenry/codegraph
- 验证脚本: `./test_codegraph.sh`
