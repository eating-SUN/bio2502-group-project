<template>
  <div class="chart-container">
    <h5 class="text-center mb-3">染色体变异分布</h5>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'

export default {
  props: {
    chartData: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    let chartInstance = null
    
    const renderChart = () => {
      if (chartInstance) {
        chartInstance.destroy()
      }
      
      if (!chartCanvas.value || !props.chartData) return
      
      const ctx = chartCanvas.value.getContext('2d')
      chartInstance = new Chart(ctx, {
        type: 'bar',
        data: props.chartData,
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: '变异数量'
              }
            },
            x: {
              title: {
                display: true,
                text: '染色体'
              }
            }
          }
        }
      })
    }
    
    onMounted(renderChart)
    watch(() => props.chartData, renderChart, { deep: true })
    
    return {
      chartCanvas
    }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>