// 分析器页面组件
function loadAnalyzer() {
    const content = document.getElementById('analyzer-content');
    
    content.innerHTML = `
        <div class="space-y-8" x-data="analyzerData()">
            <!-- 页面标题 -->
            <div class="glass-effect rounded-xl p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-3xl font-bold text-white mb-2">
                            <i class="fas fa-search mr-3 text-blue-400"></i>
                            链接分析器
                        </h2>
                        <p class="text-gray-300">批量分析网易云音乐礼品卡链接状态和VIP邀请链接有效期</p>
                    </div>
                    <div class="hidden md:block">
                        <img src="${Utils.getUnsplashImage(300, 200, 'analytics,computer')}" 
                             alt="Analytics" 
                             class="w-48 h-32 object-cover rounded-lg shadow-lg opacity-60">
                    </div>
                </div>
            </div>

            <!-- 输入区域 -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- 链接输入 -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- 文本输入 -->
                    <div class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold text-white mb-4">
                            <i class="fas fa-edit mr-2 text-green-400"></i>
                            输入链接
                        </h3>
                        <div class="space-y-4">
                            <textarea 
                                x-model="linksText"
                                placeholder="粘贴礼品卡链接，每行一个&#10;支持格式：&#10;http://163cn.tv/xxxxxx&#10;https://music.163.com/g/vip-invite-cashier/..."
                                class="w-full h-64 bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-4 text-white placeholder-gray-400 resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                @input="validateLinks()"
                            ></textarea>
                            
                            <div class="flex flex-wrap gap-3">
                                <button 
                                    @click="loadFromFile()"
                                    class="flex items-center bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-file-upload mr-2"></i>
                                    从文件加载
                                </button>
                                <button 
                                    @click="pasteFromClipboard()"
                                    class="flex items-center bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-clipboard mr-2"></i>
                                    从剪贴板粘贴
                                </button>
                                <button 
                                    @click="clearLinks()"
                                    class="flex items-center bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-trash mr-2"></i>
                                    清空
                                </button>
                                <button 
                                    @click="generateSampleLinks()"
                                    class="flex items-center bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-magic mr-2"></i>
                                    生成示例
                                </button>
                            </div>
                            
                            <!-- 链接验证状态 -->
                            <div x-show="validationStatus.checked" class="space-y-2">
                                <div class="flex justify-between text-sm">
                                    <span class="text-gray-300">链接验证</span>
                                    <span class="text-blue-400" x-text="validationStatus.valid + '/' + validationStatus.total + ' 有效'"></span>
                                </div>
                                <div class="w-full bg-gray-700 rounded-full h-2">
                                    <div class="bg-green-500 h-2 rounded-full transition-all duration-300" 
                                         :style="'width: ' + (validationStatus.valid / Math.max(validationStatus.total, 1) * 100) + '%'">
                                    </div>
                                </div>
                                <div x-show="validationStatus.invalid > 0" class="text-yellow-400 text-sm">
                                    <i class="fas fa-exclamation-triangle mr-1"></i>
                                    发现 <span x-text="validationStatus.invalid"></span> 个无效链接
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 分析进度 -->
                    <div x-show="isAnalyzing || analysisResults.length > 0" class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold text-white mb-4">
                            <i class="fas fa-chart-line mr-2 text-yellow-400"></i>
                            分析进度
                        </h3>
                        
                        <!-- 进度条 -->
                        <div x-show="isAnalyzing" class="space-y-4">
                            <div class="flex justify-between text-sm text-gray-300">
                                <span>进度</span>
                                <span x-text="progress.current + '/' + progress.total + ' (' + Math.round(progress.percentage) + '%)'"></span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-3">
                                <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-300" 
                                     :style="'width: ' + progress.percentage + '%'">
                                </div>
                            </div>
                            <div class="flex justify-between text-sm text-gray-400">
                                <span x-text="'估计剩余时间: ' + estimatedTimeRemaining"></span>
                                <span x-text="'速度: ' + analysisSpeed + ' 链接/秒'"></span>
                            </div>
                        </div>

                        <!-- 实时统计 -->
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                            <div class="text-center">
                                <p class="text-2xl font-bold text-green-400" x-text="currentStats.available"></p>
                                <p class="text-sm text-gray-300">可用</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-red-400" x-text="currentStats.expired"></p>
                                <p class="text-sm text-gray-300">过期</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-yellow-400" x-text="currentStats.claimed"></p>
                                <p class="text-sm text-gray-300">已领取</p>
                            </div>
                            <div class="text-center">
                                <p class="text-2xl font-bold text-purple-400" x-text="currentStats.vip"></p>
                                <p class="text-sm text-gray-300">VIP链接</p>
                            </div>
                        </div>

                        <!-- 控制按钮 -->
                        <div class="flex space-x-3 mt-6">
                            <button 
                                x-show="!isAnalyzing"
                                @click="startAnalysis()"
                                :disabled="!canStartAnalysis"
                                class="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-play mr-2"></i>
                                开始分析
                            </button>
                            <button 
                                x-show="isAnalyzing && !isPaused"
                                @click="pauseAnalysis()"
                                class="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-pause mr-2"></i>
                                暂停
                            </button>
                            <button 
                                x-show="isAnalyzing && isPaused"
                                @click="resumeAnalysis()"
                                class="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-play mr-2"></i>
                                继续
                            </button>
                            <button 
                                x-show="isAnalyzing"
                                @click="stopAnalysis()"
                                class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-stop mr-2"></i>
                                停止
                            </button>
                        </div>
                    </div>
                </div>

                <!-- 设置面板 -->
                <div class="space-y-6">
                    <!-- 分析设置 -->
                    <div class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold text-white mb-4">
                            <i class="fas fa-cogs mr-2 text-orange-400"></i>
                            分析设置
                        </h3>
                        <div class="space-y-4">
                            <!-- 并发数 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">
                                    并发线程数
                                    <span class="text-gray-400">（建议: 5-20）</span>
                                </label>
                                <input 
                                    type="range" 
                                    min="1" 
                                    max="50" 
                                    x-model="settings.maxWorkers"
                                    class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider">
                                <div class="flex justify-between text-xs text-gray-400 mt-1">
                                    <span>1</span>
                                    <span class="font-medium text-white" x-text="settings.maxWorkers"></span>
                                    <span>50</span>
                                </div>
                            </div>

                            <!-- 超时设置 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">
                                    请求超时 (秒)
                                </label>
                                <input 
                                    type="number" 
                                    min="5" 
                                    max="60" 
                                    x-model="settings.timeout"
                                    class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-2 text-white">
                            </div>

                            <!-- 重试次数 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">
                                    重试次数
                                </label>
                                <select 
                                    x-model="settings.retryCount"
                                    class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-2 text-white">
                                    <option value="0">不重试</option>
                                    <option value="1">1次</option>
                                    <option value="2">2次</option>
                                    <option value="3">3次</option>
                                </select>
                            </div>

                            <!-- 延迟设置 -->
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">
                                    请求间隔 (毫秒)
                                </label>
                                <input 
                                    type="number" 
                                    min="0" 
                                    max="5000" 
                                    step="100"
                                    x-model="settings.delay"
                                    class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-2 text-white">
                            </div>
                        </div>
                    </div>

                    <!-- 过滤设置 -->
                    <div class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold text-white mb-4">
                            <i class="fas fa-filter mr-2 text-indigo-400"></i>
                            结果过滤
                        </h3>
                        <div class="space-y-3">
                            <label class="flex items-center text-gray-300">
                                <input type="checkbox" x-model="filters.showAvailable" class="mr-3 rounded">
                                <span class="flex items-center">
                                    <div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                                    显示可用礼品
                                </span>
                            </label>
                            <label class="flex items-center text-gray-300">
                                <input type="checkbox" x-model="filters.showExpired" class="mr-3 rounded">
                                <span class="flex items-center">
                                    <div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                                    显示过期礼品
                                </span>
                            </label>
                            <label class="flex items-center text-gray-300">
                                <input type="checkbox" x-model="filters.showClaimed" class="mr-3 rounded">
                                <span class="flex items-center">
                                    <div class="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                                    显示已领取礼品
                                </span>
                            </label>
                            <label class="flex items-center text-gray-300">
                                <input type="checkbox" x-model="filters.showVip" class="mr-3 rounded">
                                <span class="flex items-center">
                                    <div class="w-3 h-3 bg-purple-500 rounded-full mr-2"></div>
                                    显示VIP链接
                                </span>
                            </label>
                            <label class="flex items-center text-gray-300">
                                <input type="checkbox" x-model="filters.showInvalid" class="mr-3 rounded">
                                <span class="flex items-center">
                                    <div class="w-3 h-3 bg-gray-500 rounded-full mr-2"></div>
                                    显示无效链接
                                </span>
                            </label>
                        </div>
                    </div>

                    <!-- 导出选项 -->
                    <div class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold text-white mb-4">
                            <i class="fas fa-download mr-2 text-teal-400"></i>
                            导出选项
                        </h3>
                        <div class="space-y-3">
                            <button 
                                @click="exportResults('available')"
                                :disabled="currentStats.available === 0"
                                class="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-file-export mr-2"></i>
                                导出可用链接
                            </button>
                            <button 
                                @click="exportResults('all')"
                                :disabled="analysisResults.length === 0"
                                class="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-file-download mr-2"></i>
                                导出全部结果
                            </button>
                            <button 
                                @click="exportResults('json')"
                                :disabled="analysisResults.length === 0"
                                class="w-full bg-purple-500 hover:bg-purple-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                <i class="fas fa-file-code mr-2"></i>
                                导出JSON格式
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 实时结果预览 -->
            <div x-show="analysisResults.length > 0" class="glass-effect rounded-xl p-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-semibold text-white">
                        <i class="fas fa-eye mr-2 text-cyan-400"></i>
                        实时结果预览
                    </h3>
                    <button 
                        @click="$parent.setActivePage('results')"
                        class="text-cyan-400 hover:text-cyan-300 text-sm">
                        查看详细结果 <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>

                <div class="max-h-96 overflow-y-auto space-y-2">
                    <template x-for="result in filteredPreviewResults" :key="result.short_url">
                        <div class="bg-white bg-opacity-5 rounded-lg p-3 flex items-center justify-between">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center space-x-3">
                                    <i 
                                        :class="{
                                            'fas fa-gift text-green-400': result.gift_status === 'available',
                                            'fas fa-clock text-red-400': result.gift_status === 'expired',
                                            'fas fa-check-circle text-yellow-400': result.gift_status === 'claimed',
                                            'fas fa-crown text-purple-400': result.is_vip_link,
                                            'fas fa-times-circle text-gray-400': result.gift_status === 'invalid'
                                        }"
                                    ></i>
                                    <div>
                                        <p class="text-white text-sm font-medium" x-text="result.gift_type || 'Unknown'"></p>
                                        <p class="text-gray-400 text-xs truncate" x-text="result.short_url"></p>
                                    </div>
                                </div>
                            </div>
                            <div class="ml-3 text-right">
                                <p 
                                    class="text-sm font-medium"
                                    :class="{
                                        'text-green-400': result.gift_status === 'available',
                                        'text-red-400': result.gift_status === 'expired',
                                        'text-yellow-400': result.gift_status === 'claimed',
                                        'text-gray-400': result.gift_status === 'invalid'
                                    }"
                                    x-text="result.status_text || getStatusText(result.gift_status)"
                                ></p>
                                <p x-show="result.gift_price" class="text-xs text-gray-400" x-text="'¥' + result.gift_price"></p>
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </div>

        <!-- 文件上传输入 -->
        <input type="file" accept=".txt,.csv" x-ref="fileInput" @change="handleFileSelect" class="hidden">
    `;
}

// 分析器数据管理
function analyzerData() {
    return {
        // 输入数据
        linksText: '',
        validationStatus: {
            checked: false,
            total: 0,
            valid: 0,
            invalid: 0
        },

        // 分析状态
        isAnalyzing: false,
        isPaused: false,
        analysisResults: [],
        progress: {
            current: 0,
            total: 0,
            percentage: 0
        },
        startTime: null,
        
        // 设置
        settings: {
            maxWorkers: 10,
            timeout: 15,
            retryCount: 1,
            delay: 100
        },

        // 过滤器
        filters: {
            showAvailable: true,
            showExpired: true,
            showClaimed: true,
            showVip: true,
            showInvalid: false
        },

        // 初始化
        init() {
            // 从父组件同步设置
            this.settings = { ...this.$parent.settings };
            
            // 如果有未完成的分析结果，显示它们
            if (this.$parent.results.length > 0) {
                this.analysisResults = [...this.$parent.results];
            }
        },

        // 计算属性
        get canStartAnalysis() {
            const links = Utils.parseLinks(this.linksText);
            return links.length > 0 && !this.isAnalyzing;
        },

        get currentStats() {
            return {
                available: this.analysisResults.filter(r => r.gift_status === 'available').length,
                expired: this.analysisResults.filter(r => r.gift_status === 'expired').length,
                claimed: this.analysisResults.filter(r => r.gift_status === 'claimed').length,
                vip: this.analysisResults.filter(r => r.is_vip_link).length
            };
        },

        get estimatedTimeRemaining() {
            if (!this.isAnalyzing || this.progress.current === 0) return '计算中...';
            
            const elapsed = (Date.now() - this.startTime) / 1000;
            const speed = this.progress.current / elapsed;
            const remaining = (this.progress.total - this.progress.current) / speed;
            
            if (remaining < 60) {
                return Math.round(remaining) + ' 秒';
            } else if (remaining < 3600) {
                return Math.round(remaining / 60) + ' 分钟';
            } else {
                return Math.round(remaining / 3600) + ' 小时';
            }
        },

        get analysisSpeed() {
            if (!this.isAnalyzing || this.progress.current === 0) return '0';
            
            const elapsed = (Date.now() - this.startTime) / 1000;
            const speed = this.progress.current / elapsed;
            return speed.toFixed(1);
        },

        get filteredPreviewResults() {
            return this.analysisResults
                .filter(result => {
                    if (result.gift_status === 'available' && this.filters.showAvailable) return true;
                    if (result.gift_status === 'expired' && this.filters.showExpired) return true;
                    if (result.gift_status === 'claimed' && this.filters.showClaimed) return true;
                    if (result.is_vip_link && this.filters.showVip) return true;
                    if (result.gift_status === 'invalid' && this.filters.showInvalid) return true;
                    return false;
                })
                .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
                .slice(0, 20); // 只显示最新的20个结果
        },

        // 方法
        validateLinks() {
            const text = this.linksText.trim();
            if (!text) {
                this.validationStatus = { checked: false, total: 0, valid: 0, invalid: 0 };
                return;
            }

            const lines = text.split('\n').filter(line => line.trim());
            const validLinks = lines.filter(line => Utils.validateLink(line.trim()));
            
            this.validationStatus = {
                checked: true,
                total: lines.length,
                valid: validLinks.length,
                invalid: lines.length - validLinks.length
            };
        },

        async loadFromFile() {
            this.$refs.fileInput.click();
        },

        async handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;

            try {
                const text = await this.readFileAsText(file);
                this.linksText = text;
                this.validateLinks();
                Utils.showToast(`已加载 ${file.name}`, 'success');
            } catch (error) {
                Utils.showToast('文件读取失败', 'error');
            }
        },

        readFileAsText(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = e => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsText(file);
            });
        },

        async pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                this.linksText = text;
                this.validateLinks();
                Utils.showToast('已从剪贴板粘贴', 'success');
            } catch (error) {
                Utils.showToast('无法访问剪贴板', 'error');
            }
        },

        clearLinks() {
            this.linksText = '';
            this.validationStatus = { checked: false, total: 0, valid: 0, invalid: 0 };
        },

        generateSampleLinks() {
            const sampleLinks = [
                'http://163cn.tv/GBm6AHn',
                'http://163cn.tv/HCp7BIo',
                'http://163cn.tv/IDq8CJp',
                'https://music.163.com/g/vip-invite-cashier/sample1',
                'https://music.163.com/g/vip-invite-cashier/sample2',
                'http://163cn.tv/JEr9DKq',
                'http://163cn.tv/KFs0ELr'
            ];
            
            this.linksText = sampleLinks.join('\n');
            this.validateLinks();
            Utils.showToast('已生成示例链接', 'info');
        },

        async startAnalysis() {
            if (!this.canStartAnalysis) return;

            const links = Utils.parseLinks(this.linksText);
            
            this.isAnalyzing = true;
            this.isPaused = false;
            this.startTime = Date.now();
            this.progress = { current: 0, total: links.length, percentage: 0 };
            this.analysisResults = [];

            // 同步设置到父组件
            this.$parent.settings = { ...this.settings };
            this.$parent.saveSettings();

            // 添加链接到父组件
            this.$parent.links.push(...links);

            try {
                Utils.showToast(`开始分析 ${links.length} 个链接`, 'info');

                const results = await AnalyzerAPI.batchAnalyze(
                    links,
                    this.settings.maxWorkers,
                    (current, total) => {
                        this.progress.current = current;
                        this.progress.total = total;
                        this.progress.percentage = (current / total) * 100;
                    },
                    (result) => {
                        // 实时添加单个结果
                        this.analysisResults.push(result);
                        this.$parent.results.push(result);
                        this.$parent.saveData();
                    }
                );

                Utils.showToast(`分析完成！共处理 ${results.length} 个链接`, 'success');

            } catch (error) {
                Utils.showToast('分析过程中出现错误', 'error');
                console.error(error);
            } finally {
                this.isAnalyzing = false;
                this.isPaused = false;
            }
        },

        pauseAnalysis() {
            this.isPaused = true;
            Utils.showToast('已暂停分析', 'warning');
            // 在实际实现中，这里需要暂停正在进行的分析
        },

        resumeAnalysis() {
            this.isPaused = false;
            Utils.showToast('已恢复分析', 'info');
            // 在实际实现中，这里需要恢复暂停的分析
        },

        stopAnalysis() {
            this.isAnalyzing = false;
            this.isPaused = false;
            Utils.showToast('已停止分析', 'warning');
            // 在实际实现中，这里需要停止正在进行的分析
        },

        exportResults(type) {
            let data, filename, contentType;

            switch (type) {
                case 'available':
                    const availableLinks = this.analysisResults
                        .filter(r => r.gift_status === 'available')
                        .map(r => r.short_url);
                    data = availableLinks.join('\n');
                    filename = `可用礼品链接_${new Date().toISOString().slice(0, 10)}.txt`;
                    contentType = 'text/plain';
                    break;

                case 'all':
                    const allLinks = this.analysisResults.map(r => r.short_url);
                    data = allLinks.join('\n');
                    filename = `全部分析链接_${new Date().toISOString().slice(0, 10)}.txt`;
                    contentType = 'text/plain';
                    break;

                case 'json':
                    data = JSON.stringify(this.analysisResults, null, 2);
                    filename = `分析结果_${new Date().toISOString().slice(0, 10)}.json`;
                    contentType = 'application/json';
                    break;

                default:
                    return;
            }

            Utils.downloadFile(data, filename, contentType);
            Utils.showToast(`已导出 ${filename}`, 'success');
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