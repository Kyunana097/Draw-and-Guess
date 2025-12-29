#!/bin/bash
# Draw & Guess 服务器一键部署脚本

set -e

echo "========================================"
echo "  Draw & Guess 游戏服务器部署脚本"
echo "========================================"

# 检测系统
if ! command -v apt &> /dev/null; then
    echo " 此脚本仅支持 Ubuntu/Debian 系统"
    exit 1
fi

# 安装依赖
echo ""
echo " 安装系统依赖..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip screen

# 创建虚拟环境
echo ""
echo " 创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 安装 Python 依赖
echo ""
echo " 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置防火墙
echo ""
echo " 配置防火墙..."
sudo ufw allow 5555/tcp 2>/dev/null || true
echo " 端口 5555 已开放"

# 获取公网 IP
echo ""
echo " 服务器信息:"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "无法获取")
echo "   公网 IP: $PUBLIC_IP"
echo "   端口: 5555"

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo ""
echo "启动服务器命令："
echo "  ./start-server.sh"
echo ""
echo "客户端连接地址："
echo "  服务器地址: $PUBLIC_IP"
echo "  端口: 5555"
echo ""
