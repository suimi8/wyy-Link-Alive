#!/bin/bash

echo "网易云音乐礼品卡分析器 - Web版启动脚本"
echo "=========================================="
echo

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境，请先安装Python 3.8+"
    exit 1
fi

python3 --version

echo
echo "安装依赖包..."
pip3 install -r requirements_api.txt

# 创建static目录
echo "设置静态文件目录..."
mkdir -p static
cp index.html static/ 2>/dev/null || echo "index.html已在static目录中"
cp -r js static/ 2>/dev/null || echo "js目录已在static目录中"

echo
echo "启动后端API服务器..."
echo "服务器地址: http://127.0.0.1:5000"
echo "前端页面: http://127.0.0.1:5000/static/index.html"
echo
echo "按 Ctrl+C 停止服务器"
echo

python3 server.py --host 0.0.0.0 --port 5000