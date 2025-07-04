#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易云音乐礼品卡分析器 - Web API 服务器 (简化版)
提供HTTP API接口，支持跨域请求
"""

import json
import time
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
from datetime import datetime, timezone, timedelta
import re
from urllib.parse import urlparse, parse_qs
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入原有的分析器
try:
    from optimal_gift_analyzer import OptimalGiftAnalyzer
except ImportError:
    print("警告: 无法导入 optimal_gift_analyzer，将使用简化版分析器")
    OptimalGiftAnalyzer = None

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebAnalyzer:
    """Web版本的分析器（简化版）"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })
        self.original_analyzer = None
        if OptimalGiftAnalyzer:
            self.original_analyzer = OptimalGiftAnalyzer()
    
    def to_beijing_time(self, timestamp_ms):
        """将毫秒时间戳转换为北京时间字符串"""
        try:
            beijing_tz = timezone(timedelta(hours=8))
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=beijing_tz)
            return dt.strftime('%Y-%m-%d %H:%M:%S (北京时间)')
        except:
            return '时间转换失败'
    
    def get_redirect_url(self, url):
        """获取重定向URL"""
        try:
            response = self.session.head(url, allow_redirects=False, timeout=10)
            if response.status_code in [301, 302, 303, 307, 308]:
                return response.headers.get('Location', url)
            return url
        except Exception as e:
            logger.error(f"获取重定向URL失败: {e}")
            return url
    
    def check_vip_link(self, link):
        """检查VIP链接"""
        try:
            # 获取重定向URL
            redirect_url = self.get_redirect_url(link)
            
            if 'vip-invite-cashier' not in redirect_url:
                return {
                    'short_url': link,
                    'status': 'error',
                    'gift_status': 'invalid',
                    'error_message': '不是有效的VIP链接',
                    'timestamp': int(time.time() * 1000)
                }
            
            # 获取页面内容
            response = self.session.get(redirect_url, timeout=15)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")
            
            html = response.text
            
            # 解析过期时间
            expire_patterns = [
                r'expireTime["\']?\s*[=:]\s*["\']?(\d{13})["\']?',
                r'"expireTime"\s*:\s*(\d{13})',
                r'tokenExpireTime["\']?\s*[=:]\s*["\']?(\d{13})["\']?',
            ]
            
            expire_time = None
            for pattern in expire_patterns:
                match = re.search(pattern, html)
                if match:
                    expire_time = int(match.group(1))
                    break
            
            current_time = int(time.time() * 1000)
            is_valid = expire_time and expire_time > current_time
            
            # 解析标题
            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1) if title_match else 'VIP邀请'
            
            return {
                'short_url': link,
                'redirect_url': redirect_url,
                'status': 'success',
                'is_vip_link': True,
                'gift_type': 'VIP邀请',
                'gift_status': 'available' if is_valid else 'expired',
                'vip_status': 'valid' if is_valid else 'expired',
                'expire_time': expire_time,
                'expire_date': self.to_beijing_time(expire_time) if expire_time else None,
                'remaining_days': max(0, (expire_time - current_time) / (1000 * 60 * 60 * 24)) if expire_time else 0,
                'status_text': 'VIP有效' if is_valid else 'VIP已过期',
                'title': title,
                'timestamp': current_time
            }
                
        except Exception as e:
            logger.error(f"VIP链接检测失败: {e}")
            return {
                'short_url': link,
                'status': 'error',
                'is_vip_link': True,
                'gift_status': 'invalid',
                'error_message': str(e),
                'timestamp': int(time.time() * 1000)
            }
    
    def check_gift_link(self, link):
        """检查礼品卡链接"""
        try:
            # 如果有原始分析器，优先使用
            if self.original_analyzer:
                try:
                    result = self.original_analyzer.analyze_gift_link(link)
                    if result.get('status') == 'success':
                        return result
                except Exception as e:
                    logger.warning(f"原始分析器失败，使用Web分析器: {e}")
            
            # Web分析器实现
            gift_id_match = re.search(r'163cn\.tv/(\w+)', link)
            if not gift_id_match:
                raise Exception('无效的礼品卡链接格式')
            
            gift_id = gift_id_match.group(1)
            
            # 尝试直接访问链接获取页面内容
            response = self.session.get(link, timeout=15)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")
            
            html = response.text
            
            # 检查页面状态指示器
            status_indicators = {
                '礼品卡不存在': 'invalid',
                '链接已失效': 'invalid',
                '已过期': 'expired',
                '已领取完': 'claimed',
                '礼品卡已被领完': 'claimed',
                '活动已结束': 'expired'
            }
            
            for indicator, status in status_indicators.items():
                if indicator in html:
                    return {
                        'short_url': link,
                        'status': 'success',
                        'gift_status': status,
                        'status_text': indicator,
                        'gift_type': '未知礼品',
                        'timestamp': int(time.time() * 1000)
                    }
            
            # 尝试解析JSON数据
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.INITIAL_STATE\s*=\s*({.+?});',
                r'__NUXT__\s*=\s*({.+?});'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        gift_data = self.extract_gift_data(json_data)
                        if gift_data:
                            return self.parse_gift_data(gift_data, link)
                    except json.JSONDecodeError:
                        continue
            
            # 如果没有找到明确的状态，默认返回可能可用
            return {
                'short_url': link,
                'status': 'success',
                'gift_status': 'available',
                'status_text': '状态未知，请手动检查',
                'gift_type': '未知礼品',
                'timestamp': int(time.time() * 1000)
            }
                
        except Exception as e:
            logger.error(f"礼品卡检测失败: {e}")
            return {
                'short_url': link,
                'status': 'error',
                'gift_status': 'invalid',
                'error_message': str(e),
                'timestamp': int(time.time() * 1000)
            }
    
    def extract_gift_data(self, json_data):
        """从JSON数据中提取礼品信息"""
        # 递归查找礼品数据
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key in ['gift', 'giftInfo', 'linkCard', 'card']:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self.extract_gift_data(value)
                    if result:
                        return result
        elif isinstance(json_data, list):
            for item in json_data:
                result = self.extract_gift_data(item)
                if result:
                    return result
        return None
    
    def parse_gift_data(self, gift_data, link):
        """解析礼品数据"""
        try:
            current_time = int(time.time() * 1000)
            expire_time = gift_data.get('expireTime') or gift_data.get('expire_time')
            is_expired = expire_time and expire_time < current_time
            
            total_count = gift_data.get('count', gift_data.get('total_count', 0))
            used_count = gift_data.get('usedCount', gift_data.get('used_count', 0))
            available_count = max(0, total_count - used_count)
            
            if is_expired:
                gift_status = 'expired'
                status_text = '已过期'
            elif available_count <= 0:
                gift_status = 'claimed'
                status_text = '已领取完'
            else:
                gift_status = 'available'
                status_text = f'可领取 ({available_count}/{total_count})'
            
            return {
                'short_url': link,
                'status': 'success',
                'gift_status': gift_status,
                'status_text': status_text,
                'gift_type': gift_data.get('giftTypeName', gift_data.get('gift_type_name', '未知礼品')),
                'gift_price': gift_data.get('price', gift_data.get('gift_price', 0)),
                'sender_name': gift_data.get('senderName', gift_data.get('sender_name', '未知')),
                'total_count': total_count,
                'used_count': used_count,
                'available_count': available_count,
                'expire_time': expire_time,
                'expire_date': self.to_beijing_time(expire_time) if expire_time else None,
                'is_expired': is_expired,
                'timestamp': current_time
            }
        except Exception as e:
            raise Exception(f'数据解析失败: {str(e)}')
    
    def analyze_single_link(self, link):
        """分析单个链接"""
        try:
            # 检查链接类型
            redirect_url = self.get_redirect_url(link)
            
            if 'vip-invite-cashier' in redirect_url:
                return self.check_vip_link(link)
            elif '163cn.tv' in link:
                return self.check_gift_link(link)
            else:
                return {
                    'short_url': link,
                    'status': 'error',
                    'gift_status': 'invalid',
                    'error_message': '不支持的链接格式',
                    'timestamp': int(time.time() * 1000)
                }
        except Exception as e:
            logger.error(f"分析链接失败: {e}")
            return {
                'short_url': link,
                'status': 'error',
                'gift_status': 'invalid',
                'error_message': str(e),
                'timestamp': int(time.time() * 1000)
            }

# 创建全局分析器实例
analyzer = WebAnalyzer()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time() * 1000),
        'analyzer_available': OptimalGiftAnalyzer is not None
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_link():
    """分析单个链接"""
    try:
        data = request.get_json()
        if not data or 'link' not in data:
            return jsonify({
                'error': '缺少link参数'
            }), 400
        
        link = data['link'].strip()
        if not link:
            return jsonify({
                'error': '链接不能为空'
            }), 400
        
        logger.info(f"开始分析链接: {link}")
        result = analyzer.analyze_single_link(link)
        logger.info(f"分析完成: {result.get('gift_status', 'unknown')}")
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"分析接口错误: {e}", exc_info=True)
        return jsonify({
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/batch_analyze', methods=['POST'])
def batch_analyze():
    """批量分析链接"""
    try:
        data = request.get_json()
        if not data or 'links' not in data:
            return jsonify({
                'error': '缺少links参数'
            }), 400
        
        links = data['links']
        if not isinstance(links, list):
            return jsonify({
                'error': 'links必须是数组'
            }), 400
        
        if len(links) > 50:  # 限制批量数量
            return jsonify({
                'error': '单次最多支持50个链接'
            }), 400
        
        results = []
        for link in links:
            result = analyzer.analyze_single_link(link)
            results.append(result)
        
        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': int(time.time() * 1000)
        })
            
    except Exception as e:
        logger.error(f"批量分析接口错误: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)

@app.route('/')
def index():
    """主页"""
    return """
    <h1>网易云音乐礼品卡分析器 API</h1>
    <p>API接口:</p>
    <ul>
        <li>GET /api/health - 健康检查</li>
        <li>POST /api/analyze - 分析单个链接</li>
        <li>POST /api/batch_analyze - 批量分析链接</li>
    </ul>
    <p>前端页面: <a href="/static/index.html">打开分析器</a></p>
    """

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='网易云音乐礼品卡分析器 Web 服务器')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    print(f"启动服务器: http://{args.host}:{args.port}")
    print("API文档:")
    print("  POST /api/analyze - 分析单个链接")
    print("  POST /api/batch_analyze - 批量分析链接")
    print("  GET /api/health - 健康检查")
    print("前端页面:")
    print(f"  http://{args.host}:{args.port}/static/index.html")
    
    app.run(host=args.host, port=args.port, debug=args.debug)