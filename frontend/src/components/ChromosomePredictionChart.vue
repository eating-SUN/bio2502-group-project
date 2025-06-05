<template>
  <div class="chart-container">
    <h5 class="text-center mb-3">染色体预测结果分布</h5>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

export default {
  props: {
    chartData: Object
  },
  mounted() {
    this.renderChart();
  },
  watch: {
    chartData: {
      deep: true,
      handler() {
        this.renderChart();
      }
    }
  },
  methods: {
    renderChart() {
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }
      
      if (!this.chartData || !this.chartData.labels) return;
      
      const ctx = this.$refs.chartCanvas.getContext('2d');
      this.chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: this.chartData.labels,
          datasets: this.chartData.datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              stacked: true,
              title: {
                display: true,
                text: '染色体'
              }
            },
            y: {
              stacked: true,
              beginAtZero: true,
              title: {
                display: true,
                text: '变异数量'
              }
            }
          },
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              callbacks: {
                title: (items) => `染色体 ${items[0].label}`,
                label: (context) => {
                  const label = context.dataset.label || '';
                  const value = context.raw || 0;
                  return `${label}: ${value} 个变异`;
                }
              }
            }
          }
        }
      });
    }
  },
  beforeUnmount() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }
};
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 400px;
  padding: 50px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>