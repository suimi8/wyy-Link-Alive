// 主应用状态管理
function appState() {
    return {
        // 页面状态
        activePage: 'dashboard',
        mobileMenuOpen: false,
        
        // 分析状态
        isAnalyzing: false,
        isPaused: false,
        progress: {
            current: 0,
            total: 0,
            percentage: 0
        },
        
        // 数据状态
        links: [],
        results: [],
        statistics: {
            total: 0,
            available: 0,
            expired: 0,
            claimed: 0,
            invalid: 0,
            vipLinks: 0
        },
        
        // 设置
        settings: {
            maxWorkers: 10,
            timeout: 15,
            autoSave: true,
            showNotifications: true
        },
        
        // 初始化
        init() {
            this.loadSettings();
            this.loadData();
            this.setActivePage('dashboard');
        },
        
        // 页面导航
        setActivePage(page) {
            this.activePage = page;
            this.mobileMenuOpen = false;
            this.loadPageContent(page);
        },
        
        // 加载页面内容
        loadPageContent(page) {
            switch(page) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'analyzer':
                    loadAnalyzer();
                    break;
                case 'results':
                    loadResults();
                    break;
                case 'settings':
                    loadSettings();
                    break;
            }
        },
        
        // 保存设置
        saveSettings() {
            localStorage.setItem('giftAnalyzer_settings', JSON.stringify(this.settings));
        },
        
        // 加载设置
        loadSettings() {
            const saved = localStorage.getItem('giftAnalyzer_settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
        },
        
        // 保存数据
        saveData() {
            localStorage.setItem('giftAnalyzer_data', JSON.stringify({
                links: this.links,
                results: this.results,
                statistics: this.statistics
            }));
        },
        
        // 加载数据
        loadData() {
            const saved = localStorage.getItem('giftAnalyzer_data');
            if (saved) {
                const data = JSON.parse(saved);
                this.links = data.links || [];
                this.results = data.results || [];
                this.statistics = data.statistics || this.statistics;
            }
        },
        
        // 清除所有数据
        clearAllData() {
            this.links = [];
            this.results = [];
            this.statistics = {
                total: 0,
                available: 0,
                expired: 0,
                claimed: 0,
                invalid: 0,
                vipLinks: 0
            };
            this.saveData();
        }
    }
}

// 工具函数
const Utils = {
    // 显示Toast通知
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const typeClasses = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'warning': 'bg-yellow-500 text-black',
            'info': 'bg-blue-500 text-white'
        };
        
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        toast.className = `flex items-center p-4 rounded-lg shadow-lg ${typeClasses[type]} transform transition-all duration-300 translate-x-full`;
        toast.innerHTML = `
            <i class="${icons[type]} mr-3"></i>
            <span class="flex-1">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-3 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // 动画显示
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // 自动隐藏
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, duration);
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 格式化时间
    formatTime(date) {
        return new Intl.DateTimeFormat('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        }).format(date);
    },
    
    // 下载文件
    downloadFile(content, filename, type = 'text/plain') {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('已复制到剪贴板', 'success');
        } catch (err) {
            this.showToast('复制失败', 'error');
        }
    },
    
    // 获取随机Unsplash图片
    getUnsplashImage(width = 800, height = 600, keyword = 'music') {
        return `https://source.unsplash.com/${width}x${height}/?${keyword}`;
    },
    
    // 验证链接格式
    validateLink(link) {
        const patterns = [
            /^https?:\/\/163cn\.tv\/\w+$/,  // 礼品卡链接
            /vip-invite-cashier/  // VIP链接
        ];
        return patterns.some(pattern => pattern.test(link));
    },
    
    // 解析链接列表
    parseLinks(text) {
        return text
            .split('\n')
            .map(line => line.trim())
            .filter(line => line && this.validateLink(line));
    }
};

// 分析器API
const AnalyzerAPI = {
    // 模拟分析单个链接
    async analyzeSingleLink(link) {
        return new Promise((resolve) => {
            setTimeout(() => {
                const random = Math.random();
                const isVipLink = link.includes('vip-invite-cashier');
                
                let result = {
                    short_url: link,
                    status: 'success',
                    is_vip_link: isVipLink,
                    timestamp: Date.now()
                };
                
                if (isVipLink) {
                    result.gift_type = 'VIP邀请';
                    result.vip_status = random > 0.3 ? 'valid' : 'expired';
                    result.expire_date = new Date(Date.now() + Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleString('zh-CN');
                    result.remaining_days = random > 0.3 ? Math.floor(Math.random() * 30) : 0;
                    result.gift_status = result.vip_status === 'valid' ? 'available' : 'expired';
                } else {
                    if (random > 0.7) {
                        result.gift_status = 'available';
                        result.status_text = `可领取 (${Math.floor(Math.random() * 5) + 1}/${Math.floor(Math.random() * 5) + 5})`;
                        result.available_count = Math.floor(Math.random() * 5) + 1;
                        result.total_count = result.available_count + Math.floor(Math.random() * 3);
                    } else if (random > 0.4) {
                        result.gift_status = 'expired';
                        result.status_text = '已过期';
                        result.expire_date = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleString('zh-CN');
                    } else if (random > 0.2) {
                        result.gift_status = 'claimed';
                        result.status_text = '已领取完';
                        result.total_count = Math.floor(Math.random() * 10) + 1;
                        result.used_count = result.total_count;
                    } else {
                        result.status = 'error';
                        result.gift_status = 'invalid';
                        result.status_text = '链接无效';
                    }
                    
                    result.gift_type = ['黑胶VIP月卡', '黑胶VIP年卡', '音乐包月卡'][Math.floor(Math.random() * 3)];
                    result.gift_price = [15, 98, 12][Math.floor(Math.random() * 3)];
                    result.sender_name = '用户' + Math.floor(Math.random() * 1000);
                }
                
                resolve(result);
            }, Math.random() * 2000 + 500); // 0.5-2.5秒随机延迟
        });
    },
    
    // 批量分析链接
    async batchAnalyze(links, maxWorkers = 10, onProgress = null, onSingleResult = null) {
        const results = [];
        const workers = Math.min(maxWorkers, links.length);
        const chunks = this.chunkArray(links, Math.ceil(links.length / workers));
        
        let completed = 0;
        const total = links.length;
        
        const analyzeChunk = async (chunk) => {
            for (const link of chunk) {
                try {
                    const result = await this.analyzeSingleLink(link);
                    results.push(result);
                    completed++;
                    
                    if (onProgress) {
                        onProgress(completed, total);
                    }
                    
                    if (onSingleResult) {
                        onSingleResult(result);
                    }
                } catch (error) {
                    console.error('分析失败:', error);
                    completed++;
                    if (onProgress) {
                        onProgress(completed, total);
                    }
                }
            }
        };
        
        await Promise.all(chunks.map(analyzeChunk));
        return results;
    },
    
    // 将数组分块
    chunkArray(array, chunkSize) {
        const chunks = [];
        for (let i = 0; i < array.length; i += chunkSize) {
            chunks.push(array.slice(i, i + chunkSize));
        }
        return chunks;
    }
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    // Alpine.js会自动初始化，我们只需要确保组件加载
    console.log('网易云音乐礼品卡分析器已启动');
});