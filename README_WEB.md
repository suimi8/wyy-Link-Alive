# 网易云音乐礼品卡分析器 - Web版 🎵

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0+-cyan.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **现代化Web版本** - 使用TailwindCSS和Alpine.js构建的现代化前端界面
> **跨平台支持** - 支持Windows、Linux、macOS系统
> **真实API分析** - 结合Python后端实现真实的链接分析功能

## 🎯 新版本特点

### ✨ 全新设计
- **🎨 现代化UI**: 玻璃拟态设计风格，美观大方
- **📱 响应式布局**: 完美适配桌面、平板、手机
- **🌙 深色主题**: 护眼的深色主题设计
- **🎭 动画效果**: 流畅的页面切换和交互动画

### 🏗️ 技术架构
- **前端**: TailwindCSS + Alpine.js + Vanilla JavaScript
- **后端**: Flask + aiohttp + 异步处理
- **API**: RESTful API设计，支持单个和批量分析
- **数据**: 本地存储 + 服务器端处理

### 🚀 功能特色
- **智能分析**: 自动识别礼品卡和VIP链接
- **批量处理**: 支持大量链接的并发分析
- **实时进度**: 分析进度实时显示和统计
- **数据可视化**: 饼图、统计卡片、趋势展示
- **导出功能**: 支持多种格式的结果导出

## 📦 快速开始

### 环境要求
- Python 3.8+ 
- 现代浏览器（Chrome、Firefox、Safari、Edge）
- 网络连接

### 安装步骤

#### Windows 用户
```bash
# 1. 双击运行启动脚本
start_server.bat
```

#### Linux/Mac 用户
```bash
# 1. 运行启动脚本
./start_server.sh

# 或者手动安装
pip3 install -r requirements_api.txt
python3 server.py
```

#### 手动安装
```bash
# 1. 安装依赖
pip install -r requirements_api.txt

# 2. 启动服务器
python server.py --host 0.0.0.0 --port 5000

# 3. 打开浏览器访问
# http://127.0.0.1:5000/static/index.html
```

## 🖥️ 使用指南

### 1. 启动服务
运行启动脚本后，控制台会显示：
```
启动服务器: http://127.0.0.1:5000
API文档:
  POST /api/analyze - 分析单个链接
  POST /api/batch_analyze - 批量分析链接
  GET /api/health - 健康检查
```

### 2. 访问界面
在浏览器中打开：`http://127.0.0.1:5000/static/index.html`

### 3. 页面功能

#### 📊 仪表板
- **统计概览**: 显示总链接数、可用礼品、VIP链接等统计信息
- **快速分析**: 直接粘贴链接进行快速分析
- **最近结果**: 查看最新的分析结果
- **数据图表**: 饼图显示分析结果分布

#### 🔍 分析器
- **链接输入**: 支持文本输入、文件上传、剪贴板粘贴
- **实时验证**: 输入时自动验证链接格式
- **批量处理**: 支持大量链接的并发分析
- **进度监控**: 实时显示分析进度和速度
- **结果预览**: 分析完成的结果实时显示

#### 📈 结果页面
- **详细列表**: 所有分析结果的详细列表
- **高级过滤**: 按状态、类型、时间等条件过滤
- **批量操作**: 支持批量选择、导出、删除
- **详细信息**: 点击查看每个结果的详细信息

#### ⚙️ 设置页面
- **分析配置**: 并发数、超时时间、重试次数等
- **界面设置**: 主题、动画、通知等偏好
- **数据管理**: 数据备份、导入、清理等
- **高级选项**: 调试模式、缓存管理等

## 📋 API 接口

### 健康检查
```http
GET /api/health
```

响应:
```json
{
  "status": "healthy",
  "timestamp": 1700000000000,
  "analyzer_available": true
}
```

### 分析单个链接
```http
POST /api/analyze
Content-Type: application/json

{
  "link": "http://163cn.tv/xxxxxx"
}
```

响应:
```json
{
  "short_url": "http://163cn.tv/xxxxxx",
  "status": "success",
  "gift_status": "available",
  "status_text": "可领取 (2/3)",
  "gift_type": "黑胶VIP月卡",
  "gift_price": 15,
  "sender_name": "用户昵称",
  "total_count": 3,
  "used_count": 1,
  "available_count": 2,
  "expire_date": "2024-12-31 23:59:59 (北京时间)",
  "timestamp": 1700000000000
}
```

### 批量分析链接
```http
POST /api/batch_analyze
Content-Type: application/json

{
  "links": [
    "http://163cn.tv/link1",
    "http://163cn.tv/link2"
  ],
  "max_workers": 5
}
```

响应:
```json
{
  "results": [...],
  "total": 2,
  "timestamp": 1700000000000
}
```

## 🔧 配置说明

### 服务器配置
```bash
# 自定义端口
python server.py --port 8080

# 自定义主机地址
python server.py --host 0.0.0.0

# 调试模式
python server.py --debug
```

### 前端配置
在 `static/js/app.js` 中修改API基础URL：
```javascript
const AnalyzerAPI = {
    baseURL: 'http://your-server:5000',  // 修改为你的服务器地址
    // ...
}
```

## 📁 项目结构

```
wyy/
├── server.py                 # Flask API服务器
├── requirements_api.txt      # API服务器依赖
├── start_server.bat         # Windows启动脚本
├── start_server.sh          # Linux/Mac启动脚本
├── static/                  # 静态文件目录
│   ├── index.html          # 主页面
│   └── js/                 # JavaScript文件
│       ├── app.js          # 主应用逻辑
│       └── components/     # 页面组件
│           ├── dashboard.js    # 仪表板
│           ├── analyzer.js     # 分析器
│           ├── results.js      # 结果页面
│           └── settings.js     # 设置页面
├── gift_analyzer_ui.py      # 原PyQt6版本
├── optimal_gift_analyzer.py # 核心分析引擎
└── README_WEB.md           # Web版说明文档
```

## 🎨 界面预览

### 仪表板
- 现代化的卡片布局
- 实时统计数据
- 可视化图表
- 快速操作入口

### 分析器
- 直观的输入界面
- 实时进度显示
- 智能链接验证
- 结果实时预览

### 结果页面
- 表格化数据展示
- 强大的过滤功能
- 批量操作支持
- 详细信息弹窗

### 设置页面
- 分类清晰的设置项
- 实时保存配置
- 数据备份还原
- 系统状态监控

## 🚨 注意事项

### 网络要求
- 需要稳定的网络连接
- 建议在良好的网络环境下使用
- 避免过于频繁的请求

### 性能建议
- 建议并发数设置在5-20之间
- 大量链接可以分批处理
- 定期清理历史数据

### 安全提醒
- 仅在可信网络环境下使用
- 不要分享敏感的分析结果
- 遵守相关服务条款

## 🔧 故障排除

### 常见问题

#### 1. 服务器启动失败
```bash
# 检查Python版本
python --version

# 检查依赖安装
pip install -r requirements_api.txt

# 检查端口占用
netstat -an | grep 5000
```

#### 2. 前端无法访问
- 确认服务器已启动
- 检查防火墙设置
- 确认浏览器地址正确

#### 3. 分析功能异常
- 检查网络连接
- 查看控制台错误信息
- 尝试使用模拟模式

#### 4. 性能问题
- 降低并发数设置
- 分批处理大量链接
- 关闭不必要的浏览器标签

### 调试模式
启用调试模式获取详细日志：
```bash
python server.py --debug
```

## 📝 更新日志

### v2.0.0 (Web版)
- ✨ 全新的Web界面设计
- 🚀 Flask API服务器
- 📱 响应式布局支持
- 🎨 TailwindCSS美化界面
- ⚡ 异步分析处理
- 📊 数据可视化功能

## 🤝 贡献指南

欢迎提交Issues和Pull Requests来改进项目！

### 开发环境搭建
```bash
# 1. 克隆项目
git clone [project-url]

# 2. 安装依赖
pip install -r requirements_api.txt

# 3. 启动开发服务器
python server.py --debug
```

### 代码规范
- 前端代码使用ES6+语法
- 后端代码遵循PEP8规范
- 添加必要的注释和文档

## ⚖️ 免责声明

本软件仅供学习研究使用，请勿用于商业用途。使用时请遵守相关服务条款和法律法规。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**开发者**: suimi
**版本**: 2.0.0 (Web版)
**更新时间**: 2024年

**如有问题请通过Issues反馈，感谢使用！** 🎉