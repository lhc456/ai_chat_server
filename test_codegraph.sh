#!/bin/bash

echo "🔍 CodeGraph 配置验证"
echo "===================="
echo ""

# 检查 codegraph 是否安装
echo "1. 检查 CodeGraph 安装..."
if command -v codegraph &> /dev/null; then
    VERSION=$(codegraph --version)
    echo "   ✅ CodeGraph 已安装 (版本: $VERSION)"
else
    echo "   ❌ CodeGraph 未安装"
    exit 1
fi
echo ""

# 检查 MCP 配置
echo "2. 检查通义灵码 MCP 配置..."
MCP_CONFIG="$HOME/Library/Application Support/Lingma/SharedClientCache/mcp.json"
if [ -f "$MCP_CONFIG" ]; then
    if grep -q "codegraph" "$MCP_CONFIG"; then
        echo "   ✅ CodeGraph 已配置到通义灵码 MCP"
    else
        echo "   ❌ CodeGraph 未配置到通义灵码 MCP"
        exit 1
    fi
else
    echo "   ❌ MCP 配置文件不存在"
    exit 1
fi
echo ""

# 检查项目索引
echo "3. 检查项目索引..."
if [ -d ".codegraph" ]; then
    echo "   ✅ .codegraph 目录存在"
    if [ -f ".codegraph/codegraph.db" ]; then
        DB_SIZE=$(du -h .codegraph/codegraph.db | cut -f1)
        echo "   ✅ 索引数据库存在 (大小: $DB_SIZE)"
    else
        echo "   ❌ 索引数据库不存在"
        exit 1
    fi
else
    echo "   ❌ .codegraph 目录不存在"
    exit 1
fi
echo ""

# 检查索引状态
echo "4. 检查索引状态..."
codegraph status | head -15
echo ""

# 测试搜索功能
echo "5. 测试搜索功能..."
echo "   搜索 'chat' 相关符号:"
codegraph query "chat" | head -10
echo ""

echo "===================="
echo "✅ 所有检查通过！"
echo ""
echo "📝 下一步："
echo "   1. 重启通义灵码编辑器"
echo "   2. 在 AI 对话中尝试提问关于代码的问题"
echo "   3. 查看 CODEGRAPH_SETUP.md 了解更多使用方法"
