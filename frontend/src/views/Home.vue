<template>
  <div>
    <!-- 导航栏 -->
    <NavBar />
    
    <!-- 头部内容 -->
    <header class="py-5 text-center bg-primary text-white">
      <div class="container d-flex flex-column align-items-center gap-4">
          <!-- 文字内容 -->
          <div class="content-group">
              <h1 class="display-4 fw-bold">基因变异分析平台</h1>
              <p class="lead">基于机器学习与生物信息学的致病性预测系统</p>
          </div>

          <!-- DNA动画容器 -->
          <div class="dna-container">
              <div class="circle-clip">
           
                   <DNA_image class="rotating-svg" />
                   
              </div>
          </div>

          <!-- 按钮 -->
          <div class="button-group mt-3">
              <router-link to="/upload" class="btn btn-light btn-lg">开始使用</router-link>
          </div>
      </div>
  </header>
    
    <!-- 研究内容区 -->
    <section id="research" class="py-5">
      <div class="container">
          <h2 class="text-center mb-5">我们的研究</h2>
          <div class="row row-cols-1 row-cols-md-4 g-4">
              <div class="col">
                  <div class="card research-card h-100">
                      <div class="card-body text-center">
                          <h5 class="card-title">临床注释</h5>
                          <p class="card-text">整合ClinVar数据库，建立本地注释系统</p>
                          <i class="bi bi-database-fill fs-1 text-primary"></i>
                      </div>
                  </div>
              </div>
              <div class="col">
                  <div class="card research-card h-100">
                      <div class="card-body text-center">
                          <h5 class="card-title">机器学习</h5>
                          <p class="card-text">随机森林模型预测变异致病性（AUC&gt;0.8）</p>
                          <i class="bi bi-brain fs-1 text-primary"></i>
                      </div>
                  </div>
              </div>
              <div class="col">
                  <div class="card research-card h-100">
                      <div class="card-body text-center">
                          <h5 class="card-title">功能分析</h5>
                          <p class="card-text">蛋白质结构预测与调控区域注释</p>
                          <i class="bi bi-protein fs-1 text-primary"></i>
                      </div>
                  </div>
              </div>
              <div class="col">
                  <div class="card research-card h-100">
                      <div class="card-body text-center">
                          <h5 class="card-title">PRS分析</h5>
                          <p class="card-text">整合多处变异预测乳腺癌概率</p>
                          <i class="bi bi-protein fs-1 text-primary"></i>
                      </div>
                  </div>
              </div>
          </div>
      </div>
  </section>

    
    
    <!-- 使用方法 -->
    <section id="methods" class="py-5 bg-light">
        <div class="container">
            <h2 class="text-center mb-5">使用指南</h2>
            <div class="row text-center">
                <div class="col-md-4 mb-4">
                    <div class="method-step">1</div>
                    <h4>
                        <router-link to="/upload" class="text-decoration-none">上传数据</router-link>
                    </h4>
                    <p>支持VCF文件和RSid查询</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="method-step">2</div>
                    <h4>
                        <router-link to="/results" class="text-decoration-none">系统分析</router-link>
                    </h4>
                    <p>自动进行注释与致病性预测</p>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="method-step">3</div>
                    <h4>
                        <router-link to="/results" class="text-decoration-none">下载报告</router-link>
                    </h4>
                    <p>生成PDF格式的完整分析报告</p>
                </div>
            </div>
        </div>
    </section>
    
    <!-- 页脚 -->
    <Footer />
  </div>
</template>

<script>
import NavBar from '@components/NavBar.vue'
import Footer from '@components/Footer.vue'
import DNA_image from '@assets/medical-01.svg'

export default {
  name: 'HomeView',
  components: {
    NavBar,
    Footer,
    DNA_image
  },

}
</script>


<style scoped>
/* 头部内容 */
header {
  position: relative; /* 为DNA容器提供定位上下文 */
  overflow: hidden; /* 隐藏溢出部分 */
}

/* DNA容器 */
.dna-container {
  width: 300px;
  height: 300px;
  margin: 20px auto;
  position: relative;
}

/* 圆形裁剪 */
.circle-clip {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.3); /* 添加柔和的光晕效果 */
}

/* DNA图片 */
.rotating-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover; /* 确保图片填充整个容器 */
  animation: dna-rotate 10s linear infinite;
  transform-origin: center center;
}

/* 更平滑的旋转动画 */
@keyframes dna-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式优化 - 手机端 */
@media (max-width: 768px) {
  .dna-container {
    width: 200px;
    height: 200px;
    margin: 15px auto;
  }
  
  header h1 {
    font-size: 2.2rem;
  }
  
  header p {
    font-size: 1.1rem;
  }
}

/* 其他样式保持不变 */
.text-decoration-none:hover {
  text-decoration: underline !important;
  color: #6a11cb;
}

.research-card {
  background: #F8F9FA;
  border-left: 5px solid #2A5CAA;
}

.method-step {
  font-size: 1.5rem;
  color: #2A5CAA;
}

</style>
