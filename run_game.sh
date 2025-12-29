#!/bin/bash
# 你画我猜游戏启动脚本

echo "================================"
echo "  你画我猜游戏 - 启动脚本"
echo "================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 检查并激活虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

echo "激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt

echo ""
echo "正在启动服务器..."
# 在后台启动服务器（默认监听 0.0.0.0:5555，支持通过环境变量覆盖）
HOST=${HOST:-0.0.0.0} PORT=${PORT:-5555} python server-deploy/server.py &
SERVER_PID=$!
echo "服务器已启动 (PID: $SERVER_PID)"

# 等待服务器启动
sleep 2

echo ""
echo "正在启动客户端..."
python -m src.client.main

echo ""
echo "游戏已关闭"

# 清理：关闭服务器
if ps -p $SERVER_PID > /dev/null; then
    echo "正在关闭服务器..."
    kill $SERVER_PID
fi

echo "完成！"
