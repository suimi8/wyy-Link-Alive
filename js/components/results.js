// 结果页面组件
function loadResults() {
    const content = document.getElementById('results-content');
    
    content.innerHTML = `
        <div class="space-y-8" x-data="resultsData()">
            <!-- 页面标题和操作 -->
            <div class="glass-effect rounded-xl p-6">
                <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    <div>
                        <h2 class="text-3xl font-bold text-white mb-2">
                            <i class="fas fa-chart-bar mr-3 text-purple-400"></i>
                            分析结果
                        </h2>
                        <p class="text-gray-300">
                            共 <span class="text-blue-400 font-semibold" x-text="totalResults"></span> 个结果
                            · 可用 <span class="text-green-400 font-semibold" x-text="availableCount"></span> 个
                            · VIP <span class="text-purple-400 font-semibold" x-text="vipCount"></span> 个
                        </p>
                    </div>
                    <div class="flex flex-wrap gap-3">
                        <button 
                            @click="refreshResults()"
                            class="flex items-center bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                            <i class="fas fa-sync-alt mr-2"></i>
                            刷新
                        </button>
                        <button 
                            @click="exportAllResults()"
                            :disabled="totalResults === 0"
                            class="flex items-center bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                            <i class="fas fa-download mr-2"></i>
                            导出全部
                        </button>
                        <button 
                            @click="clearAllResults()"
                            :disabled="totalResults === 0"
                            class="flex items-center bg-red-500 hover:bg-red-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors duration-200">
                            <i class="fas fa-trash mr-2"></i>
                            清空数据
                        </button>
                    </div>
                </div>
            </div>

            <!-- 统计卡片 -->
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-green-400" x-text="stats.available"></div>
                    <div class="text-sm text-gray-300 mt-1">可用礼品</div>
                    <div class="text-xs text-green-400 mt-1" x-text="'¥' + stats.availableValue"></div>
                </div>
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-red-400" x-text="stats.expired"></div>
                    <div class="text-sm text-gray-300 mt-1">已过期</div>
                    <div class="text-xs text-red-400 mt-1" x-text="'¥' + stats.expiredValue"></div>
                </div>
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-yellow-400" x-text="stats.claimed"></div>
                    <div class="text-sm text-gray-300 mt-1">已领取</div>
                    <div class="text-xs text-yellow-400 mt-1" x-text="'¥' + stats.claimedValue"></div>
                </div>
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-purple-400" x-text="stats.vip"></div>
                    <div class="text-sm text-gray-300 mt-1">VIP链接</div>
                    <div class="text-xs text-purple-400 mt-1" x-text="stats.validVip + ' 有效'"></div>
                </div>
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-gray-400" x-text="stats.invalid"></div>
                    <div class="text-sm text-gray-300 mt-1">无效链接</div>
                    <div class="text-xs text-gray-400 mt-1">--</div>
                </div>
                <div class="glass-effect rounded-lg p-4 text-center hover-lift">
                    <div class="text-2xl font-bold text-blue-400" x-text="Math.round(stats.successRate) + '%'"></div>
                    <div class="text-sm text-gray-300 mt-1">成功率</div>
                    <div class="text-xs text-blue-400 mt-1">分析质量</div>
                </div>
            </div>

            <!-- 过滤和搜索 -->
            <div class="glass-effect rounded-xl p-6">
                <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    <!-- 搜索框 -->
                    <div class="lg:col-span-2">
                        <label class="block text-sm font-medium text-gray-300 mb-2">
                            <i class="fas fa-search mr-2"></i>
                            搜索链接或类型
                        </label>
                        <input 
                            type="text" 
                            x-model="searchQuery"
                            @input="applyFilters()"
                            placeholder="输入链接或礼品类型关键词..."
                            class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white placeholder-gray-400">
                    </div>

                    <!-- 状态过滤 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">
                            <i class="fas fa-filter mr-2"></i>
                            状态过滤
                        </label>
                        <select 
                            x-model="statusFilter"
                            @change="applyFilters()"
                            class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                            <option value="all">全部状态</option>
                            <option value="available">可用</option>
                            <option value="expired">已过期</option>
                            <option value="claimed">已领取</option>
                            <option value="invalid">无效</option>
                            <option value="vip">VIP链接</option>
                        </select>
                    </div>

                    <!-- 排序 -->
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">
                            <i class="fas fa-sort mr-2"></i>
                            排序方式
                        </label>
                        <select 
                            x-model="sortBy"
                            @change="applyFilters()"
                            class="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg p-3 text-white">
                            <option value="time_desc">时间 ↓</option>
                            <option value="time_asc">时间 ↑</option>
                            <option value="value_desc">价值 ↓</option>
                            <option value="value_asc">价值 ↑</option>
                            <option value="status">状态</option>
                        </select>
                    </div>
                </div>

                <div class="flex justify-between items-center mt-4">
                    <div class="text-sm text-gray-300">
                        显示 <span class="text-blue-400" x-text="filteredResults.length"></span> / <span x-text="totalResults"></span> 个结果
                    </div>
                    <div class="flex space-x-2">
                        <button 
                            @click="selectAll()"
                            class="text-blue-400 hover:text-blue-300 text-sm">
                            全选
                        </button>
                        <button 
                            @click="selectNone()"
                            class="text-gray-400 hover:text-gray-300 text-sm">
                            取消全选
                        </button>
                        <button 
                            @click="exportSelected()"
                            :disabled="selectedResults.length === 0"
                            class="text-green-400 hover:text-green-300 disabled:text-gray-500 text-sm">
                            导出选中 (<span x-text="selectedResults.length"></span>)
                        </button>
                    </div>
                </div>
            </div>

            <!-- 结果表格 -->
            <div class="glass-effect rounded-xl overflow-hidden">
                <div class="overflow-x-auto">
                    <div class="max-h-96 overflow-y-auto">
                        <table class="w-full text-sm">
                            <thead class="bg-white bg-opacity-10 sticky top-0">
                                <tr>
                                    <th class="px-4 py-3 text-left">
                                        <input 
                                            type="checkbox" 
                                            :checked="isAllSelected"
                                            @change="toggleSelectAll()"
                                            class="rounded">
                                    </th>
                                    <th class="px-4 py-3 text-left text-gray-300">状态</th>
                                    <th class="px-4 py-3 text-left text-gray-300">链接</th>
                                    <th class="px-4 py-3 text-left text-gray-300">类型</th>
                                    <th class="px-4 py-3 text-left text-gray-300">价值/信息</th>
                                    <th class="px-4 py-3 text-left text-gray-300">过期时间</th>
                                    <th class="px-4 py-3 text-left text-gray-300">发送者</th>
                                    <th class="px-4 py-3 text-left text-gray-300">操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                <template x-for="result in paginatedResults" :key="result.short_url">
                                    <tr class="border-b border-white border-opacity-10 hover:bg-white hover:bg-opacity-5">
                                        <td class="px-4 py-3">
                                            <input 
                                                type="checkbox" 
                                                :value="result.short_url"
                                                x-model="selectedResults"
                                                class="rounded">
                                        </td>
                                        <td class="px-4 py-3">
                                            <span 
                                                class="px-2 py-1 text-xs rounded-full inline-flex items-center"
                                                :class="{
                                                    'bg-green-500 bg-opacity-20 text-green-400': result.gift_status === 'available',
                                                    'bg-red-500 bg-opacity-20 text-red-400': result.gift_status === 'expired',
                                                    'bg-yellow-500 bg-opacity-20 text-yellow-400': result.gift_status === 'claimed',
                                                    'bg-purple-500 bg-opacity-20 text-purple-400': result.is_vip_link,
                                                    'bg-gray-500 bg-opacity-20 text-gray-400': result.gift_status === 'invalid'
                                                }">
                                                <i 
                                                    :class="{
                                                        'fas fa-gift': result.gift_status === 'available',
                                                        'fas fa-clock': result.gift_status === 'expired',
                                                        'fas fa-check-circle': result.gift_status === 'claimed',
                                                        'fas fa-crown': result.is_vip_link,
                                                        'fas fa-times-circle': result.gift_status === 'invalid'
                                                    }"
                                                    class="mr-1"
                                                ></i>
                                                <span x-text="getStatusText(result)"></span>
                                            </span>
                                        </td>
                                        <td class="px-4 py-3">
                                            <div class="flex items-center space-x-2">
                                                <span class="text-white text-sm font-mono truncate max-w-xs" x-text="result.short_url"></span>
                                                <button 
                                                    @click="copyToClipboard(result.short_url)"
                                                    class="text-gray-400 hover:text-blue-400 transition-colors">
                                                    <i class="fas fa-copy text-xs"></i>
                                                </button>
                                            </div>
                                        </td>
                                        <td class="px-4 py-3">
                                            <span class="text-white" x-text="result.gift_type || 'Unknown'"></span>
                                        </td>
                                        <td class="px-4 py-3">
                                            <div x-show="result.gift_price">
                                                <span class="text-green-400 font-semibold" x-text="'¥' + result.gift_price"></span>
                                            </div>
                                            <div x-show="result.status_text && !result.gift_price">
                                                <span class="text-gray-300 text-sm" x-text="result.status_text"></span>
                                            </div>
                                            <div x-show="result.is_vip_link && result.remaining_days !== undefined">
                                                <span class="text-purple-400 text-sm" x-text="result.remaining_days + ' 天'"></span>
                                            </div>
                                        </td>
                                        <td class="px-4 py-3">
                                            <span x-show="result.expire_date" class="text-gray-300 text-sm" x-text="formatDate(result.expire_date)"></span>
                                            <span x-show="!result.expire_date" class="text-gray-500 text-sm">--</span>
                                        </td>
                                        <td class="px-4 py-3">
                                            <span x-show="result.sender_name" class="text-gray-300 text-sm" x-text="result.sender_name"></span>
                                            <span x-show="result.sender && !result.sender_name" class="text-gray-300 text-sm" x-text="result.sender"></span>
                                            <span x-show="!result.sender_name && !result.sender" class="text-gray-500 text-sm">--</span>
                                        </td>
                                        <td class="px-4 py-3">
                                            <div class="flex space-x-1">
                                                <button 
                                                    @click="viewDetails(result)"
                                                    class="text-blue-400 hover:text-blue-300 p-1"
                                                    title="查看详情">
                                                    <i class="fas fa-eye text-xs"></i>
                                                </button>
                                                <button 
                                                    @click="reanalyze(result)"
                                                    class="text-yellow-400 hover:text-yellow-300 p-1"
                                                    title="重新分析">
                                                    <i class="fas fa-redo text-xs"></i>
                                                </button>
                                                <button 
                                                    @click="removeResult(result)"
                                                    class="text-red-400 hover:text-red-300 p-1"
                                                    title="删除结果">
                                                    <i class="fas fa-trash text-xs"></i>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 分页 -->
                <div x-show="totalPages > 1" class="bg-white bg-opacity-5 px-6 py-3 flex justify-between items-center">
                    <div class="text-sm text-gray-300">
                        第 <span x-text="currentPage"></span> 页，共 <span x-text="totalPages"></span> 页
                    </div>
                    <div class="flex space-x-2">
                        <button 
                            @click="currentPage = Math.max(1, currentPage - 1)"
                            :disabled="currentPage === 1"
                            class="px-3 py-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white rounded text-sm">
                            上一页
                        </button>
                        <template x-for="page in visiblePages" :key="page">
                            <button 
                                @click="currentPage = page"
                                :class="page === currentPage ? 'bg-blue-600' : 'bg-blue-500 hover:bg-blue-600'"
                                class="px-3 py-1 text-white rounded text-sm"
                                x-text="page">
                            </button>
                        </template>
                        <button 
                            @click="currentPage = Math.min(totalPages, currentPage + 1)"
                            :disabled="currentPage === totalPages"
                            class="px-3 py-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white rounded text-sm">
                            下一页
                        </button>
                    </div>
                </div>
            </div>

            <!-- 空状态 -->
            <div x-show="totalResults === 0" class="glass-effect rounded-xl p-12 text-center">
                <i class="fas fa-inbox text-6xl text-gray-500 mb-4"></i>
                <h3 class="text-xl font-semibold text-white mb-2">暂无分析结果</h3>
                <p class="text-gray-400 mb-6">开始分析链接来查看结果</p>
                <button 
                    @click="$parent.setActivePage('analyzer')"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg">
                    <i class="fas fa-search mr-2"></i>
                    前往分析器
                </button>
            </div>
        </div>

        <!-- 详情弹窗 -->
        <div x-show="showDetailModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.away="showDetailModal = false">
            <div class="glass-effect rounded-xl p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-semibold text-white">
                        <i class="fas fa-info-circle mr-2 text-blue-400"></i>
                        详细信息
                    </h3>
                    <button @click="showDetailModal = false" class="text-gray-400 hover:text-white">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div x-show="selectedDetail" class="space-y-3 text-sm">
                    <template x-for="[key, value] in Object.entries(selectedDetail || {})" :key="key">
                        <div class="flex justify-between py-2 border-b border-white border-opacity-10">
                            <span class="text-gray-300 font-medium" x-text="formatFieldName(key)"></span>
                            <span class="text-white text-right max-w-xs truncate" x-text="formatFieldValue(value)"></span>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    `;
}

// 结果页面数据管理
function resultsData() {
    return {
        // 搜索和过滤
        searchQuery: '',
        statusFilter: 'all',
        sortBy: 'time_desc',
        
        // 选择状态
        selectedResults: [],
        
        // 分页
        currentPage: 1,
        pageSize: 50,
        
        // 弹窗
        showDetailModal: false,
        selectedDetail: null,

        // 初始化
        init() {
            this.applyFilters();
        },

        // 计算属性
        get totalResults() {
            return this.$parent.results.length;
        },

        get availableCount() {
            return this.$parent.results.filter(r => r.gift_status === 'available').length;
        },

        get vipCount() {
            return this.$parent.results.filter(r => r.is_vip_link).length;
        },

        get stats() {
            const results = this.$parent.results;
            
            const available = results.filter(r => r.gift_status === 'available');
            const expired = results.filter(r => r.gift_status === 'expired');
            const claimed = results.filter(r => r.gift_status === 'claimed');
            const vip = results.filter(r => r.is_vip_link);
            const invalid = results.filter(r => r.gift_status === 'invalid');
            
            return {
                available: available.length,
                expired: expired.length,
                claimed: claimed.length,
                vip: vip.length,
                invalid: invalid.length,
                validVip: vip.filter(r => r.vip_status === 'valid').length,
                availableValue: available.reduce((sum, r) => sum + (r.gift_price || 0), 0),
                expiredValue: expired.reduce((sum, r) => sum + (r.gift_price || 0), 0),
                claimedValue: claimed.reduce((sum, r) => sum + (r.gift_price || 0), 0),
                successRate: results.length > 0 ? (results.filter(r => r.status === 'success').length / results.length) * 100 : 0
            };
        },

        get filteredResults() {
            let results = [...this.$parent.results];

            // 搜索过滤
            if (this.searchQuery.trim()) {
                const query = this.searchQuery.toLowerCase();
                results = results.filter(r => 
                    (r.short_url && r.short_url.toLowerCase().includes(query)) ||
                    (r.gift_type && r.gift_type.toLowerCase().includes(query)) ||
                    (r.sender_name && r.sender_name.toLowerCase().includes(query))
                );
            }

            // 状态过滤
            if (this.statusFilter !== 'all') {
                if (this.statusFilter === 'vip') {
                    results = results.filter(r => r.is_vip_link);
                } else {
                    results = results.filter(r => r.gift_status === this.statusFilter);
                }
            }

            // 排序
            switch (this.sortBy) {
                case 'time_desc':
                    results.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
                    break;
                case 'time_asc':
                    results.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
                    break;
                case 'value_desc':
                    results.sort((a, b) => (b.gift_price || 0) - (a.gift_price || 0));
                    break;
                case 'value_asc':
                    results.sort((a, b) => (a.gift_price || 0) - (b.gift_price || 0));
                    break;
                case 'status':
                    const statusOrder = { 'available': 0, 'expired': 1, 'claimed': 2, 'invalid': 3 };
                    results.sort((a, b) => (statusOrder[a.gift_status] || 4) - (statusOrder[b.gift_status] || 4));
                    break;
            }

            return results;
        },

        get totalPages() {
            return Math.ceil(this.filteredResults.length / this.pageSize);
        },

        get paginatedResults() {
            const start = (this.currentPage - 1) * this.pageSize;
            const end = start + this.pageSize;
            return this.filteredResults.slice(start, end);
        },

        get visiblePages() {
            const total = this.totalPages;
            const current = this.currentPage;
            const delta = 2;
            
            let pages = [];
            for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
                pages.push(i);
            }
            
            return pages;
        },

        get isAllSelected() {
            return this.paginatedResults.length > 0 && 
                   this.paginatedResults.every(r => this.selectedResults.includes(r.short_url));
        },

        // 方法
        applyFilters() {
            this.currentPage = 1; // 重置到第一页
        },

        refreshResults() {
            // 重新加载数据
            this.$parent.loadData();
            this.selectedResults = [];
            Utils.showToast('结果已刷新', 'success');
        },

        async exportAllResults() {
            const data = this.$parent.results.map(r => r.short_url).join('\n');
            const filename = `全部分析结果_${new Date().toISOString().slice(0, 10)}.txt`;
            Utils.downloadFile(data, filename);
            Utils.showToast(`已导出 ${this.$parent.results.length} 个结果`, 'success');
        },

        async clearAllResults() {
            if (confirm('确定要清空所有分析结果吗？此操作不可恢复。')) {
                this.$parent.clearAllData();
                this.selectedResults = [];
                Utils.showToast('已清空所有数据', 'warning');
            }
        },

        selectAll() {
            this.selectedResults = this.paginatedResults.map(r => r.short_url);
        },

        selectNone() {
            this.selectedResults = [];
        },

        toggleSelectAll() {
            if (this.isAllSelected) {
                this.selectNone();
            } else {
                this.selectAll();
            }
        },

        async exportSelected() {
            if (this.selectedResults.length === 0) return;
            
            const selectedData = this.$parent.results
                .filter(r => this.selectedResults.includes(r.short_url))
                .map(r => r.short_url)
                .join('\n');
                
            const filename = `选中结果_${new Date().toISOString().slice(0, 10)}.txt`;
            Utils.downloadFile(selectedData, filename);
            Utils.showToast(`已导出 ${this.selectedResults.length} 个选中结果`, 'success');
        },

        async copyToClipboard(text) {
            await Utils.copyToClipboard(text);
        },

        viewDetails(result) {
            this.selectedDetail = result;
            this.showDetailModal = true;
        },

        async reanalyze(result) {
            Utils.showToast('重新分析功能开发中...', 'info');
            // TODO: 实现重新分析单个链接的功能
        },

        removeResult(result) {
            if (confirm('确定要删除这个分析结果吗？')) {
                const index = this.$parent.results.findIndex(r => r.short_url === result.short_url);
                if (index !== -1) {
                    this.$parent.results.splice(index, 1);
                    this.$parent.saveData();
                    
                    // 从选中列表中移除
                    const selectedIndex = this.selectedResults.indexOf(result.short_url);
                    if (selectedIndex !== -1) {
                        this.selectedResults.splice(selectedIndex, 1);
                    }
                    
                    Utils.showToast('已删除分析结果', 'success');
                }
            }
        },

        getStatusText(result) {
            if (result.is_vip_link) {
                return result.vip_status === 'valid' ? 'VIP有效' : 'VIP过期';
            }
            
            const statusMap = {
                'available': '可用',
                'expired': '过期',
                'claimed': '已领取',
                'invalid': '无效'
            };
            return statusMap[result.gift_status] || '未知';
        },

        formatDate(dateString) {
            if (!dateString) return '--';
            try {
                // 处理不同的日期格式
                let date;
                if (typeof dateString === 'number') {
                    date = new Date(dateString);
                } else if (dateString.includes('北京时间')) {
                    // 移除 "(北京时间)" 后缀
                    const cleanDate = dateString.replace(/\s*\(北京时间\)\s*$/, '');
                    date = new Date(cleanDate);
                } else {
                    date = new Date(dateString);
                }
                
                if (isNaN(date.getTime())) {
                    return dateString; // 如果无法解析，返回原始字符串
                }
                
                return date.toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (error) {
                return dateString;
            }
        },

        formatFieldName(key) {
            const fieldNames = {
                'short_url': '链接',
                'gift_type': '礼品类型',
                'gift_price': '价值',
                'gift_status': '状态',
                'status_text': '状态描述',
                'sender_name': '发送者',
                'expire_date': '过期时间',
                'total_count': '总数量',
                'available_count': '可用数量',
                'used_count': '已使用数量',
                'is_vip_link': 'VIP链接',
                'vip_status': 'VIP状态',
                'remaining_days': '剩余天数',
                'timestamp': '分析时间',
                'status': '分析状态',
                'redirect_url': '重定向链接'
            };
            return fieldNames[key] || key;
        },

        formatFieldValue(value) {
            if (value === null || value === undefined) return '--';
            if (typeof value === 'boolean') return value ? '是' : '否';
            if (typeof value === 'number' && value > 1000000000000) {
                // 时间戳格式化
                return new Date(value).toLocaleString('zh-CN');
            }
            if (typeof value === 'object') return JSON.stringify(value);
            return String(value);
        }
    }
}