const ResultsApp = {
    delimiters: ['${', '}'],
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            prs_score: null,       // 初始化为null
            prs_risk: null,        // 初始化为null
            mergedData: [],        // 初始化为空数组
            taskId: null,
            progress: 0,
            task_status: 'pending', // 明确初始状态
            error_message: null
        }
    },
    computed: {
        loadingStatusText() {
            const statusMap = {
                pending: '正在初始化任务...',
                queued: '排队中，当前队列位置：' + this.queuePosition,
                parsing: `分析中（${this.progress}%）`,
                validating: '正在验证数据...'
            }
            return statusMap[this.task_status] || '请稍候...'
        },

        riskBadgeClass() {
            return {
                'bg-success': this.prsRisk === '低风险',
                'bg-warning': this.prsRisk === '中等风险',
                'bg-danger': this.prsRisk === '高风险',
                'badge': true
            }
        },
        totalPages() {
            return Math.ceil(this.mergedData.length / this.pageSize)
        },
        paginatedData() {
            const start = (this.currentPage - 1) * this.pageSize
            return this.mergedData.slice(start, start + Number(this.pageSize))
        }
    },
    methods: {
        pollTaskStatus() {
            const vm = this
            function checkStatus() {
                fetch(`/status/${vm.taskId}`)
                    .then(res => {
                        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
                        return res.json()
                    })
                    .then(data => {
                        console.log('[DEBUG] 状态更新:', data)
                        vm.$set(vm, 'task_status', data.status)
                        vm.$set(vm, 'progress', data.progress)

                        if (data.status === 'completed') {
                            vm.initData(data.result)
                        } else if (data.status === 'failed') {
                            vm.$set(vm, 'error_message', data.error_message)
                        } else {
                            setTimeout(checkStatus, 2500)
                        }
                    })
                    .catch(err => {
                        console.error('轮询失败:', err)
                        setTimeout(checkStatus, 5000)
                    })
            }
            checkStatus()
        },

        initData(resultData) {
            if (!resultData?.variants?.length) {
                this.error_message = '无有效分析数据';
                return;
            }
            
            console.log('[DEBUG] 初始化数据:', resultData)
            if (!resultData) return

            // 使用Vue.set确保响应式更新
            this.$set(this, 'prs_score', resultData.summary?.prs_score ?? 'N/A')
            this.$set(this, 'prs_risk', resultData.summary?.prs_risk ?? '未评估')

            // 处理嵌套数据结构
            this.mergedData = (resultData.variants || []).map((variant, index) => ({
                variant: variant.variant_info || {},
                clinvar: (resultData.summary?.clinvar_data || [])[index] || {}
            }))

            this.$nextTick(() => {
                try {
                    this.renderCharts(resultData)
                    document.getElementById('loadingMessage').classList.add('d-none')
                    document.getElementById('resultsContent').classList.remove('d-none')
                } catch (e) {
                    console.error('图表渲染失败:', e)
                }
            })
        },

        renderCharts(resultData) {
            // ClinVar临床意义分布图
            if (resultData.summary?.clinvar_data?.length) {
                this.renderClinvarChart(resultData.summary.clinvar_data)
            }

            // PRS风险分布图
            if (resultData.summary?.prs_risk) {
                this.renderPRSDistribution(resultData.summary.prs_risk)
            }
        },

        renderClinvarChart(clinvarData) {
            const container = document.getElementById('clinvarChart')
            if (!container || !clinvarData.length) {
                container.innerHTML = '<div class="alert alert-secondary">无可用ClinVar数据</div>'
                return
            }

            // 数据统计
            const significanceCount = clinvarData.reduce((acc, cur) => {
                const key = cur?.ClinicalSignificance || 'Unknown'
                acc[key] = (acc[key] || 0) + 1
                return acc
            }, {})

            // 图表配置
            const data = [{
                values: Object.values(significanceCount),
                labels: Object.keys(significanceCount),
                type: 'pie',
                hole: 0.4,
                marker: {
                    colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                }
            }]

            const layout = {
                title: 'ClinVar临床意义分布',
                height: 300,
                margin: { t: 40, b: 20 }
            }
            Plotly.newPlot('clinvarChart', data, layout)
        },

        renderPRSDistribution(riskLevel) {
            // 使用实际数据替代模拟数据
            const data = [{
                x: ['低风险', '中等风险', '高风险'],
                y: [
                    resultData.summary.risk_distribution?.low || 0,
                    resultData.summary.risk_distribution?.medium || 0,
                    resultData.summary.risk_distribution?.high || 0
                ],
                type: 'bar',
                marker: {
                    color: ['#2ca02c', '#ff7f0e', '#d62728']
                }
            }]

            const layout = {
                title: 'PRS风险分布对比',
                xaxis: { title: '风险等级' },
                yaxis: { title: '百分比 (%)' },
                height: 300
            }
            Plotly.newPlot('prsDistribution', data, layout)
        }
    },
    mounted() {
        this.taskId = new URLSearchParams(window.location.search).get('task_id')
        if (this.taskId) {
            this.pollTaskStatus()
        } else {
            this.$set(this, 'error_message', '无效的任务ID')
        }
    }
}

// 初始化Vue
document.addEventListener('DOMContentLoaded', () => {
    new Vue(ResultsApp).$mount('#app')
})