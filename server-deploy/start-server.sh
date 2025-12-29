#!/bin/bash
# 启动游戏服务器

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source venv/bin/activate

# 获取公网 IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "未知")

echo "========================================"
echo "  Draw & Guess 游戏服务器"
echo "========================================"
echo "  公网地址: $PUBLIC_IP:5555"
echo "========================================"
echo ""

# 检查是否使用 screen
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo " 后台启动服务器..."
    screen -dmS game-server bash -c "cd $SCRIPT_DIR && source venv/bin/activate && HOST=0.0.0.0 PORT=5555 python server.py"
    echo " 服务器已在后台启动"
    echo ""
    echo "查看服务器: screen -r game-server"
    echo "停止服务器: screen -S game-server -X quit"
else
    echo " 启动服务器（前台模式，Ctrl+C 停止）..."
    echo ""
    HOST=0.0.0.0 PORT=5555 python server.py
fi
