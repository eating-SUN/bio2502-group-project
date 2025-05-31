<template>
  <div>
    <NavBar :showReupload="true" />
    
    <!-- 结果展示区 -->
    <div class="container mt-4" v-cloak>
      <div class="card">
        <div class="card-header bg-success text-white">
          <h3 class="mb-0">分析结果</h3>
        </div>
        <div class="card-body">
          <!-- 错误提示 -->
          <div v-if="taskStatus === 'failed'" class="alert alert-danger">
            {{ errorMessage }}
          </div>

          <!-- 加载状态 -->
          <template v-if="taskStatus === 'pending'">
            <div class="text-center py-5">
              <div class="spinner-border text-primary"></div>
              <p class="mt-2">{{ loadingStatusText }}</p>
              <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     :style="{ width: progress + '%' }">
                </div>
              </div>
              <p class="mt-2">当前进度: {{ progress }}%</p>
            </div>
          </template>

          <!-- 完成状态 -->
          <template v-else-if="taskStatus === 'completed'">
            <!-- PRS评分 -->
            <div class="mb-4">
              <h4>PRS评分: 
                <span class="text-primary">{{ prsScore }}</span>
                <span class="badge" :class="riskBadgeClass">{{ prsRisk }}</span>
              </h4>
              <p class="text-muted">基于 {{ mergedData.length }} 个变异计算</p>
            </div>

            <!-- 分页控制 -->
            <div class="row mb-3" v-if="mergedData.length > 0">
              <div class="col-md-6">
                <div class="input-group">
                  <span class="input-group-text">每页显示</span>
                  <select class="form-select" v-model="pageSize">
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="20">20</option>
                  </select>
                </div>
              </div>
              <div class="col-md-6">
                <nav aria-label="Page navigation">
                  <ul class="pagination justify-content-end">
                    <li class="page-item" :class="{disabled: currentPage === 1}">
                      <button class="page-link" @click="currentPage = Math.max(1, currentPage - 1)">&laquo;</button>
                    </li>
                    <li class="page-item" 
                        v-for="page in visiblePages" 
                        :key="page"
                        :class="{active: currentPage === page}">
                      <button class="page-link" @click="currentPage = page">{{ page }}</button>
                    </li>
                    <li class="page-item" :class="{disabled: currentPage === totalPages}">
                      <button class="page-link" @click="currentPage = Math.min(totalPages, currentPage + 1)">&raquo;</button>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>

            <div v-if="taskStatus === 'completed' && mergedData.length === 0">
              <div class="alert alert-info">
                未检测到有效变异
              </div>
            </div>
            <!-- 变异表格 -->
            <div class="table-responsive">
              <table class="table table-striped">
                <thead>
                  <tr>
                    <th>变异ID</th>
                    <th>染色体</th>
                    <th>位置</th>
                    <th>参考序列</th>
                    <th>变异序列</th>
                    <th>基因型</th>
                    <th>临床意义</th>
                    <th>基因</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in paginatedData" :key="index">
                    <td>{{ item.variant_info.id || 'N/A' }}</td>
                    <td>{{ item.variant_info.chrom || 'chrN/A' }}</td>
                    <td>{{ item.variant_info.pos || '-' }}</td>
                    <td class="text-monospace">{{ item.variant_info.ref || '-' }}</td>
                    <td class="text-monospace text-danger">{{ item.variant_info.alt || '-' }}</td>
                    <td class="text-monospace">{{ item.variant_info.genotype || '-' }}</td>
                    <td>
                      <span class="badge" :class="getClinicalClass(item.clinvar_data?.clinvar?.ClinicalSignificance)">
                        {{ item.clinvar_data?.clinvar?.ClinicalSignificance || '未知' }}
                      </span>
                    </td>
                    <td>{{ item.clinvar_data?.clinvar?.Gene || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- 蛋白质变异信息展示区域 -->
            <div v-if="hasProteinVariants" class="mt-4">
              <div class="card">
                <div class="card-header bg-info text-white">
                  <h4>蛋白质变异信息</h4>
                </div>
                <div class="card-body">
                  <div v-for="(item, index) in proteinVariants" :key="index" class="mb-4">
                    <h5>变异ID: {{ item.variant_info.id }}</h5>
                    
                    <div class="row">
                      <div class="col-md-4">
                        <p><strong>蛋白质ID:</strong> 
                          <a :href="`https://www.uniprot.org/uniprot/${item.protein_info.protein_id}`" target="_blank">
                            {{ item.protein_info.protein_id }}
                          </a>
                        </p>
                        <p><strong>HGVS.p:</strong> {{ item.protein_info.hgvs_p }}</p>
                        <p v-if="item.protein_info.mut_pos">
                          <strong>突变位置:</strong> {{ item.protein_info.mut_pos }}
                        </p>
                      </div>
                      
                      <div class="col-md-8">
                        <div class="sequence-box">
                          <div class="sequence-header">
                            <span>野生型序列:</span>
                          </div>
                          <pre class="sequence">{{ item.protein_info.wt_seq_local }}</pre>
                          <div v-if="item.protein_info.mut_pos_offset >= 0" 
                               class="sequence-pointer" 
                               :style="{ left: item.protein_info.mut_pos_offset + 'ch' }">
                            ↑
                          </div>
                        </div>
                        
                        <div class="sequence-box mt-2">
                          <div class="sequence-header">
                            <span>突变型序列:</span>
                          </div>
                          <pre class="sequence text-danger">{{ item.protein_info.mut_seq_local }}</pre>
                          <div v-if="item.protein_info.mut_pos_offset >= 0" 
                               class="sequence-pointer text-danger" 
                               :style="{ left: item.protein_info.mut_pos_offset + 'ch' }">
                            ↑
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 蛋白质特征变化 -->
                    <div v-if="item.protein_features" class="mt-3">
                      <h6>蛋白质特征变化:</h6>
                      <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                          分子量变化
                          <span :class="getChangeClass(item.protein_features.molecular_weight_change)">
                            {{ formatChange(item.protein_features.molecular_weight_change) }}
                          </span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                          芳香性变化
                          <span :class="getChangeClass(item.protein_features.aromaticity_change)">
                            {{ formatChange(item.protein_features.aromaticity_change) }}
                          </span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                          不稳定指数变化
                          <span :class="getChangeClass(item.protein_features.instability_index_change)">
                            {{ formatChange(item.protein_features.instability_index_change) }}
                          </span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                          疏水性变化
                          <span :class="getChangeClass(item.protein_features.gravy_change)">
                            {{ formatChange(item.protein_features.gravy_change) }}
                          </span>
                        </li>
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                          等电点变化
                          <span :class="getChangeClass(item.protein_features.isoelectric_point_change)">
                            {{ formatChange(item.protein_features.isoelectric_point_change) }}
                          </span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 图表容器 -->
            <div class="row mt-4">
              <div class="col-md-6">
                <clinvar-chart :chartData="clinvarChartData" />
              </div>
              <div class="col-md-6">
                <prs-distribution-chart :chartData="prsDistributionChartData" />
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- PDF下载按钮 -->
    <div class="container mt-4 text-center" v-if="taskStatus === 'completed'">
      <button @click="downloadReport" class="btn btn-warning btn-lg">
        <i class="bi bi-download me-2"></i>生成PDF报告
      </button>
    </div>
    
    <Footer />
  </div>
</template>

<script>
import NavBar from '@components/NavBar.vue'
import Footer from '@components/Footer.vue'
import ClinvarChart from '@components/ClinvarChart.vue'
import PrsDistributionChart from '@components/PrsDistributionChart.vue'
import axios from 'axios';
import { getTaskStatus, getResults } from '@services/api'

export default {
  components: {
    NavBar,
    Footer,
    ClinvarChart,
    PrsDistributionChart
  },
  data() {
    return {
      taskStatus: 'pending',
      errorMessage: '',
      loadingStatusText: '正在处理...',
      progress: 0,
      prsScore: 0,
      prsRisk: '未评估',
      riskBadgeClass: 'bg-secondary',
      mergedData: [],
      currentPage: 1,
      pageSize: 10
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.mergedData.length / this.pageSize)
    },
    visiblePages() {
      const pages = []
      const start = Math.max(1, this.currentPage - 2)
      const end = Math.min(this.totalPages, this.currentPage + 2)
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.mergedData.slice(start, end)
    },
    clinvarChartData() {
      // 统计临床意义分布
      const significanceCount = {
        'Pathogenic': 0,
        'Likely pathogenic': 0,
        'Uncertain significance': 0,
        'Likely benign': 0,
        'Benign': 0,
        'Unknown': 0
      }
      
      this.mergedData.forEach(item => {
        const significance = item.clinvar_data?.clinvar?.ClinicalSignificance || 'Unknown'
        if (significance in significanceCount) {
          significanceCount[significance]++
        } else {
          significanceCount['Unknown']++
        }
      })
      
      return {
        labels: Object.keys(significanceCount),
        datasets: [{
          label: '临床意义分布',
          data: Object.values(significanceCount),
          backgroundColor: [
            '#e74c3c', // Pathogenic
            '#f39c12', // Likely pathogenic
            '#3498db', // Uncertain significance
            '#2ecc71', // Likely benign
            '#27ae60', // Benign
            '#95a5a6'  // Unknown
          ]
        }]
      }
    },
    // 提取含有蛋白变异的条目
    proteinVariants() {
      return this.mergedData.filter(item => item.protein_info);
    },
    
    // 检查是否存在蛋白变异
    hasProteinVariants() {
      return this.proteinVariants.length > 0;
    },
    prsDistributionChartData() {
      // 按染色体分组统计变异数量
      const chromosomeCounts = {}
      
      this.mergedData.forEach(item => {
        const chrom = item.variant_info?.chrom || 'Unknown'
        if (!chromosomeCounts[chrom]) {
          chromosomeCounts[chrom] = 0
        }
        chromosomeCounts[chrom]++
      })
      
      return {
        labels: Object.keys(chromosomeCounts),
        datasets: [{
          label: '染色体变异分布',
          data: Object.values(chromosomeCounts),
          backgroundColor: '#3498db'
        }]
      }
    }
  },
  created() {
    this.fetchResults()
  },
  methods: {
    async fetchResults() {
      const taskId = this.$route.query.task_id
      if (!taskId) {
        this.taskStatus = 'invalid'
        this.errorMessage = '无效的任务ID'
        return
      }
      
      try {
        const statusResponse = await getTaskStatus(taskId);
        this.taskStatus = statusResponse.data.status
        this.progress = statusResponse.data.progress || 0
        
        if (this.taskStatus === 'pending') {
          this.pollTaskStatus(taskId)
        } else if (this.taskStatus === 'completed') {
          await this.fetchTaskResults(taskId)
        } else if (this.taskStatus === 'failed') {
          this.errorMessage = statusResponse.data.error_message || '任务处理失败'
        }
      } catch (error) {
        console.error('获取任务状态失败:', error)
        this.taskStatus = 'failed'
        this.errorMessage = '获取任务状态失败'
      }
    },
    pollTaskStatus(taskId) {
      const interval = setInterval(async () => {
        try {
          const response = await getTaskStatus(taskId)
          this.taskStatus = response.data.status
          this.progress = response.data.progress || 0
          this.loadingStatusText = this.getLoadingStatusText(response.data.status)
          
          if (this.taskStatus === 'completed') {
            clearInterval(interval)
            await this.fetchTaskResults(taskId)
          } else if (this.taskStatus === 'failed') {
            clearInterval(interval)
            this.errorMessage = response.data.error_message || '任务处理失败'
          }
        } catch (error) {
          console.error('轮询任务状态失败:', error)
          clearInterval(interval)
          this.taskStatus = 'failed'
          this.errorMessage = '获取任务状态失败'
        }
      }, 3000)
    },
    async fetchTaskResults(taskId) {
      try {
        const response = await getResults(taskId)
        this.prsScore = response.data.prsScore
        this.prsRisk = response.data.prsRisk
        this.mergedData = response.data.variants || []

        // 处理蛋白质数据
        this.processProteinData()

        // 设置风险等级徽章样式
        if (this.prsRisk.includes('低')) {
          this.riskBadgeClass = 'bg-success'
        } else if (this.prsRisk.includes('中等')) {
          this.riskBadgeClass = 'bg-warning'
        } else if (this.prsRisk.includes('高')) {
          this.riskBadgeClass = 'bg-danger'
        } else {
          this.riskBadgeClass = 'bg-secondary'
        }
        
        this.taskStatus = 'completed'
      } catch (error) {
        console.error('获取任务结果失败:', error)
        this.taskStatus = 'failed'
        this.errorMessage = '获取任务结果失败'
      }
    },
    getClinicalClass(significance) {
      if (!significance) return 'bg-secondary'
      
      if (significance.includes('Pathogenic')) {
        return 'bg-danger'
      } else if (significance.includes('Likely pathogenic')) {
        return 'bg-warning'
      } else if (significance.includes('Uncertain significance')) {
        return 'bg-info'
      } else if (significance.includes('Likely benign')) {
        return 'bg-success'
      } else if (significance.includes('Benign')) {
        return 'bg-success'
      }
      return 'bg-secondary'
    },
    getChangeClass(value) {
      if (value > 0) return 'text-danger'
      if (value < 0) return 'text-success'
      return ''
    },
    formatChange(value) {
      if (value === null || value === undefined) return 'N/A'
      return value > 0 ? `+${value}` : value
    },
    getLoadingStatusText(status) {
      const statusMap = {
        queued: '任务排队中...',
        processing: '处理文件中...',
        analyzing: '分析数据中...',
        annotating: '注释变异中...',
        scoring: '计算风险评分...',
        generating: '生成报告...'
      }
      
      return statusMap[status] || '正在处理...'
    },
    downloadReport() {
      const taskId = this.$route.query.task_id
      if (!taskId) {
        alert('无法生成报告：缺少任务ID')
        return
      }
      
      alert('PDF报告生成功能将在后端实现')
    },
    processProteinData() {
      this.mergedData.forEach(item => {
        if (item.protein_info) {
          // 解析突变位置（从HGVS.p格式中提取）
          const hgvsMatch = item.protein_info.hgvs_p?.match(/\.(\d+)/);
          const mut_pos = hgvsMatch ? parseInt(hgvsMatch[1]) : -1;
          
          // 计算序列显示范围（突变位置前后各15个氨基酸）
          const start = Math.max(0, mut_pos - 15);
          const end = Math.min(item.protein_info.wt_seq.length, mut_pos + 15);
          
          // 计算突变位置在显示序列中的偏移量
          const mut_pos_offset = mut_pos > 0 ? mut_pos - start - 1 : -1;
          
          item.protein_info = {
            ...item.protein_info,
            wt_seq_local: this.formatSequence(item.protein_info.wt_seq.substring(start, end)), 
            mut_seq_local: this.formatSequence(item.protein_info.mut_seq.substring(start, end)),
            mut_pos: mut_pos,
            mut_pos_offset: mut_pos_offset
          };
        }
      });
    },
    // 格式化序列显示（每10个字符加空格）
    formatSequence(seq) {
      return seq.replace(/(.{10})/g, '$1 ');
    }
  }
}
</script>

<style scoped>
.card {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  border: none;
  margin-bottom: 1.5rem;
}

.card-header {
  font-weight: bold;
}

.progress {
  height: 20px;
  margin-top: 10px;
}

.table th {
  background-color: #f8f9fa;
}

.text-monospace {
  font-family: monospace;
}

.badge {
  padding: 0.5em 0.75em;
  font-size: 0.9em;
  margin-left: 0.5em;
}

.bg-danger {
  background-color: #e74c3c !important;
}

.bg-warning {
  background-color: #f39c12 !important;
}

.bg-info {
  background-color: #3498db !important;
}

.bg-success {
  background-color: #2ecc71 !important;
}

.bg-secondary {
  background-color: #95a5a6 !important;
}

[v-cloak] {
  display: none;
}

.sequence-box {
  position: relative;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px;
  background-color: #f8f9fa;
  overflow-x: auto;
}

.sequence-header {
  margin-bottom: 5px;
  font-weight: bold;
}

.sequence {
  font-family: monospace;
  font-size: 1.1rem;
  letter-spacing: 1px;
  margin-bottom: 0;
  white-space: pre-wrap;
  line-height: 1.5;
}

.sequence-pointer {
  position: absolute;
  bottom: -20px;
  transform: translateX(-50%);
  font-weight: bold;
  font-size: 1.2rem;
}

.list-group-item {
  padding: 0.75rem 1.25rem;
}
</style>