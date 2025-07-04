#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API诊断测试脚本
用于检测分析器API是否正常工作
"""

import requests
import json
import sys

def test_api():
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 开始诊断API...")
    print("=" * 50)
    
    # 测试1: 健康检查
    print("1. 测试API健康状态...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("   ✅ 健康检查通过")
        else:
            print(f"   ❌ 健康检查失败: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 无法连接到API服务器: {e}")
        print("   💡 请确认服务器是否已启动: python3 server_simple.py")
        return False
    
    # 测试2: 分析接口测试
    print("\n2. 测试分析接口...")
    test_links = [
        "http://163cn.tv/test123",
        "https://163cn.tv/example"
    ]
    
    for link in test_links:
        print(f"   测试链接: {link}")
        try:
            response = requests.post(
                f"{base_url}/api/analyze",
                json={"link": link},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"     状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"     结果: {data.get('gift_status', 'unknown')} - {data.get('status_text', 'N/A')}")
                print("     ✅ 分析接口正常")
            else:
                print(f"     ❌ 分析失败: {response.text}")
        except Exception as e:
            print(f"     ❌ 请求异常: {e}")
    
    # 测试3: 批量分析测试
    print("\n3. 测试批量分析接口...")
    try:
        response = requests.post(
            f"{base_url}/api/batch_analyze",
            json={"links": test_links},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   处理数量: {data.get('total', 0)}")
            print("   ✅ 批量分析接口正常")
        else:
            print(f"   ❌ 批量分析失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 批量分析异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 诊断建议:")
    print("1. 如果健康检查失败，请确认服务器已启动")
    print("2. 如果分析失败，请检查网络连接")
    print("3. 查看服务器终端日志获取详细错误信息")
    print("4. 在浏览器F12控制台查看前端错误")
    print("\n✅ 如果所有测试通过，说明后端API正常工作")
    
    return True

if __name__ == "__main__":
    try:
        test_api()
    except KeyboardInterrupt:
        print("\n\n❌ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试脚本异常: {e}")
        sys.exit(1)