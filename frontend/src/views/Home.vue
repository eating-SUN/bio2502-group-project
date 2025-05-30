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
                  <svg class="rotating-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                      <image :xlink:href="DNA_image" width="100%" height="100%" />
                  </svg>
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
    Footer
  },
  data() {
    return {
      DNA_image: DNA_image
    }
  }
}
</script>

<style scoped>
.dna-container {
    width: min(90vw, 600px);  /* 最大宽度600px，小屏自适应 */
    max-height: 50vh;         /* 最大高度50%视口高度 */
    margin: 10px auto;        /* 居中显示 */
    position: relative;
    overflow: hidden;         /* 防止内容溢出 */
}

.dna-container::before {
    content: "";
    display: block;
    padding-top: 100%;            /* 保持1:1比例 */
}

/* 动态调整子容器尺寸 */
.circle-clip {
    width: 50%;
    max-width: 300px;                      
    height: auto;             
    position: absolute;
    border-radius:50%;
    overflow: hidden;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
}


/* 响应式优化 */
@media (max-width: 768px) {
    .dna-container::before {
        padding-top: 75%;         /* 手机端改为4:3比例 */
    }
    
    .circle-clip {
        width: 60%;               /* 放大显示 */
        max-width: none;
    }
}

.text-decoration-none:hover {
  text-decoration: underline !important;
  color: #6a11cb;
}

.rotating-svg {
    width: 100%;
    height: 100%;
    animation: dna-rotate 5s linear infinite;
}

@keyframes dna-rotate {
    0% { transform: translateX(0) rotate(0deg); }
    25% { transform: translateX(0) rotate(20deg); }
    75% { transform: translateX(0) rotate(-20deg); }
    100% { transform: translateX(0) rotate(0deg); }
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
