// 设置页面组件
function loadSettings() {
    const content = document.getElementById('settings-content');
    
    content.innerHTML = `
        <div class="space-y-8" x-data="settingsData()">
            <!-- 页面标题 -->
            <div class="glass-effect rounded-xl p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-3xl font-bold text-white mb-2">
                            <i class="fas fa-cogs mr-3 text-orange-400"></i>
                            设置
                        </h2>
                        <p class="text-gray-300">配置分析器参数和应用程序偏好设置</p>
                    </div>
                    <div class="hidden md:block">
                        <img src="${Utils.getUnsplashImage(300, 200, 'settings,gear')}" 
                             alt="Settings" 
                             class="w-48 h-32 object-cover rounded-lg shadow-lg opacity-60">
                    </div>
                </div>
            </div>

            <!-- 设置面板 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- 分析设置 -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-xl font-semibold text-white mb-6">
                        <i class="fas fa-search mr-2 text-blue-400"></i>
                        分析设置
                    </h3>
                    
                    <div class="space-y-6">
                        <!-- 并发线程数 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-3">
                                并发线程数
                                <span class="text-gray-400 text-xs ml-2">（建议: 5-20，过高可能被限制）</span>
                            </label>
                            <div class="space-y-3">
                                <input 
                                    type="range" 
                                    min="1" 
                                    max="50" 
                                    x-model="settings.maxWorkers"
                                    @input="updateSetting('maxWorkers', $event.target.value)"
                                    class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer">
                                <div class="flex justify-between text-xs text-gray-400">
                                    <span>1</span>
                                    <span class="font-medium text-white text-sm" x-text="settings.maxWorkers + ' 线程'"></span>
                                    <span>50</span>
                                </div>
                                <div class="text-xs text-gray-400">
                                    <span x-show="settings.maxWorkers <= 5" class="text-green-400">保守模式 - 稳定性优先</span>
                                    <span x-show="settings.maxWorkers > 5 && settings.maxWorkers <= 15" class="text-yellow-400">平衡模式 - 性能与稳定性兼顾</span>
                                    <span x-show="settings.maxWorkers > 15" class="text-red-400">激进模式 - 性能优先（可能不稳定）</span>
                                </div>
                            </div>
                        </div>

                        <!-- 请求超时 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                请求超时时间 (秒)
                            </label>
                            <input 
                                type="number" 
                                min="5" 
                                max="60" 
                                x-model="settings.timeout"
                                @change="updateSetting('timeout', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                            <p class="text-xs text-gray-400 mt-1">网络较慢时可适当增加</p>
                        </div>

                        <!-- 请求延迟 -->
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
                                @change="updateSetting('delay', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                            <p class="text-xs text-gray-400 mt-1">增加延迟可以降低被限制的风险</p>
                        </div>

                        <!-- 重试次数 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                失败重试次数
                            </label>
                            <select 
                                x-model="settings.retryCount"
                                @change="updateSetting('retryCount', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                                <option value="0">不重试</option>
                                <option value="1">重试 1 次</option>
                                <option value="2">重试 2 次</option>
                                <option value="3">重试 3 次</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- 数据设置 -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-xl font-semibold text-white mb-6">
                        <i class="fas fa-database mr-2 text-green-400"></i>
                        数据设置
                    </h3>
                    
                    <div class="space-y-6">
                        <!-- 自动保存 -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">自动保存</label>
                                <p class="text-xs text-gray-400">分析结果实时保存到本地</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    x-model="settings.autoSave"
                                    @change="updateSetting('autoSave', $event.target.checked)"
                                    class="sr-only peer">
                                <div class="w-11 h-6 bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                            </label>
                        </div>

                        <!-- 数据清理 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                数据保留时间
                            </label>
                            <select 
                                x-model="settings.dataRetention"
                                @change="updateSetting('dataRetention', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                                <option value="7">7 天</option>
                                <option value="30">30 天</option>
                                <option value="90">90 天</option>
                                <option value="365">1 年</option>
                                <option value="0">永久保留</option>
                            </select>
                        </div>

                        <!-- 导出格式 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                默认导出格式
                            </label>
                            <select 
                                x-model="settings.exportFormat"
                                @change="updateSetting('exportFormat', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                                <option value="txt">文本文件 (.txt)</option>
                                <option value="csv">CSV文件 (.csv)</option>
                                <option value="json">JSON文件 (.json)</option>
                            </select>
                        </div>

                        <!-- 数据统计 -->
                        <div class="bg-white bg-opacity-5 rounded-lg p-4">
                            <h4 class="text-sm font-medium text-gray-300 mb-3">存储统计</h4>
                            <div class="space-y-2 text-xs">
                                <div class="flex justify-between">
                                    <span class="text-gray-400">分析结果</span>
                                    <span class="text-white" x-text="dataStats.results + ' 条'"></span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">存储大小</span>
                                    <span class="text-white" x-text="dataStats.size"></span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-400">最后更新</span>
                                    <span class="text-white" x-text="dataStats.lastUpdate"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 界面设置 -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-xl font-semibold text-white mb-6">
                        <i class="fas fa-paint-brush mr-2 text-purple-400"></i>
                        界面设置
                    </h3>
                    
                    <div class="space-y-6">
                        <!-- 主题设置 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                主题风格
                            </label>
                            <div class="grid grid-cols-2 gap-3">
                                <button 
                                    @click="updateSetting('theme', 'dark')"
                                    :class="settings.theme === 'dark' ? 'ring-2 ring-blue-500' : ''"
                                    class="bg-gray-800 border border-gray-600 rounded-lg p-3 text-white hover:bg-gray-700 transition-colors">
                                    <i class="fas fa-moon mb-2"></i>
                                    <div class="text-sm">深色主题</div>
                                </button>
                                <button 
                                    @click="updateSetting('theme', 'light')"
                                    :class="settings.theme === 'light' ? 'ring-2 ring-blue-500' : ''"
                                    class="bg-gray-200 border border-gray-300 rounded-lg p-3 text-gray-800 hover:bg-gray-100 transition-colors">
                                    <i class="fas fa-sun mb-2"></i>
                                    <div class="text-sm">浅色主题</div>
                                </button>
                            </div>
                        </div>

                        <!-- 动画效果 -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">动画效果</label>
                                <p class="text-xs text-gray-400">页面切换和元素动画</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    x-model="settings.animations"
                                    @change="updateSetting('animations', $event.target.checked)"
                                    class="sr-only peer">
                                <div class="w-11 h-6 bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                            </label>
                        </div>

                        <!-- 音效 -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">提示音效</label>
                                <p class="text-xs text-gray-400">完成分析时播放提示音</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    x-model="settings.soundEffects"
                                    @change="updateSetting('soundEffects', $event.target.checked)"
                                    class="sr-only peer">
                                <div class="w-11 h-6 bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                            </label>
                        </div>

                        <!-- 桌面通知 -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">桌面通知</label>
                                <p class="text-xs text-gray-400">浏览器桌面通知提醒</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    x-model="settings.showNotifications"
                                    @change="updateSetting('showNotifications', $event.target.checked)"
                                    class="sr-only peer">
                                <div class="w-11 h-6 bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                            </label>
                        </div>

                        <!-- 语言设置 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                语言
                            </label>
                            <select 
                                x-model="settings.language"
                                @change="updateSetting('language', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                                <option value="zh-CN">简体中文</option>
                                <option value="zh-TW">繁體中文</option>
                                <option value="en-US">English</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- 高级设置 -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-xl font-semibold text-white mb-6">
                        <i class="fas fa-tools mr-2 text-red-400"></i>
                        高级设置
                    </h3>
                    
                    <div class="space-y-6">
                        <!-- 调试模式 -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="text-sm font-medium text-gray-300">调试模式</label>
                                <p class="text-xs text-gray-400">显示详细的调试信息</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    x-model="settings.debugMode"
                                    @change="updateSetting('debugMode', $event.target.checked)"
                                    class="sr-only peer">
                                <div class="w-11 h-6 bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                            </label>
                        </div>

                        <!-- 缓存设置 -->
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">
                                缓存大小限制 (MB)
                            </label>
                            <input 
                                type="number" 
                                min="10" 
                                max="1000"
                                x-model="settings.cacheLimit"
                                @change="updateSetting('cacheLimit', $event.target.value)"
                                class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                        </div>

                        <!-- 备份还原 -->
                        <div class="space-y-3">
                            <label class="block text-sm font-medium text-gray-300">
                                数据备份与还原
                            </label>
                            <div class="flex space-x-3">
                                <button 
                                    @click="exportBackup()"
                                    class="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-download mr-2"></i>
                                    导出备份
                                </button>
                                <button 
                                    @click="importBackup()"
                                    class="flex-1 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-upload mr-2"></i>
                                    导入备份
                                </button>
                            </div>
                        </div>

                        <!-- 重置设置 -->
                        <div class="space-y-3">
                            <label class="block text-sm font-medium text-gray-300">
                                重置选项
                            </label>
                            <div class="flex space-x-3">
                                <button 
                                    @click="resetSettings()"
                                    class="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-undo mr-2"></i>
                                    重置设置
                                </button>
                                <button 
                                    @click="clearAllData()"
                                    class="flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                                    <i class="fas fa-trash mr-2"></i>
                                    清空数据
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 保存提示 -->
            <div x-show="showSaveNotice" x-transition class="fixed bottom-4 left-4 glass-effect rounded-lg p-4">
                <div class="flex items-center text-white">
                    <i class="fas fa-check-circle text-green-400 mr-2"></i>
                    <span>设置已保存</span>
                </div>
            </div>
        </div>

        <!-- 隐藏的文件输入 -->
        <input type="file" accept=".json" x-ref="backupFileInput" @change="handleBackupFile" class="hidden">
    `;
}

// 设置页面数据管理
function settingsData() {
    return {
        settings: {
            // 分析设置
            maxWorkers: 10,
            timeout: 15,
            delay: 100,
            retryCount: 1,
            
            // 数据设置
            autoSave: true,
            dataRetention: 30,
            exportFormat: 'txt',
            
            // 界面设置
            theme: 'dark',
            animations: true,
            soundEffects: false,
            showNotifications: true,
            language: 'zh-CN',
            
            // 高级设置
            debugMode: false,
            cacheLimit: 100
        },
        
        showSaveNotice: false,

        // 初始化
        init() {
            this.loadSettings();
        },

        // 计算属性
        get dataStats() {
            const results = this.$parent.results.length;
            const dataStr = JSON.stringify(this.$parent.results);
            const size = new Blob([dataStr]).size;
            const lastUpdate = this.$parent.results.length > 0 ? 
                new Date(Math.max(...this.$parent.results.map(r => r.timestamp || 0))).toLocaleString('zh-CN') : 
                '无';

            return {
                results: results,
                size: Utils.formatFileSize(size),
                lastUpdate: lastUpdate
            };
        },

        // 方法
        loadSettings() {
            const saved = localStorage.getItem('giftAnalyzer_settings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
            // 同步到父组件
            this.$parent.settings = { ...this.settings };
        },

        updateSetting(key, value) {
            this.settings[key] = value;
            this.saveSettings();
            this.showSaveIndicator();
        },

        saveSettings() {
            localStorage.setItem('giftAnalyzer_settings', JSON.stringify(this.settings));
            // 同步到父组件
            this.$parent.settings = { ...this.settings };
        },

        showSaveIndicator() {
            this.showSaveNotice = true;
            setTimeout(() => {
                this.showSaveNotice = false;
            }, 2000);
        },

        async exportBackup() {
            const backup = {
                settings: this.settings,
                results: this.$parent.results,
                links: this.$parent.links,
                timestamp: Date.now(),
                version: '2.0'
            };

            const data = JSON.stringify(backup, null, 2);
            const filename = `网易云分析器备份_${new Date().toISOString().slice(0, 10)}.json`;
            Utils.downloadFile(data, filename, 'application/json');
            Utils.showToast('备份文件已导出', 'success');
        },

        importBackup() {
            this.$refs.backupFileInput.click();
        },

        async handleBackupFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            try {
                const text = await this.readFileAsText(file);
                const backup = JSON.parse(text);

                if (!backup.settings || !backup.results) {
                    throw new Error('备份文件格式不正确');
                }

                // 确认导入
                if (confirm('导入备份将覆盖当前所有数据，确定继续吗？')) {
                    this.settings = { ...this.settings, ...backup.settings };
                    this.$parent.results = backup.results || [];
                    this.$parent.links = backup.links || [];
                    
                    this.saveSettings();
                    this.$parent.saveData();
                    
                    Utils.showToast('备份数据已导入', 'success');
                }
            } catch (error) {
                Utils.showToast('备份文件格式错误', 'error');
                console.error(error);
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

        resetSettings() {
            if (confirm('确定要重置所有设置为默认值吗？')) {
                this.settings = {
                    maxWorkers: 10,
                    timeout: 15,
                    delay: 100,
                    retryCount: 1,
                    autoSave: true,
                    dataRetention: 30,
                    exportFormat: 'txt',
                    theme: 'dark',
                    animations: true,
                    soundEffects: false,
                    showNotifications: true,
                    language: 'zh-CN',
                    debugMode: false,
                    cacheLimit: 100
                };
                this.saveSettings();
                Utils.showToast('设置已重置为默认值', 'warning');
            }
        },

        clearAllData() {
            if (confirm('确定要清空所有数据吗？此操作不可恢复！')) {
                this.$parent.clearAllData();
                Utils.showToast('所有数据已清空', 'warning');
            }
        }
    }
}