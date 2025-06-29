"""
网易云音乐礼品卡分析器 - PyQt6 UI界面
功能：
1. 批量分析礼品卡状态，支持失效链接删除
2. VIP链接有效期检查，自动保存未过期的VIP链接
3. 支持有效期内VIP链接的管理和清理
作者: suimi
"""

import sys
import os
import json
import time
import requests
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QTabWidget, QGroupBox, QSpinBox, QCheckBox, QSplitter,
    QStatusBar, QDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QAction

# 导入我们的分析器
from optimal_gift_analyzer import OptimalGiftAnalyzer

# 北京时间转换函数
def to_beijing_time(timestamp_ms):
    """将毫秒时间戳转换为北京时间字符串"""
    try:
        # 创建北京时区 (UTC+8)
        beijing_tz = timezone(timedelta(hours=8))
        # 转换时间戳（毫秒转秒）
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=beijing_tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S (北京时间)')
    except:
        return '时间转换失败'

class FileOperationThread(QThread):
    """文件操作工作线程"""
    operation_completed = pyqtSignal(bool, str)  # 成功状态, 消息
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 状态信息

    def __init__(self, operation_type, file_path=None, data=None, **kwargs):
        super().__init__()
        self.operation_type = operation_type  # 'load', 'save', 'export'
        self.file_path = file_path
        self.data = data
        self.kwargs = kwargs
        self.result_data = None

    def run(self):
        """执行文件操作"""
        try:
            if self.operation_type == 'load':
                self._load_file()
            elif self.operation_type == 'save':
                self._save_file()
            elif self.operation_type == 'export':
                self._export_file()
            elif self.operation_type == 'save_multiple':
                self._save_multiple_files()
        except Exception as e:
            self.operation_completed.emit(False, f"操作失败: {str(e)}")

    def _load_file(self):
        """加载文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.result_data = content
            self.operation_completed.emit(True, f"已加载文件: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"加载文件失败: {str(e)}")

    def _save_file(self):
        """保存文件"""
        try:
            if self.kwargs.get('format') == 'json':
                import json
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
            else:
                # 文本格式
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    if isinstance(self.data, list):
                        # 处理大量数据时显示进度
                        total = len(self.data)
                        for i, item in enumerate(self.data):
                            if isinstance(item, dict):
                                f.write(item.get('short_url', str(item)) + '\n')
                            else:
                                f.write(str(item) + '\n')

                            # 每1000条更新一次进度
                            if i % 1000 == 0:
                                self.progress_updated.emit(i + 1, total, f"保存中...")
                    else:
                        f.write(str(self.data))

            count = len(self.data) if isinstance(self.data, list) else 1
            self.operation_completed.emit(True, f"已保存 {count} 项到: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"保存文件失败: {str(e)}")

    def _export_file(self):
        """导出文件"""
        try:
            export_type = self.kwargs.get('export_type', 'links')

            if export_type == 'available_links':
                links = [result.get('short_url', '') for result in self.data
                        if result['status'] == 'success' and result.get('gift_status') == 'available']
            elif export_type == 'invalid_links':
                links = [result.get('short_url', '') for result in self.data
                        if result['status'] != 'success' or result.get('gift_status') != 'available']
            else:
                links = self.data

            with open(self.file_path, 'w', encoding='utf-8') as f:
                total = len(links)
                for i, link in enumerate(links):
                    f.write(link + '\n')
                    # 每1000条更新一次进度
                    if i % 1000 == 0:
                        self.progress_updated.emit(i + 1, total, f"导出中...")

            self.operation_completed.emit(True, f"已导出 {len(links)} 个链接到: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"导出文件失败: {str(e)}")

    def _save_multiple_files(self):
        """保存多个文件"""
        try:
            files_data = self.kwargs.get('files_data', {})
            saved_count = 0

            for filename, links in files_data.items():
                if links:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(links))
                    saved_count += 1
                    self.progress_updated.emit(saved_count, len(files_data), f"保存 {filename}")

            self.operation_completed.emit(True, f"已保存 {saved_count} 个文件")
        except Exception as e:
            self.operation_completed.emit(False, f"保存多个文件失败: {str(e)}")

class AnalyzerThread(QThread):
    """分析器工作线程"""
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 状态信息
    result_ready = pyqtSignal(list)  # 分析结果（保留用于兼容性）
    single_result_ready = pyqtSignal(dict)  # 单个分析结果（新增）
    error_occurred = pyqtSignal(str)  # 错误信息

    def __init__(self, links, max_workers=5):
        super().__init__()
        self.links = links
        self.max_workers = max_workers
        self.analyzer = OptimalGiftAnalyzer()
        self.is_running = True
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # 初始状态为非暂停

    def extract_token_info(self, vip_url):
        """从VIP URL中提取token和其他参数"""
        try:
            parsed = urlparse(vip_url)
            query_params = parse_qs(parsed.query)

            token = query_params.get('token', [None])[0]
            record_id = query_params.get('recordId', [None])[0]

            # 从路径中提取活动ID
            path_parts = parsed.path.split('/')
            activity_id = None
            for part in path_parts:
                if part and part not in ['g', 'vip-invite-cashier']:
                    activity_id = part
                    break

            return {
                'token': token,
                'record_id': record_id,
                'activity_id': activity_id,
                'full_url': vip_url
            }
        except Exception as e:
            print(f"[❌ URL解析失败] {e}")
            return None

    def check_vip_api(self, token_info):
        """通过API检查VIP状态"""
        try:
            # 尝试调用VIP详情API
            api_urls = [
                'https://interface.music.163.com/api/vipactivity/app/vip/invitation/detail/info/get',
                'https://interface.music.163.com/api/vip/invitation/detail',
                'https://music.163.com/api/vip/invitation/detail'
            ]

            for api_url in api_urls:
                try:
                    params = {}
                    if token_info.get('token'):
                        params['token'] = token_info['token']
                    if token_info.get('record_id'):
                        params['recordId'] = token_info['record_id']

                    print(f"[🔍 尝试API] {api_url}")
                    response = requests.get(api_url, params=params, timeout=10)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f"[✅ API响应成功] 状态码: {response.status_code}")

                            # 解析响应数据
                            if 'data' in data:
                                detail_data = data['data']
                                # 尝试多个可能的过期时间字段
                                expire_time = (detail_data.get('expireTime') or
                                             detail_data.get('tokenExpireTime') or
                                             detail_data.get('expire_time') or
                                             detail_data.get('token_expire_time'))

                                if expire_time:
                                    current_time = int(time.time() * 1000)
                                    is_valid = expire_time > current_time
                                    expire_date_beijing = to_beijing_time(expire_time)
                                    remaining_days = (expire_time - current_time) / (1000 * 60 * 60 * 24)

                                    print(f"[⏰ 找到过期时间] {expire_time} -> {expire_date_beijing}")

                                    return {
                                        'is_valid': is_valid,
                                        'expire_time': expire_time,
                                        'expire_date': expire_date_beijing,
                                        'remaining_days': remaining_days,
                                        'api_data': detail_data,
                                        'method': 'api',
                                        'error': None
                                    }
                                else:
                                    print(f"[⚠️ 未找到过期时间字段] 可用字段: {list(detail_data.keys())}")

                        except json.JSONDecodeError:
                            print(f"[⚠️ JSON解析失败] {response.text[:200]}")
                            continue
                    else:
                        print(f"[⚠️ API请求失败] 状态码: {response.status_code}")

                except Exception as e:
                    print(f"[⚠️ API请求异常] {e}")
                    continue

            return None

        except Exception as e:
            print(f"[❌ API检查失败] {str(e)}")
            return None

    def check_vip_expiry(self, redirect_url):
        """检查VIP链接的有效期 - 增强版

        Args:
            redirect_url: VIP重定向链接

        Returns:
            dict: {
                'is_valid': bool,  # 是否未过期
                'expire_time': int,  # 过期时间戳（毫秒）
                'expire_date': str,  # 过期日期字符串
                'remaining_days': float,  # 剩余天数
                'method': str,  # 检测方法 ('api' 或 'page')
                'error': str  # 错误信息（如果有）
            }
        """
        try:
            print(f"[🔍 检查VIP有效期] {redirect_url}")

            # 1. 首先尝试API方法
            token_info = self.extract_token_info(redirect_url)
            if token_info and token_info.get('token'):
                api_result = self.check_vip_api(token_info)
                if api_result:
                    return api_result

            # 2. API失败，回退到页面解析方法
            print(f"[🔍 API方法失败，尝试页面解析]")
            response = requests.get(redirect_url, timeout=15)
            response.raise_for_status()

            content = response.text

            # 多种模式匹配expireTime
            expire_patterns = [
                # JavaScript中的expireTime比较
                r'expireTime["\']?\s*[)}\]]*\s*>=?\s*Date\.now\(\)',
                # JSON格式的expireTime
                r'["\']?expireTime["\']?\s*:\s*(\d{13})',
                r'expireTime["\']?\s*=\s*(\d{13})',
                # 对象属性访问
                r'\.expireTime\s*>=?\s*Date\.now\(\)',
                # 更宽泛的13位时间戳匹配
                r'expire[^:]*:\s*(\d{13})',
                r'time[^:]*:\s*(\d{13})',
                # 新增模式
                r'expireTime["\']?\s*[=:]\s*["\']?(\d{13})["\']?',
                r'expire_time["\']?\s*[=:]\s*["\']?(\d{13})["\']?',
                r'"expireTime"\s*:\s*(\d{13})',
                r"'expireTime'\s*:\s*(\d{13})",
                r'tokenExpireTime["\']?\s*[=:]\s*["\']?(\d{13})["\']?',
            ]

            expire_time = None
            matched_pattern = None

            # 尝试不同的模式匹配
            for i, pattern in enumerate(expire_patterns):
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"[🔍 模式{i+1}匹配到] {matches}")
                    for match in matches:
                        if isinstance(match, str) and match.isdigit() and len(match) == 13:
                            expire_time = int(match)
                            matched_pattern = f"模式{i+1}"
                            print(f"[✅ 找到时间戳] 使用{matched_pattern}: {expire_time}")
                            break
                    if expire_time:
                        break

            # 如果没有找到明确的时间戳，尝试查找所有可能的13位数字
            if not expire_time:
                print("[🔍 尝试通用时间戳匹配]")
                timestamp_pattern = r'\b(1[6-9]\d{11})\b'
                timestamps = re.findall(timestamp_pattern, content)

                if timestamps:
                    print(f"[📋 找到所有时间戳] {timestamps}")
                    current_time = int(time.time() * 1000)
                    # 过滤出未来的时间戳
                    future_timestamps = [int(ts) for ts in timestamps if int(ts) > current_time]

                    if future_timestamps:
                        expire_time = max(future_timestamps)
                        matched_pattern = "通用匹配"
                        print(f"[✅ 找到未来时间戳] {expire_time}")
                    else:
                        print(f"[⚠️ 找到时间戳但都是过去时间] {timestamps}")
                        # 如果没有未来时间戳，取最大的时间戳
                        if timestamps:
                            expire_time = max(int(ts) for ts in timestamps)
                            matched_pattern = "最大时间戳"
                            print(f"[⚠️ 使用最大时间戳] {expire_time}")
                else:
                    print("[❌ 未找到任何13位时间戳]")

            if expire_time:
                # 检查是否过期
                current_time = int(time.time() * 1000)
                is_valid = expire_time > current_time

                # 转换为北京时间
                expire_date_beijing = to_beijing_time(expire_time)

                # 计算剩余时间
                remaining_ms = expire_time - current_time
                remaining_days = remaining_ms / (1000 * 60 * 60 * 24)

                return {
                    'is_valid': is_valid,
                    'expire_time': expire_time,
                    'expire_date': expire_date_beijing,
                    'remaining_days': remaining_days,
                    'method': 'page',
                    'matched_pattern': matched_pattern,
                    'error': None
                }
            else:
                # 检查页面状态指示器
                status_indicators = {
                    '已过期': 'expired',
                    '活动已结束': 'ended',
                    '邀请已失效': 'invalid',
                    '链接已失效': 'invalid',
                    '不存在': 'not_found',
                    '已领取': 'claimed',
                    '领取成功': 'claimed',
                    '活动火爆': 'busy',
                    '请稍后重试': 'retry',
                }

                for indicator, status in status_indicators.items():
                    if indicator in content:
                        return {
                            'is_valid': False,
                            'expire_time': None,
                            'expire_date': None,
                            'remaining_days': 0,
                            'method': 'page',
                            'error': f'页面状态: {status} ({indicator})'
                        }

                return {
                    'is_valid': False,
                    'expire_time': None,
                    'expire_date': None,
                    'remaining_days': 0,
                    'method': 'page',
                    'error': '未找到有效期信息'
                }

        except requests.RequestException as e:
            return {
                'is_valid': False,
                'expire_time': None,
                'expire_date': None,
                'remaining_days': 0,
                'method': 'error',
                'error': f'网络请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'is_valid': False,
                'expire_time': None,
                'expire_date': None,
                'remaining_days': 0,
                'method': 'error',
                'error': f'解析失败: {str(e)}'
            }

    def analyze_single_link(self, link):
        """分析单个链接，包含增强VIP有效期检查"""
        try:
            # 首先检查是否为VIP链接（通过重定向检查）
            is_vip_link = False
            redirect_url = None

            try:
                # 获取重定向URL
                response = requests.head(link, allow_redirects=False, timeout=5)
                if response.status_code in [301, 302] and 'Location' in response.headers:
                    redirect_url = response.headers['Location']
                    is_vip_link = 'vip-invite-cashier' in redirect_url
                else:
                    # 如果HEAD失败，尝试GET
                    response = requests.get(link, allow_redirects=True, timeout=10)
                    redirect_url = response.url
                    is_vip_link = 'vip-invite-cashier' in redirect_url
            except:
                pass

            # 如果是VIP链接，使用增强的VIP检测
            if is_vip_link and redirect_url:
                print(f"[🎯 检测到VIP链接] {link}")

                # 进行VIP有效期检查
                expiry_result = self.check_vip_expiry(redirect_url)

                # 构建VIP链接结果 - 只显示VIP相关信息
                result = {
                    'status': 'success',
                    'short_url': link,
                    'redirect_url': redirect_url,
                    'is_vip_link': True,
                    'vip_expiry_check': expiry_result,
                    'gift_type': 'VIP邀请',
                    'gift_price': 0,  # VIP链接没有固定价格
                    'sender': '',  # 将在后面填充
                    'gift_count': '',  # VIP链接不显示数量
                }

                # 根据有效期检查结果设置状态
                if expiry_result.get('error'):
                    print(f"[⚠️ VIP有效期检查失败] {expiry_result['error']}")
                    result['vip_status'] = 'expiry_check_failed'
                    result['vip_status_text'] = f"有效期检查失败: {expiry_result['error']}"
                    result['gift_status'] = 'unknown'
                    result['status_text'] = f"VIP链接 - {expiry_result['error']}"
                elif expiry_result.get('is_valid') is False:
                    expire_date = expiry_result.get('expire_date', 'Unknown')
                    print(f"[⏰ VIP已过期] {link} (过期时间: {expire_date})")
                    result['vip_status'] = 'expired'
                    result['vip_status_text'] = f"VIP已过期 (过期时间: {expire_date})"
                    result['gift_status'] = 'expired'
                    result['status_text'] = 'VIP已过期'
                    result['expire_date'] = expire_date  # 修正字段名
                else:
                    expire_date = expiry_result.get('expire_date', 'Unknown')
                    remaining_days = expiry_result.get('remaining_days', 0)
                    method = expiry_result.get('method', 'unknown')
                    print(f"[✅ VIP有效] {link} (过期时间: {expire_date}, 剩余: {remaining_days:.1f}天, 方法: {method})")
                    result['vip_status'] = 'valid'
                    result['vip_status_text'] = f"VIP有效 (剩余: {remaining_days:.1f}天)"
                    result['gift_status'] = 'available'
                    result['status_text'] = f'VIP有效 - 剩余{remaining_days:.1f}天'
                    result['expire_date'] = expire_date  # 修正字段名

                    # 如果是API方法获取的，添加邀请者信息
                    if method == 'api' and expiry_result.get('api_data'):
                        api_data = expiry_result['api_data']
                        # 检查邀请者信息的不同字段名
                        inviter_info = api_data.get('inviter', {})
                        if isinstance(inviter_info, dict) and 'nickname' in inviter_info:
                            result['sender'] = inviter_info['nickname']
                        elif 'inviterNickname' in api_data:
                            result['sender'] = api_data['inviterNickname']

                        # 检查总天数信息
                        if 'inviterTotalDays' in api_data:
                            total_days = api_data['inviterTotalDays']
                            result['gift_type'] = f"VIP邀请 ({total_days}天)"
                            result['gift_count'] = f"{total_days}天"
                        elif 'totalDays' in api_data:
                            result['gift_type'] = f"VIP邀请 ({api_data['totalDays']}天)"
                            result['gift_count'] = f"{api_data['totalDays']}天"

                        # 添加活动ID信息
                        if 'activityId' in api_data:
                            result['activity_id'] = api_data['activityId']

                return result

            # 如果不是VIP链接，进行常规礼品卡分析
            else:
                result = self.analyzer.analyze_gift_link(link)

                # 标记为非VIP链接
                result['is_vip_link'] = False

                # 如果常规分析也失败，但我们检测到了重定向URL，提供更多信息
                if result.get('status') != 'success' and redirect_url:
                    result['redirect_url'] = redirect_url
                    if 'gift-receive' in redirect_url:
                        result['message'] = '检测到礼品卡链接，但分析失败'
                    else:
                        result['message'] = '未知类型的链接'

                return result

        except Exception as e:
            return {
                'status': 'error',
                'message': f'分析失败: {str(e)}',
                'short_url': link,
                'is_vip_link': False
            }

    def run(self):
        try:
            results = []
            total = len(self.links)
            completed_count = 0

            # 使用线程锁保护共享变量
            lock = threading.Lock()

            def process_link_with_callback(link):
                """处理单个链接并发送实时结果"""
                nonlocal completed_count

                if not self.is_running:
                    return None

                # 检查暂停状态，如果暂停则等待
                self.pause_event.wait()

                # 再次检查是否需要停止（防止在暂停期间收到停止信号）
                if not self.is_running:
                    return None

                # 使用增强的分析方法，包含VIP有效期检查
                result = self.analyze_single_link(link)

                # 发送单个结果（实时显示）
                self.single_result_ready.emit(result)

                # 线程安全地更新进度
                with lock:
                    completed_count += 1

                    # 发送进度更新
                    status_text = "已暂停..." if self.is_paused else "分析中..."
                    if result['status'] == 'success':
                        # 如果是VIP链接，显示VIP状态
                        if result.get('is_vip_link', False):
                            vip_status = result.get('vip_status_text', 'VIP状态未知')
                            gift_type = result.get('gift_type', '')
                            method = result.get('vip_expiry_check', {}).get('method', '')
                            method_text = f"[{method.upper()}]" if method else ""
                            status_text = f"{method_text} {vip_status} | {gift_type}"
                        else:
                            status_text = f"{result.get('status_text', 'Unknown')} | {result.get('gift_type', '')}"
                    elif result['status'] == 'api_exception':
                        error_category = result.get('error_category', 'unknown')
                        status_text = f"API异常: {error_category}"
                    else:
                        status_text = f"错误: {result.get('message', 'Unknown')}"

                    self.progress_updated.emit(completed_count, total, status_text)

                return result

            # 使用ThreadPoolExecutor进行多线程处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_link = {executor.submit(process_link_with_callback, link): link
                                 for link in self.links}

                # 收集结果
                for future in as_completed(future_to_link):
                    if not self.is_running:
                        # 如果停止运行，取消所有未完成的任务
                        for f in future_to_link:
                            f.cancel()
                        break

                    try:
                        result = future.result()
                        if result is not None:
                            results.append(result)
                    except Exception as e:
                        link = future_to_link[future]
                        error_result = {
                            'status': 'error',
                            'message': f'处理失败: {str(e)}',
                            'short_url': link,
                            'is_vip_link': False
                        }
                        results.append(error_result)
                        self.single_result_ready.emit(error_result)

            if self.is_running:
                self.result_ready.emit(results)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def pause(self):
        """暂停分析"""
        self.is_paused = True
        self.pause_event.clear()  # 清除事件，使线程等待

    def resume(self):
        """继续分析"""
        self.is_paused = False
        self.pause_event.set()  # 设置事件，使线程继续

    def stop(self):
        """停止分析"""
        self.is_running = False
        self.pause_event.set()  # 确保线程不会卡在暂停状态

class FileOperationThread(QThread):
    """文件操作工作线程"""
    operation_completed = pyqtSignal(bool, str)  # 成功状态, 消息
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 状态信息

    def __init__(self, operation_type, file_path=None, data=None, **kwargs):
        super().__init__()
        self.operation_type = operation_type  # 'load', 'save', 'export'
        self.file_path = file_path
        self.data = data
        self.kwargs = kwargs
        self.result_data = None

    def run(self):
        """执行文件操作"""
        try:
            if self.operation_type == 'load':
                self._load_file()
            elif self.operation_type == 'save':
                self._save_file()
            elif self.operation_type == 'export':
                self._export_file()
            elif self.operation_type == 'save_multiple':
                self._save_multiple_files()
        except Exception as e:
            self.operation_completed.emit(False, f"操作失败: {str(e)}")

    def _load_file(self):
        """加载文件"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.result_data = content
            self.operation_completed.emit(True, f"已加载文件: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"加载文件失败: {str(e)}")

    def _save_file(self):
        """保存文件"""
        try:
            if self.kwargs.get('format') == 'json':
                import json
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
            else:
                # 文本格式
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    if isinstance(self.data, list):
                        # 处理大量数据时显示进度
                        total = len(self.data)
                        for i, item in enumerate(self.data):
                            if isinstance(item, dict):
                                f.write(item.get('short_url', str(item)) + '\n')
                            else:
                                f.write(str(item) + '\n')

                            # 每1000条更新一次进度
                            if i % 1000 == 0:
                                self.progress_updated.emit(i + 1, total, f"保存中...")
                    else:
                        f.write(str(self.data))

            count = len(self.data) if isinstance(self.data, list) else 1
            self.operation_completed.emit(True, f"已保存 {count} 项到: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"保存文件失败: {str(e)}")

    def _export_file(self):
        """导出文件"""
        try:
            export_type = self.kwargs.get('export_type', 'links')

            if export_type == 'available_links':
                links = [result.get('short_url', '') for result in self.data
                        if result['status'] == 'success' and result.get('gift_status') == 'available']
            elif export_type == 'invalid_links':
                links = [result.get('short_url', '') for result in self.data
                        if result['status'] != 'success' or result.get('gift_status') != 'available']
            else:
                links = self.data

            with open(self.file_path, 'w', encoding='utf-8') as f:
                total = len(links)
                for i, link in enumerate(links):
                    f.write(link + '\n')
                    # 每1000条更新一次进度
                    if i % 1000 == 0:
                        self.progress_updated.emit(i + 1, total, f"导出中...")

            self.operation_completed.emit(True, f"已导出 {len(links)} 个链接到: {self.file_path}")
        except Exception as e:
            self.operation_completed.emit(False, f"导出文件失败: {str(e)}")

    def _save_multiple_files(self):
        """保存多个文件"""
        try:
            files_data = self.kwargs.get('files_data', {})
            saved_count = 0

            for filename, links in files_data.items():
                if links:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(links))
                    saved_count += 1
                    self.progress_updated.emit(saved_count, len(files_data), f"保存 {filename}")

            self.operation_completed.emit(True, f"已保存 {saved_count} 个文件")
        except Exception as e:
            self.operation_completed.emit(False, f"保存多个文件失败: {str(e)}")




class GiftAnalyzerUI(QMainWindow):
    """礼品卡分析器主界面"""

    def __init__(self):
        super().__init__()
        # 礼品卡分析器相关
        self.analyzer_thread = None
        self.current_results = []
        self.is_analysis_paused = False  # 分析暂停状态

        # 文件操作线程
        self.file_operation_thread = None

        # 记录原始文件路径（用于覆盖原始文件功能）
        self.original_file_path = None

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("网易云音乐礼品卡分析器 - suimi")
        self.setGeometry(100, 100, 1400, 900)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建礼品卡分析器页面
        self.analyzer_tab = self.create_analyzer_tab()
        main_layout.addWidget(self.analyzer_tab)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def create_analyzer_tab(self):
        """创建礼品卡分析器标签页"""
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)

        # 创建工具栏区域
        toolbar_layout = QHBoxLayout()

        # 文件操作按钮
        self.load_btn = QPushButton("📁 加载链接文件")
        self.save_btn = QPushButton("💾 保存结果")
        self.clear_btn = QPushButton("🗑️ 清空数据")

        # 分析控制按钮
        self.analyze_btn = QPushButton("🚀 开始分析")
        self.pause_btn = QPushButton("⏸️ 暂停分析")
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("⏹️ 停止分析")
        self.stop_btn.setEnabled(False)

        # 线程数设置
        thread_label = QLabel("线程数:")
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, 20)
        self.thread_spinbox.setValue(5)

        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.analyze_btn)
        toolbar_layout.addWidget(self.pause_btn)
        toolbar_layout.addWidget(self.stop_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(thread_label)
        toolbar_layout.addWidget(self.thread_spinbox)
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.clear_btn)

        main_layout.addLayout(toolbar_layout)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：输入和控制区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 链接输入区域
        input_group = QGroupBox("📝 礼品卡链接输入")
        input_layout = QVBoxLayout(input_group)

        self.links_text = QTextEdit()
        self.links_text.setPlaceholderText("请输入礼品卡链接，每行一个...\n例如：http://163cn.tv/GBm6AHn")
        self.links_text.setMaximumHeight(200)

        links_info_layout = QHBoxLayout()
        self.links_count_label = QLabel("链接数量: 0")
        links_info_layout.addWidget(self.links_count_label)
        links_info_layout.addStretch()

        input_layout.addWidget(self.links_text)
        input_layout.addLayout(links_info_layout)
        left_layout.addWidget(input_group)

        # 进度显示区域
        progress_group = QGroupBox("📊 分析进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("就绪")

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        left_layout.addWidget(progress_group)

        # 统计信息区域
        stats_group = QGroupBox("📈 统计信息")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)

        stats_layout.addWidget(self.stats_text)
        left_layout.addWidget(stats_group)

        splitter.addWidget(left_widget)

        # 右侧：结果显示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 结果表格
        results_group = QGroupBox("🎁 分析结果")
        results_layout = QVBoxLayout(results_group)

        # 过滤选项
        filter_layout = QHBoxLayout()
        self.show_available_cb = QCheckBox("显示可领取")
        self.show_expired_cb = QCheckBox("显示已过期")
        self.show_claimed_cb = QCheckBox("显示已领取")
        self.show_error_cb = QCheckBox("显示错误")
        self.show_api_exception_cb = QCheckBox("显示API异常")

        # VIP相关过滤选项
        self.show_vip_valid_cb = QCheckBox("显示VIP有效")
        self.show_vip_expired_cb = QCheckBox("显示VIP过期")

        self.show_available_cb.setChecked(True)
        self.show_expired_cb.setChecked(True)
        self.show_claimed_cb.setChecked(True)
        self.show_error_cb.setChecked(True)
        self.show_api_exception_cb.setChecked(True)
        self.show_vip_valid_cb.setChecked(True)
        self.show_vip_expired_cb.setChecked(True)

        filter_layout.addWidget(QLabel("过滤:"))
        filter_layout.addWidget(self.show_available_cb)
        filter_layout.addWidget(self.show_expired_cb)
        filter_layout.addWidget(self.show_claimed_cb)
        filter_layout.addWidget(self.show_error_cb)
        filter_layout.addWidget(self.show_api_exception_cb)
        filter_layout.addWidget(self.show_vip_valid_cb)
        filter_layout.addWidget(self.show_vip_expired_cb)
        filter_layout.addStretch()

        # 删除失效链接按钮
        self.delete_invalid_btn = QPushButton("🗑️ 删除失效链接")
        self.delete_invalid_btn.setEnabled(False)
        filter_layout.addWidget(self.delete_invalid_btn)

        # 同步更新按钮
        self.sync_results_btn = QPushButton("🔄 同步结果")
        self.sync_results_btn.setEnabled(False)
        self.sync_results_btn.setToolTip("将当前输入的链接与分析结果同步")
        filter_layout.addWidget(self.sync_results_btn)

        results_layout.addLayout(filter_layout)

        # 创建分页标签
        self.results_tabs = QTabWidget()

        # 礼品卡结果表格
        self.gift_results_widget = QWidget()
        self.gift_results_layout = QVBoxLayout(self.gift_results_widget)
        self.gift_results_table = QTableWidget()
        self.setup_gift_results_table()
        self.gift_results_layout.addWidget(self.gift_results_table)

        # VIP邀请结果表格
        self.vip_results_widget = QWidget()
        self.vip_results_layout = QVBoxLayout(self.vip_results_widget)
        self.vip_results_table = QTableWidget()
        self.setup_vip_results_table()
        self.vip_results_layout.addWidget(self.vip_results_table)

        # 添加标签页
        self.results_tabs.addTab(self.gift_results_widget, "🎁 礼品卡列表")
        self.results_tabs.addTab(self.vip_results_widget, "👑 VIP邀请列表")

        # 保持向后兼容性
        self.results_table = self.gift_results_table  # 默认指向礼品卡表格

        results_layout.addWidget(self.results_tabs)
        right_layout.addWidget(results_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

        return tab_widget

    def setup_results_table(self, table, headers):
        """设置结果表格"""
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # 设置列宽
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 序号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 链接
        if len(headers) > 2:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 重定向链接
        if len(headers) > 3:
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态

        # 设置表格属性
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')

        load_action = QAction('加载链接文件', self)
        load_action.triggered.connect(self.load_links_file)
        file_menu.addAction(load_action)

        save_action = QAction('保存结果', self)
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu('工具')

        # 礼品卡分析器工具
        analyzer_submenu = tools_menu.addMenu('礼品卡分析器')

        export_available_action = QAction('导出可领取链接', self)
        export_available_action.triggered.connect(self.export_available_links)
        analyzer_submenu.addAction(export_available_action)

        export_invalid_action = QAction('导出失效链接', self)
        export_invalid_action.triggered.connect(self.export_invalid_links)
        analyzer_submenu.addAction(export_invalid_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_gift_results_table(self):
        """设置礼品卡结果表格"""
        headers = ['状态', '链接', '礼品类型', '发送者', '数量', '过期时间', '价值', '异常详情']
        self.gift_results_table.setColumnCount(len(headers))
        self.gift_results_table.setHorizontalHeaderLabels(headers)

        # 设置列宽
        header = self.gift_results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        # 设置表格属性
        self.gift_results_table.setAlternatingRowColors(True)
        self.gift_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.gift_results_table.setSortingEnabled(True)

    def setup_vip_results_table(self):
        """设置VIP邀请结果表格"""
        headers = ['状态', '链接', '邀请者', '活动类型', '有效期', '剩余天数', '检测方法', '异常详情']
        self.vip_results_table.setColumnCount(len(headers))
        self.vip_results_table.setHorizontalHeaderLabels(headers)

        # 设置列宽
        header = self.vip_results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        # 设置表格属性
        self.vip_results_table.setAlternatingRowColors(True)
        self.vip_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vip_results_table.setSortingEnabled(True)

    def setup_results_table(self):
        """设置结果表格 - 保持向后兼容性"""
        self.setup_gift_results_table()

    def setup_connections(self):
        """设置信号连接"""
        # 礼品卡分析器连接
        self.load_btn.clicked.connect(self.load_links_file)
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.pause_btn.clicked.connect(self.toggle_pause_analysis)
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.save_btn.clicked.connect(self.save_results)
        self.clear_btn.clicked.connect(self.clear_data)
        self.delete_invalid_btn.clicked.connect(self.delete_invalid_links)
        self.sync_results_btn.clicked.connect(self.sync_results_with_input)

        # 过滤选项连接
        self.show_available_cb.toggled.connect(self.update_table_filter)
        self.show_expired_cb.toggled.connect(self.update_table_filter)
        self.show_claimed_cb.toggled.connect(self.update_table_filter)
        self.show_error_cb.toggled.connect(self.update_table_filter)
        self.show_api_exception_cb.toggled.connect(self.update_table_filter)
        self.show_vip_valid_cb.toggled.connect(self.update_table_filter)
        self.show_vip_expired_cb.toggled.connect(self.update_table_filter)

        # 链接文本变化
        self.links_text.textChanged.connect(self.update_links_count)

    # ==================== 礼品卡分析器方法 ====================

    def load_links_from_file(self):
        """从文件加载链接"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择链接文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            # 检查是否有文件操作线程正在运行
            if self.file_operation_thread and self.file_operation_thread.isRunning():
                QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
                return

            # 启动文件加载线程
            self.file_operation_thread = FileOperationThread('load', file_path)
            self.file_operation_thread.operation_completed.connect(self.on_file_load_completed)
            self.file_operation_thread.start()

            self.status_bar.showMessage("正在加载文件...")

    def on_file_load_completed(self, success, message):
        """文件加载完成回调"""
        if success:
            content = self.file_operation_thread.result_data
            self.links_text.setPlainText(content)
            self.update_links_count()
            self.status_bar.showMessage(message)
            # 记录原始文件路径
            self.original_file_path = self.file_operation_thread.file_path
        else:
            QMessageBox.critical(self, "错误", message)
            self.status_bar.showMessage("文件加载失败")

    def start_analysis(self):
        """开始分析"""
        links_text = self.links_text.toPlainText().strip()
        if not links_text:
            QMessageBox.warning(self, "警告", "请输入要分析的链接！")
            return

        # 解析链接
        links = [link.strip() for link in links_text.split('\n') if link.strip()]
        if not links:
            QMessageBox.warning(self, "警告", "没有找到有效的链接！")
            return

        # 获取线程数
        max_workers = self.thread_spinbox.value()

        # 禁用相关按钮
        self.analyze_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.is_analysis_paused = False

        # 清空之前的结果
        self.current_results = []
        self.gift_results_table.setRowCount(0)
        self.vip_results_table.setRowCount(0)
        self.stats_text.clear()

        # 重置进度条
        self.progress_bar.setMaximum(len(links))
        self.progress_bar.setValue(0)

        # 启动分析线程
        self.analyzer_thread = AnalyzerThread(links, max_workers)
        self.analyzer_thread.progress_updated.connect(self.update_progress)
        self.analyzer_thread.result_ready.connect(self.analysis_completed)
        self.analyzer_thread.single_result_ready.connect(self.add_single_result)
        self.analyzer_thread.error_occurred.connect(self.analysis_error)
        self.analyzer_thread.start()

        self.status_bar.showMessage("正在分析链接...")

    # ==================== 礼品卡分析器方法 ====================

    def load_links_file(self):
        """加载链接文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择链接文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            # 检查是否有文件操作线程正在运行
            if self.file_operation_thread and self.file_operation_thread.isRunning():
                QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
                return

            # 启动文件加载线程
            self.file_operation_thread = FileOperationThread('load', file_path)
            self.file_operation_thread.operation_completed.connect(self.on_file_load_completed)
            self.file_operation_thread.start()

            self.status_bar.showMessage("正在加载文件...")

    def on_file_load_completed(self, success, message):
        """文件加载完成回调"""
        if success:
            content = self.file_operation_thread.result_data
            self.links_text.setPlainText(content)
            # 记录原始文件路径
            self.original_file_path = self.file_operation_thread.file_path
            self.status_bar.showMessage(message)
        else:
            QMessageBox.critical(self, "错误", message)
            self.status_bar.showMessage("文件加载失败")

    def update_links_count(self):
        """更新链接数量显示"""
        text = self.links_text.toPlainText().strip()
        if text:
            links = [line.strip() for line in text.split('\n') if line.strip()]
            count = len(links)
        else:
            count = 0
        self.links_count_label.setText(f"链接数量: {count}")

    def start_analysis(self):
        """开始分析"""
        text = self.links_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请先输入或加载礼品卡链接！")
            return

        links = [line.strip() for line in text.split('\n') if line.strip()]
        if not links:
            QMessageBox.warning(self, "警告", "没有找到有效的链接！")
            return

        # 禁用相关按钮
        self.analyze_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.delete_invalid_btn.setEnabled(False)
        self.is_analysis_paused = False

        # 清空之前的结果
        self.current_results = []
        self.gift_results_table.setRowCount(0)
        self.vip_results_table.setRowCount(0)
        self.stats_text.clear()

        # 重置进度条
        self.progress_bar.setMaximum(len(links))
        self.progress_bar.setValue(0)

        # 启动分析线程
        max_workers = self.thread_spinbox.value()
        self.analyzer_thread = AnalyzerThread(links, max_workers)
        self.analyzer_thread.progress_updated.connect(self.update_progress)
        self.analyzer_thread.result_ready.connect(self.analysis_completed)
        self.analyzer_thread.single_result_ready.connect(self.add_single_result)  # 新增实时结果连接
        self.analyzer_thread.error_occurred.connect(self.analysis_error)
        self.analyzer_thread.start()

        self.status_bar.showMessage("分析中...")

    def stop_analysis(self):
        """停止分析"""
        if self.analyzer_thread and self.analyzer_thread.isRunning():
            self.analyzer_thread.stop()
            self.analyzer_thread.wait()

        self.analyze_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.is_analysis_paused = False
        self.pause_btn.setText("⏸️ 暂停分析")  # 重置按钮文本
        self.status_bar.showMessage("分析已停止")

    def toggle_pause_analysis(self):
        """切换暂停/继续分析"""
        if not self.analyzer_thread or not self.analyzer_thread.isRunning():
            return

        if self.is_analysis_paused:
            # 当前是暂停状态，点击继续
            self.analyzer_thread.resume()
            self.is_analysis_paused = False
            self.pause_btn.setText("⏸️ 暂停分析")
            self.status_bar.showMessage("分析已继续...")
        else:
            # 当前是运行状态，点击暂停
            self.analyzer_thread.pause()
            self.is_analysis_paused = True
            self.pause_btn.setText("▶️ 继续分析")
            self.status_bar.showMessage("分析已暂停")

    def update_progress(self, current, total, status):
        """更新进度"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"进度: {current}/{total} - {status}")

    def add_single_result(self, result):
        """实时添加单个分析结果到表格"""
        # 将结果添加到当前结果列表
        self.current_results.append(result)

        # 检查是否应该显示这个结果（根据过滤条件）
        if self.should_show_result(result):
            # 在表格中添加新行
            self.add_result_to_table(result)

        # 实时更新统计信息
        self.update_statistics()

    def should_show_result(self, result):
        """检查结果是否应该根据当前过滤条件显示"""
        status = result.get('status', 'unknown')

        if status == 'success':
            gift_status = result.get('gift_status', 'unknown')
            is_vip_link = result.get('is_vip_link', False)

            # 基本状态过滤
            show_basic = False
            if gift_status == 'available' and self.show_available_cb.isChecked():
                show_basic = True
            elif gift_status == 'expired' and self.show_expired_cb.isChecked():
                show_basic = True
            elif gift_status == 'claimed' and self.show_claimed_cb.isChecked():
                show_basic = True

            # VIP状态过滤
            if is_vip_link:
                vip_status = result.get('vip_status', 'unknown')
                if vip_status == 'valid' and self.show_vip_valid_cb.isChecked():
                    return show_basic
                elif vip_status == 'expired' and self.show_vip_expired_cb.isChecked():
                    return show_basic
                else:
                    return False  # VIP链接但不符合VIP过滤条件
            else:
                return show_basic  # 非VIP链接，只看基本状态

        elif status == 'api_exception':
            return self.show_api_exception_cb.isChecked()
        elif status in ['system_exception', 'invalid', 'error']:
            return self.show_error_cb.isChecked()

        return False

    def add_result_to_table(self, result):
        """将单个结果添加到对应的表格"""
        if result.get('is_vip_link', False):
            # VIP链接添加到VIP表格
            current_row = self.vip_results_table.rowCount()
            self.vip_results_table.insertRow(current_row)
            self.populate_vip_table_row(current_row, result)
        else:
            # 礼品卡链接添加到礼品卡表格
            current_row = self.gift_results_table.rowCount()
            self.gift_results_table.insertRow(current_row)
            self.populate_gift_table_row(current_row, result)

    def populate_gift_table_row(self, row, result):
        """填充礼品卡表格行数据"""
        # 状态
        status_text = self.get_status_display(result)
        self.gift_results_table.setItem(row, 0, QTableWidgetItem(status_text))

        # 链接
        link = result.get('short_url', '')
        self.gift_results_table.setItem(row, 1, QTableWidgetItem(link))

        status = result.get('status', 'unknown')

        if status == 'success':
            # 礼品类型
            gift_type = result.get('gift_type', '')
            self.gift_results_table.setItem(row, 2, QTableWidgetItem(gift_type))

            # 发送者
            sender = result.get('sender_name', '')
            self.gift_results_table.setItem(row, 3, QTableWidgetItem(sender))

            # 数量
            available = result.get('available_count', 0)
            total = result.get('total_count', 0)
            count_text = f"{available}/{total}"
            self.gift_results_table.setItem(row, 4, QTableWidgetItem(count_text))

            # 过期时间
            expire_date = result.get('expire_date', '')
            self.gift_results_table.setItem(row, 5, QTableWidgetItem(expire_date))

            # 价值
            price = result.get('gift_price', 0)
            price_text = f"¥{price:.1f}"
            self.gift_results_table.setItem(row, 6, QTableWidgetItem(price_text))

            # 异常详情（成功状态下为空）
            self.gift_results_table.setItem(row, 7, QTableWidgetItem(''))

        elif status == 'api_exception':
            # API异常信息
            error_msg = result.get('error_message', result.get('message', ''))
            self.gift_results_table.setItem(row, 2, QTableWidgetItem('API异常'))

            # 异常详情
            error_category = result.get('error_category', 'unknown')
            category_names = {
                'connection_error': '连接错误',
                'timeout_error': '超时错误',
                'http_error': 'HTTP错误',
                'redirect_error': '重定向错误',
                'json_decode_error': '响应格式错误',
                'api_business_error': 'API业务错误',
                'missing_data': '数据缺失'
            }
            category_display = category_names.get(error_category, error_category)
            self.gift_results_table.setItem(row, 7, QTableWidgetItem(f"{category_display}: {error_msg}"))

            # 清空其他列
            for col in range(3, 7):
                self.gift_results_table.setItem(row, col, QTableWidgetItem(''))

        else:
            # 其他错误信息
            error_msg = result.get('message', '')
            self.gift_results_table.setItem(row, 2, QTableWidgetItem(error_msg))
            self.gift_results_table.setItem(row, 7, QTableWidgetItem(''))
            for col in range(3, 7):
                self.gift_results_table.setItem(row, col, QTableWidgetItem(''))

    def populate_vip_table_row(self, row, result):
        """填充VIP表格行数据"""
        # 状态
        status_text = self.get_status_display(result)
        vip_status_item = QTableWidgetItem(status_text)

        # 根据VIP状态设置颜色
        vip_status = result.get('vip_status', 'unknown')
        if vip_status == 'valid':
            vip_status_item.setBackground(Qt.GlobalColor.green)
            vip_status_item.setForeground(Qt.GlobalColor.white)
        elif vip_status == 'expired':
            vip_status_item.setBackground(Qt.GlobalColor.red)
            vip_status_item.setForeground(Qt.GlobalColor.white)
        elif vip_status == 'expiry_check_failed':
            vip_status_item.setBackground(Qt.GlobalColor.yellow)
            vip_status_item.setForeground(Qt.GlobalColor.black)

        self.vip_results_table.setItem(row, 0, vip_status_item)

        # 链接
        link = result.get('short_url', '')
        self.vip_results_table.setItem(row, 1, QTableWidgetItem(link))

        status = result.get('status', 'unknown')

        if status == 'success':
            # 邀请者
            sender = result.get('sender', '')
            self.vip_results_table.setItem(row, 2, QTableWidgetItem(sender))

            # 活动类型
            gift_type = result.get('gift_type', 'VIP邀请')
            self.vip_results_table.setItem(row, 3, QTableWidgetItem(gift_type))

            # 有效期（北京时间）
            expire_date = result.get('expire_date', '')
            self.vip_results_table.setItem(row, 4, QTableWidgetItem(expire_date))

            # 剩余天数
            expiry_check = result.get('vip_expiry_check', {})
            remaining_days = expiry_check.get('remaining_days', 0)
            if remaining_days > 0:
                remaining_text = f"{remaining_days:.1f}天"
            else:
                remaining_text = "已过期"
            self.vip_results_table.setItem(row, 5, QTableWidgetItem(remaining_text))

            # 检测方法
            method = expiry_check.get('method', 'unknown')
            method_text = {'api': 'API调用', 'page': '页面解析', 'error': '检测失败'}.get(method, method.upper())
            self.vip_results_table.setItem(row, 6, QTableWidgetItem(method_text))

            # 异常详情（成功状态下为空）
            error_info = expiry_check.get('error', '')
            self.vip_results_table.setItem(row, 7, QTableWidgetItem(error_info or ''))

        else:
            # 错误信息
            error_msg = result.get('message', '')
            self.vip_results_table.setItem(row, 3, QTableWidgetItem(error_msg))
            self.vip_results_table.setItem(row, 7, QTableWidgetItem(error_msg))
            for col in [2, 4, 5, 6]:
                self.vip_results_table.setItem(row, col, QTableWidgetItem(''))

    def populate_table_row(self, row, result):
        """填充表格行数据 - 保持向后兼容性"""
        if result.get('is_vip_link', False):
            self.populate_vip_table_row(row, result)
        else:
            self.populate_gift_table_row(row, result)

        # 链接
        link = result.get('short_url', '')
        self.results_table.setItem(row, 1, QTableWidgetItem(link))

        status = result.get('status', 'unknown')

        if status == 'success':
            # 礼品类型
            gift_type = result.get('gift_type', '')
            self.results_table.setItem(row, 2, QTableWidgetItem(gift_type))

            # 发送者
            sender = result.get('sender_name', '')
            self.results_table.setItem(row, 3, QTableWidgetItem(sender))

            # 数量
            available = result.get('available_count', 0)
            total = result.get('total_count', 0)
            count_text = f"{available}/{total}"
            self.results_table.setItem(row, 4, QTableWidgetItem(count_text))

            # 过期时间
            expire_date = result.get('expire_date', '')
            self.results_table.setItem(row, 5, QTableWidgetItem(expire_date))

            # 价值
            price = result.get('gift_price', 0)
            price_text = f"¥{price:.1f}"
            self.results_table.setItem(row, 6, QTableWidgetItem(price_text))

            # VIP状态
            vip_status_text = ''
            if result.get('is_vip_link', False):
                vip_status_text = result.get('vip_status_text', 'VIP状态未知')

                # 添加检测方法信息
                expiry_check = result.get('vip_expiry_check', {})
                method = expiry_check.get('method', '')
                if method:
                    method_text = {'api': 'API', 'page': '页面', 'error': '错误'}.get(method, method.upper())
                    vip_status_text = f"[{method_text}] {vip_status_text}"

                # 根据VIP状态设置颜色
                vip_status = result.get('vip_status', 'unknown')
                vip_item = QTableWidgetItem(vip_status_text)
                if vip_status == 'valid':
                    vip_item.setBackground(Qt.GlobalColor.green)
                    vip_item.setForeground(Qt.GlobalColor.white)
                elif vip_status == 'expired':
                    vip_item.setBackground(Qt.GlobalColor.red)
                    vip_item.setForeground(Qt.GlobalColor.white)
                elif vip_status == 'expiry_check_failed':
                    vip_item.setBackground(Qt.GlobalColor.yellow)
                    vip_item.setForeground(Qt.GlobalColor.black)
                self.results_table.setItem(row, 7, vip_item)
            else:
                non_vip_item = QTableWidgetItem('非VIP链接')
                non_vip_item.setForeground(Qt.GlobalColor.gray)
                self.results_table.setItem(row, 7, non_vip_item)

            # 异常详情（成功状态下为空）
            self.results_table.setItem(row, 8, QTableWidgetItem(''))

        elif status == 'api_exception':
            # API异常信息
            error_msg = result.get('error_message', result.get('message', ''))
            self.results_table.setItem(row, 2, QTableWidgetItem('API异常'))

            # 异常详情
            error_category = result.get('error_category', 'unknown')
            category_names = {
                'connection_error': '连接错误',
                'timeout': '请求超时',
                'server_error': '服务器错误',
                'rate_limit': '频率限制',
                'forbidden': '访问拒绝',
                'json_decode_error': '响应格式错误',
                'api_business_error': 'API业务错误',
                'missing_data': '数据缺失'
            }
            category_display = category_names.get(error_category, error_category)
            self.results_table.setItem(row, 8, QTableWidgetItem(f"{category_display}: {error_msg}"))

            # 清空其他列
            for col in range(3, 8):
                self.results_table.setItem(row, col, QTableWidgetItem(''))

        else:
            # 其他错误信息
            error_msg = result.get('message', '')
            self.results_table.setItem(row, 2, QTableWidgetItem(error_msg))
            self.results_table.setItem(row, 8, QTableWidgetItem(''))
            for col in range(3, 8):
                self.results_table.setItem(row, col, QTableWidgetItem(''))

    def analysis_completed(self, results):
        """分析完成"""
        # 注意：results 应该与 self.current_results 相同，因为我们已经实时添加了
        # 这里主要是做最终的清理和状态恢复工作

        # 确保结果一致性（防止线程同步问题）
        if len(self.current_results) != len(results):
            print(f"警告：结果数量不一致 - 实时: {len(self.current_results)}, 最终: {len(results)}")
            self.current_results = results
            # 重新构建表格以确保一致性
            self.update_table_filter()

        # 最终更新统计信息
        self.update_statistics()

        # 恢复按钮状态
        self.analyze_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.delete_invalid_btn.setEnabled(True)
        self.sync_results_btn.setEnabled(True)
        self.is_analysis_paused = False
        self.pause_btn.setText("⏸️ 暂停分析")  # 重置按钮文本

        self.status_bar.showMessage(f"分析完成，共处理 {len(results)} 个链接")

        # 显示完成消息
        success_count = len([r for r in results if r['status'] == 'success'])
        api_exception_count = len([r for r in results if r['status'] == 'api_exception'])
        other_error_count = len(results) - success_count - api_exception_count

        completion_msg = f"分析完成！\n\n"
        completion_msg += f"📊 总链接数: {len(results)}\n"
        completion_msg += f"✅ 成功分析: {success_count}\n"
        completion_msg += f"⚠️ API异常: {api_exception_count}\n"
        completion_msg += f"❌ 其他错误: {other_error_count}"

        QMessageBox.information(self, "分析完成", completion_msg)

    def analysis_error(self, error_msg):
        """分析出错"""
        self.analyze_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.is_analysis_paused = False
        self.pause_btn.setText("⏸️ 暂停分析")  # 重置按钮文本
        self.status_bar.showMessage("分析出错")
        QMessageBox.critical(self, "分析错误", f"分析过程中出现错误:\n{error_msg}")

    def update_results_table(self):
        """更新结果表格"""
        if not self.current_results:
            return

        # 过滤结果
        filtered_results = self.filter_results()

        self.results_table.setRowCount(len(filtered_results))

        for row, result in enumerate(filtered_results):
            # 状态
            status_text = self.get_status_display(result)
            self.results_table.setItem(row, 0, QTableWidgetItem(status_text))

            # 链接
            link = result.get('short_url', '')
            self.results_table.setItem(row, 1, QTableWidgetItem(link))

            status = result.get('status', 'unknown')

            if status == 'success':
                # 礼品类型
                gift_type = result.get('gift_type', '')
                self.results_table.setItem(row, 2, QTableWidgetItem(gift_type))

                # 发送者
                sender = result.get('sender_name', '')
                self.results_table.setItem(row, 3, QTableWidgetItem(sender))

                # 数量
                available = result.get('available_count', 0)
                total = result.get('total_count', 0)
                count_text = f"{available}/{total}"
                self.results_table.setItem(row, 4, QTableWidgetItem(count_text))

                # 过期时间
                expire_date = result.get('expire_date', '')
                self.results_table.setItem(row, 5, QTableWidgetItem(expire_date))

                # 价值
                price = result.get('gift_price', 0)
                price_text = f"¥{price:.1f}"
                self.results_table.setItem(row, 6, QTableWidgetItem(price_text))

                # 异常详情（成功状态下为空）
                self.results_table.setItem(row, 7, QTableWidgetItem(''))

            elif status == 'api_exception':
                # API异常信息
                error_msg = result.get('error_message', result.get('message', ''))
                self.results_table.setItem(row, 2, QTableWidgetItem('API异常'))

                # 异常详情
                error_category = result.get('error_category', 'unknown')
                category_names = {
                    'connection_error': '连接错误',
                    'timeout': '请求超时',
                    'server_error': '服务器错误',
                    'rate_limit': '频率限制',
                    'forbidden': '访问拒绝',
                    'json_decode_error': '响应格式错误',
                    'api_business_error': 'API业务错误',
                    'missing_data': '数据缺失'
                }
                category_display = category_names.get(error_category, error_category)
                self.results_table.setItem(row, 7, QTableWidgetItem(f"{category_display}: {error_msg}"))

                # 清空其他列
                for col in range(3, 7):
                    self.results_table.setItem(row, col, QTableWidgetItem(''))

            else:
                # 其他错误信息
                error_msg = result.get('message', '')
                self.results_table.setItem(row, 2, QTableWidgetItem(error_msg))
                self.results_table.setItem(row, 7, QTableWidgetItem(''))
                for col in range(3, 7):
                    self.results_table.setItem(row, col, QTableWidgetItem(''))

    def get_status_display(self, result):
        """获取状态显示文本"""
        status = result.get('status', 'unknown')

        if status == 'success':
            gift_status = result.get('gift_status', 'unknown')
            if gift_status == 'available':
                return "✅ 可领取"
            elif gift_status == 'expired':
                return "⏰ 已过期"
            elif gift_status == 'claimed':
                return "📦 已领取"
            else:
                return "❓ 未知"
        elif status == 'api_exception':
            error_category = result.get('error_category', 'unknown')
            if error_category == 'connection_error':
                return "🌐 连接异常"
            elif error_category == 'timeout':
                return "⏱️ 超时异常"
            elif error_category == 'server_error':
                return "🔥 服务器异常"
            elif error_category == 'rate_limit':
                return "🚦 频率限制"
            elif error_category == 'forbidden':
                return "🚫 访问拒绝"
            else:
                return "⚠️ API异常"
        elif status == 'system_exception':
            return "💥 系统异常"
        elif status == 'invalid':
            return "🚫 无效链接"
        else:
            return "❌ 错误"

    def filter_results(self):
        """过滤结果"""
        if not self.current_results:
            return []

        filtered = []
        for result in self.current_results:
            if self.should_show_result(result):
                filtered.append(result)

        return filtered

    def update_table_filter(self):
        """更新表格过滤"""
        # 清空两个表格
        self.gift_results_table.setRowCount(0)
        self.vip_results_table.setRowCount(0)

        # 重新添加符合过滤条件的结果
        for result in self.current_results:
            if self.should_show_result(result):
                self.add_result_to_table(result)

    def update_statistics(self):
        """更新统计信息"""
        if not self.current_results:
            return

        total = len(self.current_results)
        success_count = len([r for r in self.current_results if r['status'] == 'success'])
        api_exception_count = len([r for r in self.current_results if r['status'] == 'api_exception'])
        system_exception_count = len([r for r in self.current_results if r['status'] == 'system_exception'])
        invalid_count = len([r for r in self.current_results if r['status'] in ['invalid', 'error']])

        stats_text = f"📊 分析统计\n"
        stats_text += f"总链接数: {total}\n"
        stats_text += f"成功分析: {success_count}\n"
        stats_text += f"API异常: {api_exception_count}\n"
        stats_text += f"系统异常: {system_exception_count}\n"
        stats_text += f"无效链接: {invalid_count}\n\n"

        if success_count > 0:
            # 状态统计
            status_count = {}
            gift_types = {}
            vip_status_count = {}
            total_value = 0
            available_value = 0
            vip_count = 0
            non_vip_count = 0

            for result in self.current_results:
                if result['status'] == 'success':
                    status = result.get('gift_status', 'unknown')
                    status_count[status] = status_count.get(status, 0) + 1

                    gift_type = result.get('gift_type', 'Unknown')
                    gift_types[gift_type] = gift_types.get(gift_type, 0) + 1

                    price = result.get('gift_price', 0)
                    total_value += price
                    if status == 'available':
                        available_value += price

                    # VIP状态统计
                    is_vip_link = result.get('is_vip_link', False)
                    if is_vip_link:
                        vip_count += 1
                        vip_status = result.get('vip_status', 'unknown')
                        vip_status_count[vip_status] = vip_status_count.get(vip_status, 0) + 1
                    else:
                        non_vip_count += 1

            stats_text += "🎁 状态分布:\n"
            for status, count in status_count.items():
                percentage = (count / success_count) * 100
                status_name = {
                    'available': '可领取',
                    'expired': '已过期',
                    'claimed': '已领取'
                }.get(status, status)
                stats_text += f"  {status_name}: {count} ({percentage:.1f}%)\n"

            stats_text += f"\n🎯 礼品类型:\n"
            for gift_type, count in gift_types.items():
                percentage = (count / success_count) * 100
                stats_text += f"  {gift_type}: {count} ({percentage:.1f}%)\n"

            stats_text += f"\n💰 价值统计:\n"
            stats_text += f"  总价值: ¥{total_value:.1f}\n"
            stats_text += f"  可领取价值: ¥{available_value:.1f}\n"
            if total_value > 0:
                stats_text += f"  可领取率: {(available_value/total_value*100):.1f}%\n"

            # VIP统计信息
            if vip_count > 0 or non_vip_count > 0:
                stats_text += f"\n🎯 VIP链接统计:\n"
                stats_text += f"  VIP链接: {vip_count}\n"
                stats_text += f"  非VIP链接: {non_vip_count}\n"

                if vip_count > 0:
                    stats_text += f"\n🔍 VIP状态分布:\n"
                    for vip_status, count in vip_status_count.items():
                        percentage = (count / vip_count) * 100
                        status_name = {
                            'valid': 'VIP有效',
                            'expired': 'VIP过期',
                            'expiry_check_failed': '有效期检查失败'
                        }.get(vip_status, vip_status)
                        stats_text += f"  {status_name}: {count} ({percentage:.1f}%)\n"

                    # 检测方法统计
                    method_count = {}
                    for result in self.current_results:
                        if result.get('is_vip_link', False) and result['status'] == 'success':
                            method = result.get('vip_expiry_check', {}).get('method', 'unknown')
                            method_count[method] = method_count.get(method, 0) + 1

                    if method_count:
                        stats_text += f"\n🛠️ VIP检测方法:\n"
                        for method, count in method_count.items():
                            percentage = (count / vip_count) * 100
                            method_name = {
                                'api': 'API调用',
                                'page': '页面解析',
                                'error': '检测失败'
                            }.get(method, method)
                            stats_text += f"  {method_name}: {count} ({percentage:.1f}%)\n"

        # API异常详细统计
        if api_exception_count > 0:
            api_exception_categories = {}
            for result in self.current_results:
                if result['status'] == 'api_exception':
                    category = result.get('error_category', 'unknown')
                    api_exception_categories[category] = api_exception_categories.get(category, 0) + 1

            stats_text += f"\n⚠️ API异常分类:\n"
            category_names = {
                'connection_error': '连接错误',
                'timeout': '请求超时',
                'server_error': '服务器错误',
                'rate_limit': '频率限制',
                'forbidden': '访问拒绝',
                'json_decode_error': '响应格式错误',
                'api_business_error': 'API业务错误',
                'missing_data': '数据缺失'
            }

            for category, count in api_exception_categories.items():
                percentage = (count / api_exception_count) * 100
                category_display = category_names.get(category, category)
                stats_text += f"  {category_display}: {count} ({percentage:.1f}%)\n"

        self.stats_text.setPlainText(stats_text)

    def delete_invalid_links(self):
        """删除失效链接并同步更新分析结果"""
        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有分析结果可以处理！")
            return

        # 详细统计各种状态的链接
        valid_results = []
        valid_links = []
        expired_links = []
        claimed_links = []
        api_exception_links = []
        error_links = []

        for result in self.current_results:
            status = result.get('status', 'unknown')
            short_url = result.get('short_url', '')

            if status == 'success':
                gift_status = result.get('gift_status', 'unknown')

                if gift_status == 'available':
                    # 可领取的链接 - 保留
                    valid_results.append(result)
                    valid_links.append(short_url)
                elif gift_status == 'expired':
                    # 已过期的链接 - 删除
                    expired_links.append(short_url)
                elif gift_status == 'claimed':
                    # 已领取的链接 - 删除
                    claimed_links.append(short_url)
                else:
                    # 其他状态 - 删除
                    error_links.append(short_url)
            elif status == 'api_exception':
                # API异常的链接 - 删除
                api_exception_links.append(short_url)
            else:
                # 其他分析失败的链接 - 删除
                error_links.append(short_url)

        total_invalid = len(expired_links) + len(claimed_links) + len(api_exception_links) + len(error_links)

        if total_invalid == 0:
            QMessageBox.information(self, "信息", "没有找到失效的链接！\n所有链接都是可领取状态。")
            return

        # 显示详细的删除统计信息和文件操作选项
        self.show_delete_confirmation_dialog(valid_links, expired_links, claimed_links, api_exception_links, error_links, valid_results)

    def show_delete_confirmation_dialog(self, valid_links, expired_links, claimed_links, api_exception_links, error_links, valid_results):
        """显示删除确认对话框，包含文件操作选项"""
        total_invalid = len(expired_links) + len(claimed_links) + len(api_exception_links) + len(error_links)

        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("删除失效链接确认")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        # 统计信息
        stats_label = QLabel()
        stats_text = f"删除统计详情：\n\n"
        stats_text += f"📊 总链接数: {len(self.current_results)}\n"
        stats_text += f"✅ 保留可领取: {len(valid_links)}\n"
        stats_text += f"⏰ 删除已过期: {len(expired_links)}\n"
        stats_text += f"📦 删除已领取: {len(claimed_links)}\n"
        stats_text += f"⚠️ 删除API异常: {len(api_exception_links)}\n"
        stats_text += f"❌ 删除错误链接: {len(error_links)}\n"
        stats_text += f"\n🗑️ 总删除数量: {total_invalid}"
        stats_label.setText(stats_text)
        layout.addWidget(stats_label)

        # 文件操作选项
        file_group = QGroupBox("📁 文件操作选项")
        file_layout = QVBoxLayout(file_group)

        # 选项1：仅更新界面
        self.option_ui_only = QCheckBox("仅更新界面（不修改文件）")
        self.option_ui_only.setChecked(True)
        file_layout.addWidget(self.option_ui_only)

        # 选项2：保存清理后的链接到新文件
        self.option_save_cleaned = QCheckBox("保存清理后的链接到新文件")
        file_layout.addWidget(self.option_save_cleaned)

        # 选项3：覆盖原始文件（如果是从文件加载的）
        self.option_overwrite_original = QCheckBox("覆盖原始文件（谨慎操作）")
        if self.original_file_path:
            self.option_overwrite_original.setToolTip(f"将覆盖文件: {self.original_file_path}")
        else:
            self.option_overwrite_original.setEnabled(False)
            self.option_overwrite_original.setToolTip("没有原始文件路径，无法使用此选项")
        file_layout.addWidget(self.option_overwrite_original)

        # 选项4：保存删除的链接到分类文件
        self.option_save_deleted = QCheckBox("保存删除的链接到分类文件")
        self.option_save_deleted.setChecked(True)
        file_layout.addWidget(self.option_save_deleted)

        layout.addWidget(file_group)

        # 按钮
        button_layout = QHBoxLayout()

        confirm_btn = QPushButton("✅ 确认删除")
        confirm_btn.clicked.connect(lambda: self.execute_delete_with_options(
            dialog, valid_links, expired_links, claimed_links, api_exception_links, error_links, valid_results
        ))

        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.exec()

    def execute_delete_with_options(self, dialog, valid_links, expired_links, claimed_links, api_exception_links, error_links, valid_results):
        """根据用户选择的选项执行删除操作"""
        dialog.accept()

        # 获取用户选择的选项
        save_cleaned = self.option_save_cleaned.isChecked()
        overwrite_original = self.option_overwrite_original.isChecked()
        save_deleted = self.option_save_deleted.isChecked()

        total_invalid = len(expired_links) + len(claimed_links) + len(api_exception_links) + len(error_links)

        # 1. 更新UI界面（始终执行）
        self.links_text.setPlainText('\n'.join(valid_links))
        self.current_results = valid_results.copy()
        self.update_results_table()
        self.update_statistics()
        self.update_links_count()

        # 2. 根据选项执行文件操作
        file_operations = []

        if save_cleaned:
            file_operations.append(('save_cleaned', valid_links))

        if overwrite_original:
            file_operations.append(('overwrite_original', valid_links))

        if save_deleted:
            file_operations.append(('save_deleted', (expired_links, claimed_links, api_exception_links, error_links)))

        # 执行文件操作
        if file_operations:
            self.execute_file_operations(file_operations, total_invalid, len(valid_links))
        else:
            # 仅UI操作完成
            self.show_delete_completion_message(total_invalid, len(valid_links), ui_only=True)

    def execute_file_operations(self, file_operations, total_invalid, valid_count):
        """执行文件操作"""
        try:
            operations_completed = []

            for operation_type, data in file_operations:
                if operation_type == 'save_cleaned':
                    # 保存清理后的链接到新文件
                    file_path, _ = QFileDialog.getSaveFileName(
                        self, "保存清理后的链接", "清理后的链接.txt",
                        "文本文件 (*.txt);;所有文件 (*)"
                    )
                    if file_path:
                        self.save_links_to_file_threaded(file_path, data, "清理后的链接")
                        operations_completed.append(f"保存清理后的链接到: {file_path}")

                elif operation_type == 'overwrite_original':
                    # 覆盖原始文件
                    if self.original_file_path:
                        reply = QMessageBox.question(
                            self, "确认覆盖",
                            f"⚠️ 警告：此操作将覆盖原始文件，无法撤销！\n\n"
                            f"原始文件: {self.original_file_path}\n\n"
                            f"确定要继续吗？",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self.save_links_to_file_threaded(self.original_file_path, data, "原始文件（已清理）")
                            operations_completed.append(f"已覆盖原始文件: {self.original_file_path}")
                    else:
                        QMessageBox.warning(self, "警告", "没有记录原始文件路径，无法覆盖原始文件！\n请使用'保存清理后的链接到新文件'选项。")

                elif operation_type == 'save_deleted':
                    # 保存删除的链接到分类文件
                    expired_links, claimed_links, api_exception_links, error_links = data
                    self.save_deleted_links_to_files(expired_links, claimed_links, api_exception_links, error_links)
                    operations_completed.append("已保存删除的链接到分类文件")

            # 显示完成消息
            self.show_delete_completion_message(total_invalid, valid_count, operations=operations_completed)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"文件操作失败: {str(e)}")

    def save_links_to_file_threaded(self, file_path, links, description):
        """使用线程保存链接到文件"""
        if self.file_operation_thread and self.file_operation_thread.isRunning():
            QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
            return

        # 启动文件保存线程
        self.file_operation_thread = FileOperationThread('save', file_path, links)
        self.file_operation_thread.operation_completed.connect(
            lambda success, message: self.on_links_file_save_completed(success, message, description)
        )
        self.file_operation_thread.progress_updated.connect(self.on_file_progress_updated)
        self.file_operation_thread.start()

        self.status_bar.showMessage(f"正在保存{description}...")

    def on_links_file_save_completed(self, success, message, description):
        """链接文件保存完成回调"""
        if success:
            print(f"✅ {description}保存成功: {message}")
        else:
            print(f"❌ {description}保存失败: {message}")
            QMessageBox.critical(self, "错误", f"{description}保存失败: {message}")

    def show_delete_completion_message(self, total_invalid, valid_count, ui_only=False, operations=None):
        """显示删除完成消息"""
        success_msg = f"✅ 删除完成！\n\n"
        success_msg += f"保留有效链接: {valid_count} 个\n"
        success_msg += f"删除失效链接: {total_invalid} 个\n\n"

        if ui_only:
            success_msg += "仅更新了界面，未修改文件。"
        elif operations:
            success_msg += "已完成的文件操作：\n"
            for op in operations:
                success_msg += f"• {op}\n"

        QMessageBox.information(self, "删除完成", success_msg)
        self.status_bar.showMessage(f"已删除 {total_invalid} 个失效链接，保留 {valid_count} 个有效链接")

        # 询问是否重新分析保留的链接
        if valid_count > 0:
            self.ask_reanalyze_remaining_links(valid_count)

    def ask_reanalyze_remaining_links(self, valid_count):
        """询问是否重新分析保留的链接"""
        reanalyze_reply = QMessageBox.question(
            self, "重新分析确认",
            f"删除完成！保留了 {valid_count} 个有效链接。\n\n"
            f"是否要重新分析这些保留的链接以确保数据最新？\n"
            f"（推荐：可以检测状态变化）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reanalyze_reply == QMessageBox.StandardButton.Yes:
            # 重新分析保留的链接
            self.reanalyze_remaining_links()

    def reanalyze_remaining_links(self):
        """重新分析保留的链接"""
        text = self.links_text.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "信息", "没有链接需要重新分析。")
            return

        links = [line.strip() for line in text.split('\n') if line.strip()]
        if not links:
            QMessageBox.information(self, "信息", "没有有效的链接需要重新分析。")
            return

        # 显示重新分析确认
        reply = QMessageBox.question(
            self, "确认重新分析",
            f"将重新分析 {len(links)} 个保留的链接。\n\n"
            f"这将覆盖当前的分析结果，确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 清空当前结果
            self.current_results = []
            self.gift_results_table.setRowCount(0)
            self.vip_results_table.setRowCount(0)
            self.stats_text.clear()

            # 启动重新分析
            self.status_bar.showMessage("正在重新分析保留的链接...")
            self.start_analysis()  # 复用现有的分析功能

    def save_deleted_links_to_files(self, expired_links, claimed_links, api_exception_links, error_links):
        """保存删除的链接到文件"""
        # 准备要保存的文件数据
        files_data = {}

        if expired_links:
            files_data['删除的已过期链接.txt'] = expired_links
        if claimed_links:
            files_data['删除的已领取链接.txt'] = claimed_links
        if api_exception_links:
            files_data['删除的API异常链接.txt'] = api_exception_links
        if error_links:
            files_data['删除的错误链接.txt'] = error_links

        if not files_data:
            return

        # 检查是否有文件操作线程正在运行
        if self.file_operation_thread and self.file_operation_thread.isRunning():
            print("文件操作正在进行中，跳过保存删除的链接...")
            return

        # 启动多文件保存线程
        self.file_operation_thread = FileOperationThread('save_multiple', files_data=files_data)
        self.file_operation_thread.operation_completed.connect(self.on_deleted_files_save_completed)
        self.file_operation_thread.progress_updated.connect(self.on_file_progress_updated)
        self.file_operation_thread.start()

        self.status_bar.showMessage("正在保存删除的链接文件...")

    def on_deleted_files_save_completed(self, success, message):
        """删除文件保存完成回调"""
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")

    def sync_results_with_input(self):
        """同步分析结果与输入链接"""
        text = self.links_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "输入区域没有链接！")
            return

        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有分析结果可以同步！")
            return

        # 获取当前输入的链接
        input_links = set(line.strip() for line in text.split('\n') if line.strip())

        # 获取分析结果中的链接
        result_links = set(result.get('short_url', '') for result in self.current_results)

        # 计算差异
        only_in_input = input_links - result_links
        only_in_results = result_links - input_links
        common_links = input_links & result_links

        # 显示同步信息
        sync_msg = f"📊 同步分析：\n\n"
        sync_msg += f"输入区域链接数: {len(input_links)}\n"
        sync_msg += f"分析结果链接数: {len(result_links)}\n"
        sync_msg += f"共同链接数: {len(common_links)}\n\n"

        if only_in_input:
            sync_msg += f"⚠️ 仅在输入中的链接: {len(only_in_input)} 个\n"
        if only_in_results:
            sync_msg += f"⚠️ 仅在结果中的链接: {len(only_in_results)} 个\n"

        sync_msg += f"\n选择同步方式："

        # 创建自定义对话框
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("同步选择")
        dialog.setModal(True)
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # 信息标签
        info_label = QLabel(sync_msg)
        layout.addWidget(info_label)

        # 按钮布局
        button_layout = QVBoxLayout()

        # 选项1：保持分析结果，更新输入
        btn1 = QPushButton("📋 用分析结果更新输入区域")
        btn1.clicked.connect(lambda: self.sync_option_1(dialog))
        button_layout.addWidget(btn1)

        # 选项2：保持输入，过滤分析结果
        btn2 = QPushButton("🔍 用输入区域过滤分析结果")
        btn2.clicked.connect(lambda: self.sync_option_2(dialog, input_links))
        button_layout.addWidget(btn2)

        # 选项3：重新分析输入的链接
        btn3 = QPushButton("🚀 重新分析输入区域的链接")
        btn3.clicked.connect(lambda: self.sync_option_3(dialog))
        button_layout.addWidget(btn3)

        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def sync_option_1(self, dialog):
        """选项1：用分析结果更新输入区域"""
        dialog.accept()

        result_links = [result.get('short_url', '') for result in self.current_results if result.get('short_url')]
        self.links_text.setPlainText('\n'.join(result_links))
        self.update_links_count()

        QMessageBox.information(self, "同步完成", f"已用分析结果更新输入区域\n更新了 {len(result_links)} 个链接")
        self.status_bar.showMessage("已用分析结果同步输入区域")

    def sync_option_2(self, dialog, input_links):
        """选项2：用输入区域过滤分析结果"""
        dialog.accept()

        # 过滤分析结果，只保留输入区域中的链接
        filtered_results = [result for result in self.current_results
                          if result.get('short_url', '') in input_links]

        self.current_results = filtered_results
        self.update_results_table()
        self.update_statistics()

        QMessageBox.information(self, "同步完成", f"已用输入区域过滤分析结果\n保留了 {len(filtered_results)} 个结果")
        self.status_bar.showMessage("已用输入区域过滤分析结果")

    def sync_option_3(self, dialog):
        """选项3：重新分析输入区域的链接"""
        dialog.accept()
        self.reanalyze_remaining_links()

    def save_results(self):
        """保存结果"""
        if not self.current_results:
            QMessageBox.warning(self, "警告", "没有结果可以保存！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析结果", "gift_analysis_results.json",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            # 检查是否有文件操作线程正在运行
            if self.file_operation_thread and self.file_operation_thread.isRunning():
                QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
                return

            # 启动文件保存线程
            self.file_operation_thread = FileOperationThread('save', file_path, self.current_results, format='json')
            self.file_operation_thread.operation_completed.connect(self.on_file_save_completed)
            self.file_operation_thread.progress_updated.connect(self.on_file_progress_updated)
            self.file_operation_thread.start()

            self.status_bar.showMessage("正在保存分析结果...")

    def export_available_links(self):
        """导出可领取链接"""
        if not self.current_results:
            QMessageBox.information(self, "信息", "没有分析结果可以导出！")
            return

        # 预先检查是否有可领取的链接
        available_count = len([r for r in self.current_results
                              if r['status'] == 'success' and r.get('gift_status') == 'available'])

        if available_count == 0:
            QMessageBox.information(self, "信息", "没有可领取的链接！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出可领取链接", "可领取礼品卡.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            # 检查是否有文件操作线程正在运行
            if self.file_operation_thread and self.file_operation_thread.isRunning():
                QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
                return

            # 启动文件导出线程
            self.file_operation_thread = FileOperationThread('export', file_path, self.current_results, export_type='available_links')
            self.file_operation_thread.operation_completed.connect(self.on_file_save_completed)
            self.file_operation_thread.progress_updated.connect(self.on_file_progress_updated)
            self.file_operation_thread.start()

            self.status_bar.showMessage("正在导出可领取链接...")

    def export_invalid_links(self):
        """导出失效链接"""
        if not self.current_results:
            QMessageBox.information(self, "信息", "没有分析结果可以导出！")
            return

        # 预先检查是否有失效的链接
        invalid_count = len([r for r in self.current_results
                            if r['status'] != 'success' or r.get('gift_status') != 'available'])

        if invalid_count == 0:
            QMessageBox.information(self, "信息", "没有失效的链接！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出失效链接", "失效礼品卡.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            # 检查是否有文件操作线程正在运行
            if self.file_operation_thread and self.file_operation_thread.isRunning():
                QMessageBox.warning(self, "警告", "文件操作正在进行中，请稍候...")
                return

            # 启动文件导出线程
            self.file_operation_thread = FileOperationThread('export', file_path, self.current_results, export_type='invalid_links')
            self.file_operation_thread.operation_completed.connect(self.on_file_save_completed)
            self.file_operation_thread.progress_updated.connect(self.on_file_progress_updated)
            self.file_operation_thread.start()

            self.status_bar.showMessage("正在导出失效链接...")

    def clear_data(self):
        """清空数据"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.links_text.clear()
            self.current_results = []
            self.gift_results_table.setRowCount(0)
            self.vip_results_table.setRowCount(0)
            self.stats_text.clear()
            self.progress_bar.setValue(0)
            self.progress_label.setText("就绪")
            self.status_bar.showMessage("数据已清空")

    def show_about(self):
        """显示关于信息"""
        about_text = """
        <h3>网易云音乐礼品卡分析器</h3>
        <p><b>版本:</b> 2.0</p>
        <p><b>作者:</b> suimi</p>
        <p><b>功能:</b></p>
        <ul>
        <li><b>礼品卡分析器:</b></li>
        <ul>
        <li>批量分析礼品卡状态</li>
        <li>智能识别可领取、已过期、已领取状态</li>
        <li>支持失效链接删除</li>
        <li>多线程高效处理</li>
        <li>详细统计信息</li>
        <li>VIP链接有效期检查</li>
        </ul>
        </ul>
        <p><b>技术:</b> PyQt6 + 网易云音乐API + 多线程并发</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        """关闭事件"""
        # 检查是否有线程在运行
        analyzer_running = self.analyzer_thread and self.analyzer_thread.isRunning()
        file_operation_running = self.file_operation_thread and self.file_operation_thread.isRunning()

        if analyzer_running or file_operation_running:
            running_tasks = []
            if analyzer_running:
                running_tasks.append("礼品卡分析")
            if file_operation_running:
                running_tasks.append("文件操作")

            task_text = "、".join(running_tasks)
            reply = QMessageBox.question(
                self, "确认退出", f"{task_text}正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if analyzer_running:
                    self.analyzer_thread.stop()
                    self.analyzer_thread.wait()
                if file_operation_running:
                    self.file_operation_thread.wait()  # 文件操作线程没有stop方法，直接等待完成
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("网易云音乐礼品卡分析器")
    app.setApplicationVersion("2.0")

    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon('icon.png'))

    window = GiftAnalyzerUI()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()