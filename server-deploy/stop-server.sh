#!/bin/bash
# 停止游戏服务器

echo " 停止游戏服务器..."

# 停止 screen 会话
screen -S game-server -X quit 2>/dev/null && echo " screen 会话已停止" || true

# 杀死残留进程
pkill -f "python.*server.py" 2>/dev/null && echo " 服务器进程已停止" || echo "ℹ  没有运行中的服务器进程"

echo "完成"
