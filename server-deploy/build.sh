#!/bin/bash
# 编译服务器为独立可执行文件

set -e

echo "========================================"
echo "  编译 Draw & Guess 服务器"
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查/创建虚拟环境
if [ ! -d "venv" ]; then
    echo " 创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate

# 安装 PyInstaller
echo ""
echo " 安装 PyInstaller..."
pip install --upgrade pip pyinstaller

# 编译
echo ""
echo " 编译服务器..."
pyinstaller --onefile \
    --name game-server \
    --clean \
    --noconfirm \
    server.py

# 移动到当前目录
mv dist/game-server ./
rm -rf build dist *.spec

# 设置权限
chmod 755 game-server

echo ""
echo "========================================"
echo "  编译完成！"
echo "========================================"
echo ""
echo "生成文件: game-server ($(du -h game-server | cut -f1))"
echo ""
echo "运行方式:"
echo "  ./game-server"
echo ""
echo "或后台运行:"
echo "  nohup ./game-server > server.log 2>&1 &"
echo ""
