<!-- 文件路径: src/components/ModelRiskChart.vue -->
<template>
  <div class="card h-100">
    <div class="card-header bg-primary text-white">
      <h5 class="mb-0">神经网络风险预测</h5>
    </div>
    <div class="card-body d-flex flex-column">
      <div class="risk-gauge">
        <div class="gauge-background"></div>
        <div class="gauge-fill" :style="{ height: fillHeight }"></div>
        <div class="gauge-pointer" :style="{ transform: pointerRotation }"></div>
        <div class="gauge-labels">
          <span>低</span>
          <span>中</span>
          <span>高</span>
        </div>
      </div>
      <div class="mt-auto text-center">
        <p class="mb-0">预测结果: <strong :class="riskClass">{{ riskLabel }}</strong></p>
        <p class="text-muted small mt-2">基于深度学习模型对多个变异进行加权评分</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    riskLevel: {
      type: Number,
      default: 0 // 0:未知, 1:低, 2:中, 3:高
    }
  },
  computed: {
    fillHeight() {
      const heights = ['0%', '33%', '66%', '100%']
      return heights[this.riskLevel] || '0%'
    },
    pointerRotation() {
      const rotations = ['rotate(-60deg)', 'rotate(-30deg)', 'rotate(0deg)', 'rotate(30deg)']
      return rotations[this.riskLevel] || 'rotate(-60deg)'
    },
    riskLabel() {
      const labels = ['未评估', '低风险', '中等风险', '高风险']
      return labels[this.riskLevel] || '未评估'
    },
    riskClass() {
      const classes = ['text-secondary', 'text-success', 'text-warning', 'text-danger']
      return classes[this.riskLevel] || 'text-secondary'
    }
  }
}
</script>

<style scoped>
.risk-gauge {
  position: relative;
  height: 180px;
  width: 100%;
  margin-bottom: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  overflow: hidden;
}

.gauge-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(to top, #28a745 0%, #ffc107 50%, #dc3545 100%);
  opacity: 0.2;
}

.gauge-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, #28a745 0%, #ffc107 50%, #dc3545 100%);
  transition: height 0.8s ease;
}

.gauge-pointer {
  position: absolute;
  bottom: -10px;
  left: 50%;
  width: 2px;
  height: 80px;
  background: #000;
  transform-origin: bottom center;
  transition: transform 0.8s ease;
  z-index: 10;
}

.gauge-pointer::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: -8px;
  width: 18px;
  height: 18px;
  background: #343a40;
  border-radius: 50%;
}

.gauge-labels {
  position: absolute;
  bottom: 10px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  padding: 0 15px;
  font-size: 0.85rem;
  font-weight: bold;
  z-index: 5;
}
</style>