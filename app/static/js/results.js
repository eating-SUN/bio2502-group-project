
const ResultsApp = {
    delimiters: ['${', '}'],
    data() {
        return {
            currentPage: 1,
            pageSize: 10,
            mergedData: [],
            prsScore: 'N/A',
            prsRisk: '未评估'
        }
    },
    computed: {
        riskBadgeClass() {
            return {
                'bg-success': this.prsRisk === '低风险',
                'bg-warning': this.prsRisk === '中等风险',
                'bg-danger': this.prsRisk === '高风险',
                'badge': true
            }
        },
        totalPages() {
            return Math.ceil(this.mergedData.length / this.pageSize);
        },
        paginatedData() {
            const start = (this.currentPage - 1) * this.pageSize;
            return this.mergedData.slice(start, start + Number(this.pageSize));
        }
    },
    methods: {
        initData(resultData) {
            this.prsScore = resultData.summary?.prs_score || 'N/A';
            this.prsRisk = resultData.summary?.prs_risk || '未评估';
            
            // 合并数据逻辑
            this.mergedData = (resultData.variants || []).map((variant, index) => ({
                variant: variant.variant_info || {},
                clinvar: (resultData.summary?.clinvar_data || [])[index] || {}
            }));

            // 渲染图表
            this.$nextTick(() => {
                renderCharts(resultData);
            });
        }
    }
};

function renderStoredResults() {
    const rawData = sessionStorage.getItem('vcfResults');
    if (!rawData) return handleMissingResults();
    
    try {
        const resultData = JSON.parse(rawData);
        showResults(resultData);
    } catch (e) {
        showError('结果数据解析失败');
    }
}
// 监听DOM加载完成事件，渲染存储的结果
document.addEventListener('DOMContentLoaded', renderStoredResults);

function showResults(resultData) {
    const app = new Vue(ResultsApp).$mount('#app');
    app.initData(resultData);
    // 解析关键数据

    const clinvarData = resultData.summary?.clinvar_data || [];
    const variants = resultData.variants || [];

    // 构建ClinVar数据展示
    const clinvarSection = document.getElementById('clinvarSection');
    clinvarSection.innerHTML = '';

    clinvarData.forEach((item, index) => {
        if (!item) return;
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-header bg-light">
                <span class="badge bg-info">#${index + 1}</span>
                ${item.ClinicalSignificance || '未知临床意义'}
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <strong>参考编号：</strong> ${item.ReviewStatus || '-'}
                    </div>
                    <div class="col-md-8">
                        <strong>相关表型：</strong> ${item.PhenotypeList?.join(', ') || '-'}
                    </div>
                </div>
            </div>
        `;
        clinvarSection.appendChild(card);
    });

    // 构建变体表格
    const tbody = document.getElementById('variantTableBody');
  tbody.innerHTML = variants.length > 0 ? 
    variants.map(variant => `
      <tr>
        <td>${variant.variant_info?.Chromosome || 'chrN/A'}</td>
        <td>${variant.variant_info?.Start || '-'}</td>
        <td class="text-monospace">${variant.variant_info?.Reference || '-'}</td>
        <td class="text-monospace text-danger">${variant.variant_info?.Alternate || '-'}</td>
      </tr>
    `).join('') : 
    `<tr><td colspan="4" class="text-center">未检测到有效变异</td></tr>`;
    // 图表渲染
    app.$nextTick(() => {
    renderCharts(resultData);
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';
  });
    // 显示结果容器
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';
}

function handleMissingResults() {
    const loadingMessage = document.getElementById('loadingMessage');
    loadingMessage.innerHTML = `
        <div class="alert alert-danger">
            未找到分析结果，请<a href="/upload">重新上传</a>
        </div>
    `;
}

// 错误处理函数
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.classList.remove('d-none');
    
    setTimeout(() => {
        errorElement.classList.add('fade-out');
        setTimeout(() => {
            errorElement.classList.remove('fade-out', 'd-none');
        }, 500);
    }, 3000);
}

// 在results.js中添加图表渲染函数
function renderCharts(resultData) {
    // ClinVar临床意义分布图
    renderClinvarChart(resultData.summary?.clinvar_data);
    
    // PRS风险分布图
    renderPRSDistribution(resultData.summary?.prs_risk);
}

function renderClinvarChart(clinvarData) {
    if (!clinvarData || clinvarData.length === 0) return;

    // 数据统计
    const significanceCount = clinvarData.reduce((acc, cur) => {
        const key = cur?.ClinicalSignificance || 'Unknown';
        acc[key] = (acc[key] || 0) + 1;
        return acc;
    }, {});

    // 图表配置
    const data = [{
        values: Object.values(significanceCount),
        labels: Object.keys(significanceCount),
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        }
    }];

    const layout = {
        title: 'ClinVar临床意义分布',
        height: 300,
        margin: { t: 40, b: 20 }
    };

    Plotly.newPlot('clinvarChart', data, layout);
}

function renderPRSDistribution(riskLevel) {
    // 模拟风险分布数据
    const data = [{
        x: ['低风险', '中等风险', '高风险'],
        y: [25, 50, 25], // 示例数据
        type: 'bar',
        marker: {
            color: ['#2ca02c', '#ff7f0e', '#d62728']
        }
    }];

    const layout = {
        title: 'PRS风险分布对比',
        xaxis: { title: '风险等级' },
        yaxis: { title: '百分比 (%)' },
        height: 300
    };

    Plotly.newPlot('prsDistribution', data, layout);
}
