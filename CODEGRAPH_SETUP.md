# CodeGraph 配置说明

## ✅ 已完成配置

### 1. CodeGraph 安装
- **版本**: v0.9.4
- **安装方式**: `npm i -g @colbymchenry/codegraph`
- **安装位置**: 全局安装

### 2. 通义灵码 MCP 配置
已在以下位置添加 CodeGraph MCP 服务器配置：
```
~/Library/Application Support/Lingma/SharedClientCache/mcp.json
```

配置内容：
```json
{
  "codegraph": {
    "command": "codegraph",
    "args": [
      "serve",
      "--mcp"
    ]
  }
}
```

### 3. 项目索引
- **项目路径**: `/Users/lihanchao/Documents/other/ai-server`
- **索引位置**: `.codegraph/codegraph.db`
- **索引统计**:
  - 文件数: 22
  - 节点数: 128
  - 边数: 165
  - 数据库大小: 0.26 MB

## 🚀 使用方法

### 在通义灵码中使用

1. **重启通义灵码编辑器**
   - 完全关闭并重新打开通义灵码
   - MCP 服务器会在启动时自动加载

2. **使用 CodeGraph 功能**
   
   在通义灵码的 AI 对话中，你可以这样提问：
   
   ```
   "帮我分析一下 chat_service.py 的实现逻辑"
   "找出所有调用 AI 客户端的地方"
   "这个项目的数据库模型有哪些？它们之间的关系是什么？"
   "weather_service 被哪些模块调用了？"
   ```

3. **CodeGraph 会自动提供**：
   - 符号关系图
   - 调用链分析
   - 代码结构信息
   - 相关文件定位

### 命令行使用

你也可以在终端直接使用 CodeGraph：

```bash
# 查看项目状态
codegraph status

# 搜索符号
codegraph query "chat"

# 查找调用者
codegraph callers "ChatService"

# 查找被调用者
codegraph callees "chat"

# 影响分析
codegraph impact "create_reply"

# 查看文件结构
codegraph files

# 构建上下文（用于 AI 助手）
codegraph context "帮我理解天气查询功能的实现"
```

## 📊 当前项目索引详情

### 节点类型分布
- import: 43
- file: 22
- class: 19
- function: 12
- route: 11
- variable: 11
- method: 10

### 文件语言
- Python: 22 个文件

## 🔄 维护命令

### 重新索引
如果项目文件发生变化，可以手动重新索引：
```bash
cd /Users/lihanchao/Documents/other/ai-server
codegraph index
```

### 同步变更
增量同步自上次索引以来的变更：
```bash
codegraph sync
```

### 移除索引
如果需要移除 CodeGraph：
```bash
codegraph uninit
```

## 💡 使用建议

1. **首次使用**：重启通义灵码后，尝试问一些关于代码结构的问题
2. **日常开发**：在重构或理解代码时，利用 CodeGraph 快速定位相关代码
3. **代码审查**：使用 `impact` 命令分析修改的影响范围
4. **学习新代码**：使用 `context` 命令快速获取某个功能的完整上下文

## ⚠️ 注意事项

1. CodeGraph 是完全本地运行的，不会上传任何代码到外部
2. 索引文件位于 `.codegraph/` 目录，已添加到 `.gitignore`
3. MCP 服务器会在通义灵码启动时自动运行
4. 如果遇到性能问题，可以使用 `codegraph status` 检查索引状态

## 🔧 故障排除

### MCP 服务器未加载
1. 检查配置文件是否正确：
   ```bash
   cat ~/Library/Application\ Support/Lingma/SharedClientCache/mcp.json
   ```

2. 确认 codegraph 命令可用：
   ```bash
   which codegraph
   codegraph --version
   ```

3. 重启通义灵码

### 索引过时
```bash
cd /Users/lihanchao/Documents/other/ai-server
codegraph sync
```

### 查看日志
CodeGraph 的日志会显示在通义灵码的输出面板中

## 📚 更多信息

- 官方文档: https://github.com/colbymchenry/codegraph
- 支持的代理: Claude Code, Cursor, Codex CLI, opencode, Hermes Agent, 通义灵码
