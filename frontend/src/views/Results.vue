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
              <h4>乳腺癌PRS评分: 
                <span class="text-primary" data-bs-toggle="tooltip" title="多基因风险评分（Polygenic Risk Score）是一种基于多个遗传变异来评估个体患病风险的方法">{{ prsScore }}</span>
                <span class="badge" :class="riskBadgeClass">{{ prsRisk }}</span>
              </h4>
              <p class="text-muted">基于 {{ mergedData.length }} 个变异计算</p>
            </div>
            <!-- 神经网络风险预测 -->
            <div class="mb-4">
              <h4>神经网络预测乳腺癌风险: 
                <span class="text-primary" data-bs-toggle="tooltip" title="基于机器学习模型对多个变异进行加权评分，预测乳腺癌风险概率">{{ modelScore }}%</span>
                <span class="badge" :class="modelRiskBadgeClass">{{ modelRisk }}</span>
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
                    <th @click="sortBy('id')" class="sortable-header">
                      <div class="d-flex align-items-center">
                        <span>变异ID</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'id' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'id' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
                    <th @click="sortBy('chrom')" class="sortable-header">
                      <div class="d-flex align-items-center">
                        <span>染色体</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'chrom' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'chrom' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
                    <th>位置</th>
                    <th>参考序列</th>
                    <th>变异序列</th>
                    <th>基因型</th>
                    <th @click="sortBy('predict_label')" class="sortable-header">
                      <div class="d-flex align-items-center">
                        <span>模型预测标签</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'predict_label' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'predict_label' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
                    <th @click="sortBy('predict_score')" class="sortable-header">
                      <div class="d-flex align-items-center">
                        <span>模型预测得分</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'predict_score' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'predict_score' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
                    <th @click="sortBy('ClinicalSignificance')" class="sortable-header" data-bs-toggle="tooltip" title="ClinVar数据库提供的变异临床意义分类">
                      <div class="d-flex align-items-center">
                        <span>临床意义</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'ClinicalSignificance' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'ClinicalSignificance' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
                    <th>相关基因</th>
                    <th>疾病名称</th>
                    <th @click="sortBy('regulome_score')" class="sortable-header" data-bs-toggle="tooltip" title="RegulomeDB评分：评估非编码变异的调控潜力，分数越低表示调控证据越强">
                      <div class="d-flex align-items-center">
                        <span>RegulomeDB分数</span>
                        <span class="sort-indicators ms-1">
                          <i class="bi bi-caret-up-fill" :class="{'text-primary': sortField === 'regulome_score' && sortDirection === 'asc'}"></i>
                          <i class="bi bi-caret-down-fill" :class="{'text-primary': sortField === 'regulome_score' && sortDirection === 'desc'}"></i>
                        </span>
                      </div>
                    </th>
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
                      <span class="badge" :class="getPredictClass(item.predict_result?.clnsig_pred)">
                        {{ item.predict_result?.clnsig_pred || '未评估'}}
                      </span>
                    </td>
                    <td>{{ item.predict_result?.predict_score?.toFixed(4) || '-' }}</td>
                    <td>
                      <span class="badge" :class="getClinicalClass(item.clinvar_data?.ClinicalSignificance)">
                        {{ item.clinvar_data?.ClinicalSignificance || '未评估' }}
                      </span>
                    </td>
                    
                    <td class="text-monospace">{{ item.clinvar_data?.Gene || '-' }}</td>
                    <td class="text-monospace">{{ item.clinvar_data?.ClinvarDiseaseName || '-' }}</td>
                    
                    <td>
                      <span v-if="item.regulome_score && typeof item.regulome_score === 'object'" class="badge" :class="getRegulomeClass(item.regulome_score)">
                        {{ formatRegulomeScore(item.regulome_score) }}
                      </span>
                      <span v-else>
                        N/A
                      </span>
                    </td>
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
                    <p><strong>位置:</strong> {{ item.protein_info.position }}</p>
                    <p><strong>突变类型:</strong> {{ item.protein_info.mutation_type }}</p>
                    <p><strong>氨基酸变化:</strong> 
                      {{ item.protein_info.ref_aa }} → {{ item.protein_info.alt_aa }}
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
              <!-- 分析结果统计 -->            
              <!-- 图表容器 -->
              <div class="row mt-4">
                <div class="col-lg-6 mb-4">
                  <clinvar-chart :chartData="clinvarChartData" />
                </div>
                <div class="col-lg-6 mb-4">
                  <model-prediction-chart :chartData="modelPredictionChartData" />
                </div>
                
                <div class="col-lg-6 mb-4">
                  <prs-distribution-chart :chartData="clinvarDistributionByChromosome" />
                </div>
                <div class="col-lg-6 mb-4">
                  <chromosome-prediction-chart :chartData="chromosomePredictionChartData" />
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

    <!-- PDF下载按钮 -->
    <div class="container mt-4 text-center" v-if="taskStatus === 'completed'">
        <button @click="downloadReport" class="btn btn-warning btn-lg" :disabled="isGeneratingPDF">
          <template v-if="isGeneratingPDF">
            <span class="spinner-border spinner-border-sm"></span>
            生成中...
          </template>
          <template v-else>
            <i class="bi bi-download me-2"></i>生成PDF报告
          </template>
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
import ModelPredictionChart from '@components/ModelPredictionChart.vue'
import ChromosomePredictionChart from '@components/ChromosomePredictionChart.vue'
import axios from 'axios';
import { getTaskStatus, getResults } from '@services/api'

export default {
  components: {
    NavBar,
    Footer,
    ClinvarChart,
    PrsDistributionChart,
    ModelPredictionChart,
    ChromosomePredictionChart
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
      pageSize: 10,
      isGeneratingPDF: false,
      sortField: null,        // 当前排序字段
      sortDirection: 'asc' ,   // 排序方向：asc 或 desc
      modelScore: 0,
      modelRiskLevel: 0,
      modelRiskBadgeClass: 'bg-secondary',
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
    // 排序后的分页数据
    paginatedData() {
      let sortedData = [...this.mergedData];
      
      if (this.sortField) {
        sortedData.sort((a, b) => {
          let valueA, valueB;
          
          // 根据不同的排序字段获取值
          switch (this.sortField) {
            case 'id':
              valueA = a.variant_info.id || '';
              valueB = b.variant_info.id || '';
              break;
            case 'chrom':
              valueA = this.parseChromosome(a.variant_info.chrom || '');
              valueB = this.parseChromosome(b.variant_info.chrom || '');
              break;
            case 'ClinicalSignificance':
              valueA = a.clinvar_data?.ClinicalSignificance || '';
              valueB = b.clinvar_data?.ClinicalSignificance || '';
              break;
            case 'regulome_score':
              // 处理regulome_score对象排序
              valueA = a.regulome_score ? a.regulome_score.ranking : '';
              valueB = b.regulome_score ? b.regulome_score.ranking : '';
              break;
            default:
              valueA = '';
              valueB = '';
          }
          
          // 比较值
          if (valueA < valueB) {
            return this.sortDirection === 'asc' ? -1 : 1;
          }
          if (valueA > valueB) {
            return this.sortDirection === 'asc' ? 1 : -1;
          }
          return 0;
        });
      }
      
      // 分页
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return sortedData.slice(start, end);
    },
clinvarChartData() {
  const clinicalData = this.mergedData.reduce((acc, item) => {
    const significance = item.clinvar_data?.ClinicalSignificance || 'Unknown';
    acc[significance] = (acc[significance] || 0) + 1;
    return acc;
  }, {});

  const labels = Object.keys(clinicalData);
  const data = labels.map(label => clinicalData[label]);
  const backgroundColors = labels.map(label => {
    switch(label) {
      case 'Pathogenic': return '#e74c3c';
      case 'Likely_pathogenic': return '#f39c12';
      case 'Uncertain_significance': return '#3498db';
      case 'Likely_benign': return '#2ecc71';
      case 'Benign': return '#27ae60';
      default: return '#95a5a6';
    }
  });

  return {
    labels,
    datasets: [{
      data,
      backgroundColor: backgroundColors,
      borderWidth: 1
    }]
  };
},
modelPredictionChartData() {
  const predictionCounts = {
    'Benign': 0,
    'Likely_benign': 0,
    'Uncertain_significance': 0,
    'Likely_pathogenic': 0,
    'Pathogenic': 0,
    'Unknown': 0
  };

  this.mergedData.forEach(item => {
    const prediction = item.predict_result?.clnsig_pred || 'Unknown';
    predictionCounts[prediction]++;
  });

  const labels = Object.keys(predictionCounts);
  const data = labels.map(label => predictionCounts[label]);
  const backgroundColors = labels.map(label => {
    switch(label) {
      case 'Pathogenic': return '#e74c3c';
      case 'Likely_pathogenic': return '#f39c12';
      case 'Uncertain_significance': return '#3498db';
      case 'Likely_benign': return '#2ecc71';
      case 'Benign': return '#27ae60';
      default: return '#95a5a6';
    }
  });

  return {
    labels,
    datasets: [{
      data,
      backgroundColor: backgroundColors,
      borderWidth: 1
    }]
  };
},
    clinvarDistributionByChromosome() {
      const chromData = {};
      
      this.mergedData.forEach(item => {
        const chrom = item.variant_info?.chrom || 'Unknown';
        // 获取临床意义，如果没有则为'Unknown'
        const significance = item.clinvar_data?.ClinicalSignificance || 'Unknown';
        
        if (!chromData[chrom]) {
          // 初始化每种临床意义为0
          chromData[chrom] = {
            'Pathogenic': 0,
            'Likely_pathogenic': 0,
            'Uncertain_significance': 0,
            'Likely_benign': 0,
            'Benign': 0,
            'Unknown': 0
          };
        }
        
        // 如果这个临床意义在初始化对象中，则累加，否则加到Unknown
        if (significance in chromData[chrom]) {
          chromData[chrom][significance]++;
        } else {
          chromData[chrom]['Unknown']++;
        }
      });
      
      // 排序染色体
      const sortedChroms = Object.keys(chromData).sort((a, b) => {
        const aNum = parseInt(a.replace('chr', '')) || 0;
        const bNum = parseInt(b.replace('chr', '')) || 0;
        return aNum - bNum;
      });
      
      // 定义临床意义的顺序和颜色
      const significanceOrder = [
        'Pathogenic',
        'Likely_pathogenic',
        'Uncertain_significance',
        'Likely_benign',
        'Benign',
        'Unknown'
      ];
      
      const backgroundColorMap = {
        'Pathogenic': '#e74c3c',
        'Likely_pathogenic': '#f39c12',
        'Uncertain_significance': '#3498db',
        'Likely_benign': '#2ecc71',
        'Benign': '#27ae60',
        'Unknown': '#95a5a6'
      };
      
      // 构建数据集
      const datasets = significanceOrder.map(sig => ({
        label: sig,
        data: sortedChroms.map(c => chromData[c][sig]),
        backgroundColor: backgroundColorMap[sig]
      }));
      
      return {
        labels: sortedChroms,
        datasets: datasets
      };
    },
    // 提取含有蛋白变异的条目
    proteinVariants() {
      return this.mergedData.filter(item => item.protein_info);
    },
    
    // 检查是否存在蛋白变异
    hasProteinVariants() {
      return this.proteinVariants.length > 0;
    },
chromosomePredictionChartData() {
  const chromData = {};
  
  this.mergedData.forEach(item => {
    const chrom = item.variant_info?.chrom || 'Unknown';
    const label = item.predict_result?.clnsig_pred || 'Unknown';
    
    if (!chromData[chrom]) {
      chromData[chrom] = {
        Benign: 0,
        Likely_benign: 0,
        Uncertain_significance: 0,
        Likely_pathogenic: 0,
        Pathogenic: 0,
        Unknown: 0
      };
    }
    
    // 确保只累加存在的类别
    if (chromData[chrom][label] !== undefined) {
      chromData[chrom][label] += 1;
    } else {
      chromData[chrom]['Unknown'] += 1;
    }
  });
  
  // 排序染色体
  const sortedChroms = Object.keys(chromData).sort((a, b) => {
    const aNum = parseInt(a.replace('chr', '')) || 0;
    const bNum = parseInt(b.replace('chr', '')) || 0;
    return aNum - bNum;
  });

  // 定义标签顺序和颜色映射
  const labelOrder = [
    'Pathogenic',
    'Likely_pathogenic',
    'Uncertain_significance',
    'Likely_benign',
    'Benign',
    'Unknown'
  ];
  
  const backgroundColorMap = {
    'Pathogenic': '#e74c3c',
    'Likely_pathogenic': '#f39c12',
    'Uncertain_significance': '#3498db',
    'Likely_benign': '#2ecc71',
    'Benign': '#27ae60',
    'Unknown': '#95a5a6'
  };
  
  // 构建数据集
  const datasets = labelOrder.map(label => ({
    label: label,
    data: sortedChroms.map(c => chromData[c][label] || 0),
    backgroundColor: backgroundColorMap[label]
  }));
  
  return {
    labels: sortedChroms,
    datasets: datasets
  };
},
  },

  created() {
    this.fetchResults()
  },
  mounted() {
    // 初始化tooltip
    if (typeof $ !== 'undefined') {
      $('[data-bs-toggle="tooltip"]').tooltip();
    }
  },
  methods: {
    // 排序方法
    sortBy(field) {
      // 如果点击的是同一个字段，切换排序方向
      if (this.sortField === field) {
        this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        // 如果点击的是不同字段，重置排序方向
        this.sortField = field;
        this.sortDirection = 'asc';
      }
      
      // 重置到第一页
      this.currentPage = 1;
    },
    
    // 解析染色体值为可排序的数字
    parseChromosome(chrom) {
      // 移除'chr'前缀
      const numPart = chrom.replace('chr', '');
      // 处理特殊染色体
      if (numPart === 'X') return 23;
      if (numPart === 'Y') return 24;
      if (numPart === 'MT') return 25;
      // 转换为数字
      return parseInt(numPart) || 0;
    },
    
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
        console.log('Response Data:', response.data)
        this.prsScore = response.data.prsScore
        this.prsRisk = response.data.prsRisk
        this.mergedData = response.data.variants || []
        this.modelScore = (response.data.modelScore * 100).toFixed(2)
        

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
      }catch (error) {
        console.error('获取任务结果失败:', error)
        this.taskStatus = 'failed'
        this.errorMessage = '获取任务结果失败'
      }
    },
    getPredictClass(label) {
    if (!label) return 'bg-secondary'
      
      if (label.includes('Pathogenic')) {
        return 'bg-danger'
      } else if (label.includes('Likely_pathogenic')) {
        return 'bg-warning'
      } else if (label.includes('Uncertain_significance')) {
        return 'bg-info'
      } else if (label.includes('Likely_benign')) {
        return 'bg-success'
      } else if (label.includes('Benign')) {
        return 'bg-success'
      }
      return 'bg-secondary'
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
    getRegulomeClass(score) {
    if (!score || typeof score !== 'object') return 'bg-secondary';
    
    // 根据ranking值返回不同颜色
    const firstChar = score.ranking.charAt(0);
    if (['1', '2'].includes(firstChar)) return 'bg-danger';
    if (['3', '4'].includes(firstChar)) return 'bg-warning';
    if (['5', '6'].includes(firstChar)) return 'bg-success';
    return 'bg-secondary';
  },
  formatRegulomeScore(score) {
    if (!score) return 'N/A';
    if (typeof score === 'object') {
      return `${score.ranking} (${score.probability_score})`;
    }
    return score;
  },
    // 格式化序列显示（每10个字符加空格）
    formatSequence(seq) {
      return seq.replace(/(.{10})/g, '$1 ');
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
      const taskId = this.$route.query.task_id;
      if (!taskId) {
        alert('无法生成报告：缺少任务ID');
        return;
      }
      
      // 显示加载状态
      this.isGeneratingPDF = true;
      
      axios.get(`/api/report?task_id=${taskId}`, {
        responseType: 'blob'
      }).then(response => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `dna_report_${taskId}.pdf`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }).catch(error => {
        console.error('下载报告失败:', error);
        alert('报告生成失败，请重试');
      }).finally(() => {
        this.isGeneratingPDF = false;
      });
    },
      
  
    processProteinData() {
  this.mergedData.forEach(item => {
    if (item.protein_info) {
      const position = item.protein_info.position || -1;
      
      // 计算序列显示范围（突变位置前后各15个氨基酸）
      const start = Math.max(0, position - 15);
      const end = Math.min(item.protein_info.wt_seq.length, position + 15);
      
      // 计算突变位置在显示序列中的偏移量
      const mut_pos_offset = position > 0 ? position - start - 1 : -1;
      
      item.protein_info = {
        ...item.protein_info,
        wt_seq_local: this.formatSequence(item.protein_info.wt_seq.substring(start, end)), 
        mut_seq_local: this.formatSequence(item.protein_info.mut_seq.substring(start, end)),
        position: position,
        mut_pos_offset: mut_pos_offset
      };
    }
  });
},
    
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

/* 可排序表头样式 */
.sortable-header {
  cursor: pointer;
  position: relative;
}

.sortable-header:hover {
  background-color: #f0f0f0;
}

/* 排序指示器样式 */
.sort-indicators {
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin-left: 4px;
  width: 16px;
  height: 100%;
}

.sort-indicators i {
  font-size: 0.7rem;
  line-height: 0.8;
  color: #ccc;
  transition: color 0.2s;
}

.sortable-header:hover .sort-indicators i {
  color: #666;
}

.sort-indicators .text-primary {
  color: #0d6efd !important;
}
</style>