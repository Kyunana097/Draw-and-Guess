#!/bin/bash
# 快速启动脚本 (Linux/Mac)

echo "🎨 Draw & Guess 游戏启动脚本"
echo "================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "📦 检查依赖..."
pip install -q -r requirements.txt

# 默认：直接启动客户端（不再交互选择模式）
echo ""
echo "🚀 启动客户端..."
python src/client/main.py
