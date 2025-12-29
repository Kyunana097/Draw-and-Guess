#!/bin/bash
# 快速测试脚本 - 测试修复后的功能

echo "================================"
echo "  测试修复后的功能"
echo "================================"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在，请先运行 ./start.sh 创建"
    exit 1
fi

echo ""
echo "测试1: 检查Python环境"
python --version

echo ""
echo "测试2: 检查依赖"
python -c "import pygame; print('✅ pygame 已安装:', pygame.version.ver)"

echo ""
echo "测试3: 检查服务器代码"
python -m py_compile server-deploy/server.py && echo "✅ 服务器代码正常"

echo ""
echo "测试4: 检查客户端代码"
python -m py_compile src/client/main.py && echo "✅ 客户端代码正常"
python -m py_compile src/client/network.py && echo "✅ 网络模块正常"

echo ""
echo "测试5: 检查常量定义"
python -c "from src.shared.constants import MSG_NEXT_ROUND, MSG_GIVE_SCORE, MSG_GAME_RESULT; print('✅ 新增消息类型已定义')"

echo ""
echo "================================"
echo "  所有测试完成！"
echo "================================"
echo ""
echo "现在可以运行游戏："
echo "  本地测试: ./start.sh"
echo "  快速启动: ./run_game.sh"
