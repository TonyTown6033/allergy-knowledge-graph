#!/bin/bash

echo "======================================"
echo "过敏知识图谱 - 后台管理系统启动脚本"
echo "======================================"

# 切换到项目目录
cd "$(dirname "$0")"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv 未安装"
    echo ""
    echo "请先安装 uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

# 检查并安装 Flask
echo "检查依赖..."
if ! uv run python -c "import flask" 2>/dev/null; then
    echo "安装 Flask..."
    uv pip install flask
fi

# 检测可用端口
PORT=5001
echo ""
echo "检查端口可用性..."
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    echo "⚠️  端口 $PORT 已被占用，尝试下一个端口..."
    PORT=$((PORT + 1))
    if [ $PORT -gt 5010 ]; then
        echo "❌ 错误: 无法找到可用端口（5001-5010 都被占用）"
        exit 1
    fi
done

echo "✓ 使用端口: $PORT"

# 启动后台管理系统
echo ""
echo "启动后台管理系统..."
echo "访问地址: http://localhost:$PORT"
echo "======================================"
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务器"
echo ""

# 设置端口环境变量并启动
export FLASK_PORT=$PORT
uv run python -c "
import os
import sys
sys.path.insert(0, '.')
from admin.app import app
port = int(os.environ.get('FLASK_PORT', 5001))
print(f'\n✅ 服务器启动成功！')
print(f'   访问: http://localhost:{port}')
print(f'   前台: http://localhost:8000')
print()
app.run(debug=True, host='0.0.0.0', port=port)
"
