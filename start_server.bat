@echo off
echo 网易云音乐礼品卡分析器 - Web版启动脚本
echo ==========================================

echo.
echo 检查Python环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 安装依赖包...
pip install -r requirements_api.txt

echo.
echo 启动后端API服务器...
echo 服务器地址: http://127.0.0.1:5000
echo 前端页面: http://127.0.0.1:5000/static/index.html
echo.
echo 按 Ctrl+C 停止服务器
echo.

python server.py --host 0.0.0.0 --port 5000

pause