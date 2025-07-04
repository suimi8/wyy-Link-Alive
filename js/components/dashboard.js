// 仪表板页面组件
function loadDashboard() {
    const content = document.getElementById('dashboard-content');
    
    content.innerHTML = `
        <div class="space-y-8" x-data="dashboardData()">
            <!-- 欢迎头部 -->
            <div class="text-center text-white mb-8">
                <img src="${Utils.getUnsplashImage(1200, 400, 'music,neon')}" 
                     alt="Background" 
                     class="w-full h-64 object-cover rounded-2xl shadow-2xl opacity-20 absolute inset-0 -z-10">
                <div class="relative z-10 glass-effect rounded-2xl p-8">
                    <h1 class="text-4xl font-bold mb-4">
                        <i class="fas fa-music mr-3 text-yellow-400"></i>
                        网易云音乐礼品分析器
                    </h1>
                    <p class="text-xl text-gray-200 max-w-2xl mx-auto">
                        高效分析网易云音乐礼品卡状态，支持批量检测和VIP链接有效期查询
                    </p>
                </div>
            </div>

            <!-- 统计卡片 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <!-- 总链接数 -->
                <div class="glass-effect rounded-xl p-6 hover-lift">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-300 text-sm">总链接数</p>
                            <p class="text-3xl font-bold text-white" x-text="totalLinks"></p>
                        </div>
                        <div class="bg-blue-500 bg-opacity-20 p-3 rounded-full">
                            <i class="fas fa-link text-2xl text-blue-400"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <span class="text-green-400 text-sm">
                            <i class="fas fa-arrow-up mr-1"></i>
                            +<span x-text="recentAdded"></span> 最近添加
                        </span>
                    </div>
                </div>

                <!-- 可用礼品 -->
                <div class="glass-effect rounded-xl p-6 hover-lift">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-300 text-sm">可用礼品</p>
                            <p class="text-3xl font-bold text-white" x-text="availableGifts"></p>
                        </div>
                        <div class="bg-green-500 bg-opacity-20 p-3 rounded-full">
                            <i class="fas fa-gift text-2xl text-green-400"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <span class="text-green-400 text-sm" x-text="availablePercentage + '% 可用率'"></span>
                    </div>
                </div>

                <!-- VIP链接 -->
                <div class="glass-effect rounded-xl p-6 hover-lift">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-300 text-sm">VIP链接</p>
                            <p class="text-3xl font-bold text-white" x-text="vipLinks"></p>
                        </div>
                        <div class="bg-purple-500 bg-opacity-20 p-3 rounded-full">
                            <i class="fas fa-crown text-2xl text-purple-400"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <span class="text-purple-400 text-sm" x-text="validVipPercentage + '% 有效'"></span>
                    </div>
                </div>

                <!-- 分析成功率 -->
                <div class="glass-effect rounded-xl p-6 hover-lift">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-300 text-sm">成功率</p>
                            <p class="text-3xl font-bold text-white" x-text="successRate + '%'"></p>
                        </div>
                        <div class="bg-yellow-500 bg-opacity-20 p-3 rounded-full">
                            <i class="fas fa-chart-line text-2xl text-yellow-400"></i>
                        </div>
                    </div>
                    <div class="mt-4">
                        <span class="text-yellow-400 text-sm">分析效率</span>
                    </div>
                </div>
            </div>

            <!-- 快速操作 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- 快速分析 -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-xl font-semibold text-white mb-4">
                        <i class="fas fa-rocket mr-2 text-blue-400"></i>
                        快速分析
                    </h3>
                    <div class="space-y-4">
                        <textarea 
                            x-model="quickAnalyzeText"
                            placeholder="粘贴礼品卡链接，每行一个..."
                            class="w-full h-32 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white placeholder-gray-400 resize-none"
                        ></textarea>
                        <div class="flex space-x-3">
                            <button 
                                @click="startQuickAnalyze()"
                                :disabled="!quickAnalyzeText.trim() || isAnalyzing"
                                class="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-play mr-2"></i>
                                <span x-text="isAnalyzing ? '分析中...' : '开始分析'"></span>
                            </button>
                            <button 
                                @click="clearQuickAnalyze()"
                                class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-trash mr-2"></i>
                                清空
                            </button>
                        </div>
                        <div x-show="quickAnalyzeProgress.total > 0" class="space-y-2">
                            <div class="flex justify-between text-sm text-gray-300">
                                <span x-text="'进度: ' + quickAnalyzeProgress.current + '/' + quickAnalyzeProgress.total"></span>
                                <span x-text="Math.round(quickAnalyzeProgress.current / quickAnalyzeProgress.total * 100) + '%'"></span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-2">
                                <div class="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                                     :style="'width: ' + (quickAnalyzeProgress.current / quickAnalyzeProgress.total * 100) + '%'">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 最近结果 -->
                <div class="glass-effect rounded-xl p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-semibold text-white">
                            <i class="fas fa-clock mr-2 text-green-400"></i>
                            最近结果
                        </h3>
                        <button 
                            @click="$parent.setActivePage('results')"
                            class="text-green-400 hover:text-green-300 text-sm">
                            查看全部 <i class="fas fa-arrow-right ml-1"></i>
                        </button>
                    </div>
                    <div class="space-y-3">
                        <template x-for="result in recentResults" :key="result.short_url">
                            <div class="bg-white bg-opacity-5 rounded-lg p-3 flex items-center justify-between">
                                <div class="flex-1 min-w-0">
                                    <p class="text-white text-sm font-medium truncate" x-text="result.gift_type || 'Unknown'"></p>
                                    <p class="text-gray-400 text-xs truncate" x-text="result.short_url"></p>
                                </div>
                                <div class="ml-3">
                                    <span 
                                        class="px-2 py-1 text-xs rounded-full"
                                        :class="{
                                            'bg-green-500 bg-opacity-20 text-green-400': result.gift_status === 'available',
                                            'bg-red-500 bg-opacity-20 text-red-400': result.gift_status === 'expired',
                                            'bg-yellow-500 bg-opacity-20 text-yellow-400': result.gift_status === 'claimed',
                                            'bg-gray-500 bg-opacity-20 text-gray-400': result.gift_status === 'invalid'
                                        }"
                                        x-text="getStatusText(result.gift_status)"
                                    ></span>
                                </div>
                            </div>
                        </template>
                        <div x-show="recentResults.length === 0" class="text-center text-gray-400 py-8">
                            <i class="fas fa-inbox text-3xl mb-2"></i>
                            <p>暂无分析结果</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 图表统计 -->
            <div class="glass-effect rounded-xl p-6">
                <h3 class="text-xl font-semibold text-white mb-6">
                    <i class="fas fa-chart-pie mr-2 text-purple-400"></i>
                    分析统计
                </h3>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- 状态分布饼图 -->
                    <div class="text-center">
                        <h4 class="text-lg font-medium text-white mb-4">状态分布</h4>
                        <div class="relative inline-block">
                            <svg width="200" height="200" class="transform -rotate-90">
                                <circle cx="100" cy="100" r="80" fill="none" stroke="#374151" stroke-width="8"></circle>
                                <!-- 可用 -->
                                <circle cx="100" cy="100" r="80" fill="none" stroke="#10b981" stroke-width="8"
                                        :stroke-dasharray="availableArc + ' ' + (502 - availableArc)"
                                        stroke-dashoffset="0" class="transition-all duration-1000"></circle>
                                <!-- 过期 -->
                                <circle cx="100" cy="100" r="80" fill="none" stroke="#ef4444" stroke-width="8"
                                        :stroke-dasharray="expiredArc + ' ' + (502 - expiredArc)"
                                        :stroke-dashoffset="-availableArc" class="transition-all duration-1000"></circle>
                                <!-- 已领取 -->
                                <circle cx="100" cy="100" r="80" fill="none" stroke="#f59e0b" stroke-width="8"
                                        :stroke-dasharray="claimedArc + ' ' + (502 - claimedArc)"
                                        :stroke-dashoffset="-(availableArc + expiredArc)" class="transition-all duration-1000"></circle>
                            </svg>
                            <div class="absolute inset-0 flex items-center justify-center">
                                <div class="text-center">
                                    <p class="text-2xl font-bold text-white" x-text="totalLinks"></p>
                                    <p class="text-sm text-gray-300">总数</p>
                                </div>
                            </div>
                        </div>
                        <div class="mt-4 grid grid-cols-2 gap-2 text-sm">
                            <div class="flex items-center justify-center">
                                <div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                                <span class="text-gray-300">可用</span>
                            </div>
                            <div class="flex items-center justify-center">
                                <div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                                <span class="text-gray-300">过期</span>
                            </div>
                            <div class="flex items-center justify-center">
                                <div class="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                                <span class="text-gray-300">已领取</span>
                            </div>
                            <div class="flex items-center justify-center">
                                <div class="w-3 h-3 bg-gray-500 rounded-full mr-2"></div>
                                <span class="text-gray-300">无效</span>
                            </div>
                        </div>
                    </div>

                    <!-- 价值统计 -->
                    <div>
                        <h4 class="text-lg font-medium text-white mb-4">价值统计</h4>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">可用礼品总价值</span>
                                <span class="text-green-400 font-semibold" x-text="'¥' + availableValue"></span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">已过期价值</span>
                                <span class="text-red-400 font-semibold" x-text="'¥' + expiredValue"></span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-300">VIP链接数量</span>
                                <span class="text-purple-400 font-semibold" x-text="vipLinks + ' 个'"></span>
                            </div>
                            <hr class="border-gray-600">
                            <div class="flex justify-between items-center text-lg">
                                <span class="text-white font-semibold">总价值</span>
                                <span class="text-white font-bold" x-text="'¥' + totalValue"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 仪表板数据管理
function dashboardData() {
    return {
        // 快速分析
        quickAnalyzeText: '',
        isAnalyzing: false,
        quickAnalyzeProgress: {
            current: 0,
            total: 0
        },

        // 统计数据
        get totalLinks() {
            return this.$parent.links.length;
        },
        
        get availableGifts() {
            return this.$parent.results.filter(r => r.gift_status === 'available').length;
        },
        
        get vipLinks() {
            return this.$parent.results.filter(r => r.is_vip_link).length;
        },
        
        get successRate() {
            if (this.$parent.results.length === 0) return 0;
            const successful = this.$parent.results.filter(r => r.status === 'success').length;
            return Math.round((successful / this.$parent.results.length) * 100);
        },
        
        get availablePercentage() {
            if (this.$parent.results.length === 0) return 0;
            return Math.round((this.availableGifts / this.$parent.results.length) * 100);
        },
        
        get validVipPercentage() {
            const vipResults = this.$parent.results.filter(r => r.is_vip_link);
            if (vipResults.length === 0) return 0;
            const validVip = vipResults.filter(r => r.vip_status === 'valid').length;
            return Math.round((validVip / vipResults.length) * 100);
        },
        
        get recentAdded() {
            const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
            return this.$parent.results.filter(r => r.timestamp > oneDayAgo).length;
        },
        
        get recentResults() {
            return this.$parent.results
                .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
                .slice(0, 5);
        },
        
        // 图表数据
        get availableArc() {
            const total = this.$parent.results.length;
            if (total === 0) return 0;
            return (this.availableGifts / total) * 502; // 502是圆周长
        },
        
        get expiredArc() {
            const total = this.$parent.results.length;
            if (total === 0) return 0;
            const expired = this.$parent.results.filter(r => r.gift_status === 'expired').length;
            return (expired / total) * 502;
        },
        
        get claimedArc() {
            const total = this.$parent.results.length;
            if (total === 0) return 0;
            const claimed = this.$parent.results.filter(r => r.gift_status === 'claimed').length;
            return (claimed / total) * 502;
        },
        
        // 价值统计
        get availableValue() {
            return this.$parent.results
                .filter(r => r.gift_status === 'available')
                .reduce((sum, r) => sum + (r.gift_price || 0), 0);
        },
        
        get expiredValue() {
            return this.$parent.results
                .filter(r => r.gift_status === 'expired')
                .reduce((sum, r) => sum + (r.gift_price || 0), 0);
        },
        
        get totalValue() {
            return this.availableValue + this.expiredValue;
        },

        // 方法
        async startQuickAnalyze() {
            if (!this.quickAnalyzeText.trim() || this.isAnalyzing) return;
            
            const links = Utils.parseLinks(this.quickAnalyzeText);
            if (links.length === 0) {
                Utils.showToast('没有找到有效的链接', 'warning');
                return;
            }
            
            this.isAnalyzing = true;
            this.quickAnalyzeProgress = { current: 0, total: links.length };
            
            try {
                // 添加链接到主列表
                this.$parent.links.push(...links);
                
                // 开始分析
                const results = await AnalyzerAPI.batchAnalyze(
                    links,
                    this.$parent.settings.maxWorkers,
                    (current, total) => {
                        this.quickAnalyzeProgress.current = current;
                        this.quickAnalyzeProgress.total = total;
                    },
                    (result) => {
                        this.$parent.results.push(result);
                        this.$parent.saveData();
                    }
                );
                
                Utils.showToast(`快速分析完成！分析了 ${results.length} 个链接`, 'success');
                this.clearQuickAnalyze();
                
            } catch (error) {
                Utils.showToast('分析过程中出现错误', 'error');
                console.error(error);
            } finally {
                this.isAnalyzing = false;
            }
        },
        
        clearQuickAnalyze() {
            this.quickAnalyzeText = '';
            this.quickAnalyzeProgress = { current: 0, total: 0 };
        },
        
        getStatusText(status) {
            const statusMap = {
                'available': '可用',
                'expired': '过期',
                'claimed': '已领取',
                'invalid': '无效'
            };
            return statusMap[status] || '未知';
        }
    }
}