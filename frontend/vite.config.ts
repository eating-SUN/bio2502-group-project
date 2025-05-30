import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import svgLoader from 'vite-svg-loader'
import path from 'path' // 添加 path 模块

export default defineConfig({
  plugins: [vue(), svgLoader()],
  resolve: {
    alias: {
      // 添加路径别名配置
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@services': path.resolve(__dirname, './src/services')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})