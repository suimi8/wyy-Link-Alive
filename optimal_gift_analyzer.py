"""
网易云音乐礼品卡最优分析器
直接调用API接口，实现高效的礼品卡状态判断
作者: Claude 4.0 sonnet
"""

import requests
import json
import random
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from urllib.parse import urlparse, parse_qs
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import (
    RequestException, ConnectionError, Timeout,
    HTTPError, TooManyRedirects, SSLError
)

class NetEaseEncryption:
    """网易云音乐加密工具类"""
    
    def __init__(self):
        self.character = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        self.iv = '0102030405060708'
        self.public_key = '010001'
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b' \
                       '5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417' \
                       '629ec4ee341f56135fccf695280104e0312ecbda92557c93' \
                       '870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b' \
                       '424d813cfe4875d3e82047b97ddef52741d546b8e289dc69' \
                       '35b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'
    
    def create_random_string(self, length=16):
        """生成随机字符串"""
        return ''.join(random.sample(self.character, length))
    
    def aes_encrypt(self, text, key):
        """AES加密"""
        text = pad(text.encode(), AES.block_size)
        key = key.encode()
        iv = self.iv.encode()
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(text)
        return base64.b64encode(encrypted).decode()
    
    def rsa_encrypt(self, text, e, n):
        """RSA加密"""
        # 字符串反转后转十六进制
        text_hex = text[::-1].encode().hex()
        # RSA加密: C = M^e mod n
        encrypted = pow(int(text_hex, 16), int(e, 16), int(n, 16))
        return format(encrypted, 'x')
    
    def encrypt_params(self, data):
        """加密参数"""
        # 生成16位随机字符串
        random_str = self.create_random_string(16)
        
        # 第一次AES加密
        first_encrypt = self.aes_encrypt(data, self.nonce)
        
        # 第二次AES加密
        second_encrypt = self.aes_encrypt(first_encrypt, random_str)
        
        # RSA加密随机字符串
        rsa_encrypted = self.rsa_encrypt(random_str, self.public_key, self.modulus)
        
        return {
            'params': second_encrypt,
            'encSecKey': rsa_encrypted
        }

class OptimalGiftAnalyzer:
    """最优礼品卡分析器 - 直接调用API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        self.encryption = NetEaseEncryption()
        self.api_url = 'https://music.163.com/weapi/vipgift/app/gift/index'

        # 线程锁
        self.lock = threading.Lock()
        self.results = []

    def classify_exception(self, exception):
        """分类异常类型，返回详细的异常信息"""
        if isinstance(exception, ConnectionError):
            return {
                'error_type': 'api_exception',
                'error_category': 'connection_error',
                'error_message': '网络连接失败',
                'technical_details': str(exception)
            }
        elif isinstance(exception, Timeout):
            return {
                'error_type': 'api_exception',
                'error_category': 'timeout',
                'error_message': '请求超时',
                'technical_details': str(exception)
            }
        elif isinstance(exception, HTTPError):
            return {
                'error_type': 'api_exception',
                'error_category': 'http_error',
                'error_message': 'HTTP请求错误',
                'technical_details': str(exception)
            }
        elif isinstance(exception, TooManyRedirects):
            return {
                'error_type': 'api_exception',
                'error_category': 'redirect_error',
                'error_message': '重定向次数过多',
                'technical_details': str(exception)
            }
        elif isinstance(exception, SSLError):
            return {
                'error_type': 'api_exception',
                'error_category': 'ssl_error',
                'error_message': 'SSL证书错误',
                'technical_details': str(exception)
            }
        elif isinstance(exception, RequestException):
            return {
                'error_type': 'api_exception',
                'error_category': 'request_error',
                'error_message': '请求异常',
                'technical_details': str(exception)
            }
        else:
            return {
                'error_type': 'system_exception',
                'error_category': 'unknown_error',
                'error_message': '未知系统异常',
                'technical_details': str(exception)
            }
    
    def extract_gift_params(self, redirect_url):
        """从重定向URL中提取礼品卡参数"""
        try:
            parsed_url = urlparse(redirect_url)
            params = parse_qs(parsed_url.query)
            
            return {
                'd': params.get('d', [''])[0],
                'p': params.get('p', [''])[0],
                'userid': params.get('userid', [''])[0],
                'app_version': params.get('app_version', ['9.1.80'])[0],
                'dlt': params.get('dlt', ['0846'])[0]
            }
        except Exception as e:
            print(f"参数提取失败: {e}")
            return None
    
    def call_gift_api(self, gift_params):
        """直接调用礼品卡API"""
        try:
            # 构造API请求数据
            api_data = {
                'd': gift_params['d'],
                'p': gift_params['p'],
                'userid': gift_params['userid'],
                'app_version': gift_params['app_version'],
                'dlt': gift_params['dlt'],
                'csrf_token': ''
            }

            # 加密参数
            encrypted_data = self.encryption.encrypt_params(json.dumps(api_data))

            # 发送API请求
            response = self.session.post(
                self.api_url,
                data=encrypted_data,
                timeout=10
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    return self.parse_api_response(result, gift_params)
                except json.JSONDecodeError as e:
                    return {
                        'status': 'api_exception',
                        'error_type': 'api_exception',
                        'error_category': 'json_decode_error',
                        'error_message': 'API响应格式错误',
                        'message': 'API响应格式错误',
                        'technical_details': str(e)
                    }
            elif response.status_code == 403:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'forbidden',
                    'error_message': 'API访问被拒绝(403)',
                    'message': 'API访问被拒绝',
                    'technical_details': f'HTTP {response.status_code}'
                }
            elif response.status_code == 429:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'rate_limit',
                    'error_message': '请求频率过高(429)',
                    'message': '请求频率过高',
                    'technical_details': f'HTTP {response.status_code}'
                }
            elif response.status_code >= 500:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'server_error',
                    'error_message': f'服务器错误({response.status_code})',
                    'message': f'服务器错误({response.status_code})',
                    'technical_details': f'HTTP {response.status_code}'
                }
            else:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'http_error',
                    'error_message': f'HTTP错误({response.status_code})',
                    'message': f'HTTP错误({response.status_code})',
                    'technical_details': f'HTTP {response.status_code}'
                }

        except (ConnectionError, Timeout, HTTPError, TooManyRedirects, SSLError, RequestException) as e:
            error_info = self.classify_exception(e)
            return {
                'status': 'api_exception',
                'message': error_info['error_message'],
                **error_info
            }
        except Exception as e:
            error_info = self.classify_exception(e)
            return {
                'status': 'system_exception',
                'message': f'系统异常: {str(e)}',
                **error_info
            }
    
    def parse_api_response(self, api_result, gift_params):
        """解析API响应"""
        try:
            # 检查API响应的基本结构
            if not api_result:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'empty_response',
                    'error_message': 'API返回空响应',
                    'message': 'API返回空响应'
                }

            # 检查API错误码
            if 'code' in api_result and api_result['code'] != 200:
                error_code = api_result['code']
                error_msg = api_result.get('message', '未知API错误')
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'api_business_error',
                    'error_message': f'API业务错误({error_code}): {error_msg}',
                    'message': f'API业务错误: {error_msg}',
                    'api_code': error_code,
                    'technical_details': f'API Code: {error_code}, Message: {error_msg}'
                }

            # 检查是否有数据返回
            if 'data' not in api_result:
                return {
                    'status': 'api_exception',
                    'error_type': 'api_exception',
                    'error_category': 'missing_data',
                    'error_message': 'API响应缺少数据字段',
                    'message': 'API响应格式错误'
                }

            data = api_result['data']
            current_time = int(time.time() * 1000)  # 当前时间戳(毫秒)

            # 提取关键信息
            record = data.get('record', {})
            sku = data.get('sku', {})
            sender = data.get('sender', {})

            # 判断礼品卡状态
            expire_time = record.get('expireTime', 0)
            total_count = record.get('totalCount', 0)
            used_count = record.get('usedCount', 0)

            # 状态判断逻辑
            if expire_time > 0 and current_time > expire_time:
                gift_status = 'expired'
                status_text = '已过期'
            elif used_count >= total_count:
                gift_status = 'claimed'
                status_text = '已领取完'
            elif total_count > used_count:
                gift_status = 'available'
                status_text = f'可领取 ({total_count - used_count}/{total_count})'
            else:
                gift_status = 'unknown'
                status_text = '状态未知'

            # 计算过期时间
            expire_date = ''
            if expire_time > 0:
                expire_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire_time / 1000))

            return {
                'status': 'success',
                'gift_status': gift_status,
                'status_text': status_text,
                'sender_id': gift_params.get('userid', ''),
                'sender_name': sender.get('nickName', ''),
                'gift_data': gift_params.get('d', ''),
                'gift_type': sku.get('goods', ''),
                'gift_price': sku.get('price', 0),
                'total_count': total_count,
                'used_count': used_count,
                'available_count': max(0, total_count - used_count),
                'expire_time': expire_time,
                'expire_date': expire_date,
                'is_expired': current_time > expire_time if expire_time > 0 else False,
                'api_response': data
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'响应解析失败: {str(e)}'
            }
    
    def analyze_gift_link(self, short_url):
        """分析单个礼品链接"""
        try:
            # 第一步：获取重定向链接
            resp = self.session.head(short_url, allow_redirects=False, timeout=10)

            if resp.status_code not in [301, 302]:
                if resp.status_code == 404:
                    return {
                        "status": "invalid",
                        "message": "链接不存在(404)",
                        "error_category": "not_found"
                    }
                elif resp.status_code >= 500:
                    return {
                        "status": "api_exception",
                        "error_type": "api_exception",
                        "error_category": "server_error",
                        "error_message": f"短链接服务器错误({resp.status_code})",
                        "message": f"短链接服务器错误({resp.status_code})"
                    }
                else:
                    return {
                        "status": "invalid",
                        "message": f"无效的短链接(HTTP {resp.status_code})"
                    }

            if 'Location' not in resp.headers:
                return {
                    "status": "invalid",
                    "message": "短链接缺少重定向信息"
                }

            redirect_url = resp.headers['Location']

            if 'gift-receive' not in redirect_url:
                return {
                    "status": "invalid",
                    "message": "不是礼品卡链接"
                }

            # 第二步：提取礼品卡参数
            gift_params = self.extract_gift_params(redirect_url)
            if not gift_params:
                return {
                    "status": "error",
                    "message": "参数提取失败"
                }

            # 第三步：调用API获取状态
            api_result = self.call_gift_api(gift_params)

            # 添加原始信息
            api_result['short_url'] = short_url
            api_result['redirect_url'] = redirect_url

            return api_result

        except (ConnectionError, Timeout, HTTPError, TooManyRedirects, SSLError, RequestException) as e:
            error_info = self.classify_exception(e)
            return {
                "status": "api_exception",
                "short_url": short_url,
                "message": error_info['error_message'],
                **error_info
            }
        except Exception as e:
            error_info = self.classify_exception(e)
            return {
                "status": "system_exception",
                "short_url": short_url,
                "message": f"系统异常: {str(e)}",
                **error_info
            }
    
    def batch_analyze(self, short_urls, max_workers=10):
        """批量分析礼品链接"""
        print(f"[🚀 开始分析] 共 {len(short_urls)} 个链接，使用 {max_workers} 个线程")
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.analyze_gift_link, url): url 
                for url in short_urls
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # 显示进度
                    if result['status'] == 'success':
                        status_text = result.get('status_text', 'Unknown')
                        gift_type = result.get('gift_type', '')
                        sender_name = result.get('sender_name', '')
                        print(f"[✅ {completed}/{len(short_urls)}] {url} → {status_text} | {gift_type} | {sender_name}")
                    else:
                        print(f"[❌ {completed}/{len(short_urls)}] {url} → {result.get('message', 'Error')}")
                    
                except Exception as e:
                    print(f"[⚠️ {completed}/{len(short_urls)}] {url} → 处理异常: {e}")
                    results.append({
                        'status': 'error',
                        'short_url': url,
                        'message': str(e)
                    })
                    completed += 1
        
        return results
    
    def save_results(self, results, filename='gift_analysis_results.json'):
        """保存分析结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[💾 保存完成] 结果已保存到 {filename}")
    
    def print_statistics(self, results):
        """打印统计信息"""
        total = len(results)
        success_count = len([r for r in results if r['status'] == 'success'])

        if success_count > 0:
            status_count = {}
            gift_types = {}
            total_value = 0
            available_value = 0

            for result in results:
                if result['status'] == 'success':
                    status = result.get('gift_status', 'unknown')
                    status_count[status] = status_count.get(status, 0) + 1

                    # 统计礼品类型
                    gift_type = result.get('gift_type', 'Unknown')
                    gift_types[gift_type] = gift_types.get(gift_type, 0) + 1

                    # 统计价值
                    price = result.get('gift_price', 0)
                    total_value += price
                    if status == 'available':
                        available_value += price

            print(f"\n[📊 统计结果]")
            print(f"总链接数: {total}")
            print(f"成功分析: {success_count}")
            print(f"失败数量: {total - success_count}")

            print(f"\n[🎁 礼品卡状态分布]")
            for status, count in status_count.items():
                percentage = (count / success_count) * 100
                print(f"{status}: {count} ({percentage:.1f}%)")

            print(f"\n[🎯 礼品类型分布]")
            for gift_type, count in gift_types.items():
                percentage = (count / success_count) * 100
                print(f"{gift_type}: {count} ({percentage:.1f}%)")

            print(f"\n[💰 价值统计]")
            print(f"总价值: ¥{total_value:.1f}")
            print(f"可领取价值: ¥{available_value:.1f}")
            print(f"可领取率: {(available_value/total_value*100):.1f}%" if total_value > 0 else "可领取率: 0%")

    def filter_and_save(self, results, save_available=True, save_expired=True, save_claimed=True):
        """过滤并保存不同状态的礼品卡"""
        available_links = []
        expired_links = []
        claimed_links = []

        for result in results:
            if result['status'] == 'success':
                status = result.get('gift_status', 'unknown')
                short_url = result.get('short_url', '')

                if status == 'available':
                    available_links.append(short_url)
                elif status == 'expired':
                    expired_links.append(short_url)
                elif status == 'claimed':
                    claimed_links.append(short_url)

        # 保存可领取的链接
        if save_available and available_links:
            with open('可领取礼品卡.txt', 'w', encoding='utf-8') as f:
                for link in available_links:
                    f.write(link + '\n')
            print(f"[💾 已保存] {len(available_links)} 个可领取链接到 '可领取礼品卡.txt'")

        # 保存已过期的链接
        if save_expired and expired_links:
            with open('已过期礼品卡.txt', 'w', encoding='utf-8') as f:
                for link in expired_links:
                    f.write(link + '\n')
            print(f"[💾 已保存] {len(expired_links)} 个已过期链接到 '已过期礼品卡.txt'")

        # 保存已领取的链接
        if save_claimed and claimed_links:
            with open('已领取礼品卡.txt', 'w', encoding='utf-8') as f:
                for link in claimed_links:
                    f.write(link + '\n')
            print(f"[💾 已保存] {len(claimed_links)} 个已领取链接到 '已领取礼品卡.txt'")

        return {
            'available': len(available_links),
            'expired': len(expired_links),
            'claimed': len(claimed_links)
        }

# 使用示例
if __name__ == "__main__":
    analyzer = OptimalGiftAnalyzer()
    
    # 测试单个链接
    test_url = "http://163cn.tv/GBm6AHn"
    print("=== 单链接测试 ===")
    result = analyzer.analyze_gift_link(test_url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 批量测试
    try:
        with open('gift_links.txt', 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
        
        print(f"\n=== 批量分析 ===")
        # 只测试前10个链接
        test_links = links[:10]
        batch_results = analyzer.batch_analyze(test_links, max_workers=5)
        
        # 保存结果
        analyzer.save_results(batch_results)
        
        # 打印统计
        analyzer.print_statistics(batch_results)

        # 过滤并保存不同状态的链接
        filter_stats = analyzer.filter_and_save(batch_results)
        print(f"\n[📁 文件保存统计]")
        print(f"可领取: {filter_stats['available']} 个")
        print(f"已过期: {filter_stats['expired']} 个")
        print(f"已领取: {filter_stats['claimed']} 个")

    except FileNotFoundError:
        print("未找到 gift_links.txt 文件")
    except Exception as e:
        print(f"批量分析失败: {e}")
