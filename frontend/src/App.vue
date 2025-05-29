<template>
  <div id="app">
    <!-- 路由视图容器 -->
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
}

/* 全局按钮样式 */
.btn {
  transition: all 0.3s ease;
}

/* 全局卡片样式 */
.card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: none;
  margin-bottom: 1.5rem;
}

/* 全局进度条样式 */
.progress-container {
  position: relative;
  height: 20px;
  margin: 1rem 0;
}

.progress-text {
  position: absolute;
  width: 100%;
  text-align: center;
  line-height: 20px;
  color: #666;
}

/* 全局响应式调整 */
@media (max-width: 768px) {
  .display-4 {
    font-size: 2.5rem;
  }
  
  .lead {
    font-size: 1rem;
  }
}
</style>