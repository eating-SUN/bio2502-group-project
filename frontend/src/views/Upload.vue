<template>
  <div>
    <NavBar />
    
    <div class="container mt-4">
      <!-- 文件上传区 -->
      <div class="card card-spacing form-section">
        <h6>文件较大时处理时间可能较长，请耐心等待（5000条记录约需3分钟）</h6>
        <div class="card-header bg-info text-white">上传VCF文件</div>
        <div class="card-body">
          <form @submit.prevent="submitFile"> 
            <input 
              type="file" 
              id="vcfFile" 
              class="form-control mb-3" 
              accept=".vcf"
              @change="handleFileChange"
            >
            
            <div v-if="showUploadProgress" class="progress-container">
              <div class="progress-bar progress-bar-striped progress-bar-animated" 
                   role="progressbar" 
                   :style="{ width: progress + '%' }">
              </div>
              <div class="progress-text">{{ progress }}%</div>
            </div>
            
            <div v-if="uploadSuccess" class="alert alert-success mt-2">
              {{ uploadSuccess }}
            </div>
            
            <div v-if="uploadError" class="alert alert-danger mt-2">
              {{ uploadError }}
            </div>

            <div class="d-flex justify-content-between align-items-center">
              <button 
                type="submit" 
                class="btn btn-primary"
                :disabled="isUploading"
              >
                {{ isUploading ? '上传中...' : '提交分析' }}
              </button> 
              <button 
                type="button" 
                class="btn btn-secondary" 
                @click="resetForm"
              >
                重置
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- RSID查询区 -->
      <div class="card card-spacing form-section">
        <div class="card-header bg-info text-white">RSID查询</div>
        <div class="card-body">
          <div class="input-group">
            <input 
              type="text" 
              id="rsid-input" 
              class="form-control mb-3"
              placeholder="输入RSID (例如: rs123456)"
              v-model="rsid"
              @input="clearRsidError"
            >
          </div>
          <div v-if="rsidError" class="alert alert-danger mt-2">
            {{ rsidError }}
          </div>
          <div class="d-flex justify-content-between align-items-center">
            <button 
              class="btn btn-primary"
              @click="submitRSID"
              :disabled="isQuerying"
            >
              {{ isQuerying ? '查询中...' : '查询' }}
            </button>
            <button 
              class="btn btn-secondary" 
              @click="clearRsidInput"
            >
              清除
            </button>
          </div>
        </div>
      </div>
    </div>
    <br>
    <Footer />
  </div>
</template>

<script>
import NavBar from '@components/NavBar.vue'
import Footer from '@components/Footer.vue'
import { uploadFile, getTaskStatus, queryRsid } from '@services/api'; // 引入 api.js 


export default {
  components: {
    NavBar,
    Footer
  },
  data() {
    return {
      selectedFile: null,
      rsid: '',
      isUploading: false,
      isQuerying: false,
      showUploadProgress: false,
      progress: 0,
      uploadSuccess: '',
      uploadError: '',
      rsidError: '',
      taskId: null,
      progressInterval: null
    }
  },
  methods: {
    handleFileChange(event) {
      this.selectedFile = event.target.files[0];
      this.uploadError = '';
    },
    clearRsidError() {
      this.rsidError = '';
    },
    clearRsidInput() {
      this.rsid = '';
      this.rsidError = '';
    },
    resetForm() {
      this.selectedFile = null;
      document.getElementById('vcfFile').value = '';
      this.uploadError = '';
      this.showUploadProgress = false;
      this.progress = 0;
      this.uploadSuccess = '';
    },
    async submitFile() {
      this.uploadError = '';
      this.rsidError = '';
      if (!this.selectedFile) {
        this.uploadError = '请选择要上传的VCF文件';
        return;
      }

      const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
      if (this.selectedFile.size > MAX_FILE_SIZE) {
        this.uploadError = `文件大小不能超过 ${MAX_FILE_SIZE / (1024 * 1024)} MB`;
        return;
      }
      if (!this.selectedFile.name.toLowerCase().endsWith('.vcf')) {
        this.uploadError = '仅支持 .vcf 文件';
        return;
      }
      this.isUploading = true;
      this.showUploadProgress = true;
      this.uploadError = '';
      this.uploadSuccess = '';

      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        const response = await uploadFile(formData); // 调用 api.js 中的 uploadFile 函数

        if (response.data.status === 'queued') {
          this.uploadSuccess = '文件上传成功，正在处理...';
          this.taskId = response.data.task_id;
          this.startProgressCheck();
        } else {
          this.uploadError = '上传失败，请重试';
        }
      } catch (error) {
        if (error.response?.status === 400) {
          this.uploadError = '上传失败: ' + 
            (error.response.data?.error || '无效的文件');
        } else {
          this.uploadError = '上传失败: ' + 
            (error.message || '网络错误');
        }
      }
      finally {
        this.isUploading = false;
      }
    },
    async submitRSID() {
      this.uploadError = '';
      this.rsidError = '';
      if (!this.rsid) {
        this.rsidError = '请输入有效的RSID';
        return;
      }
      if (!/^rs\d+$/.test(this.rsid)) {
        this.rsidError = 'RSID格式不正确（示例：rs123456）';
        return;
      }

      this.isQuerying = true;
      this.rsidError = '';

      try {
        const response = await queryRsid({ rsid: this.rsid }); 

        if (response.data.status === 'queued') {
          this.taskId = response.data.task_id;
          this.startProgressCheck();
        } else {
          this.rsidError = '查询失败，请重试';
        }
      } catch (error) {
        console.error('RSID查询失败:', error);
        this.rsidError = error.response?.data?.error || '查询失败，请检查网络连接';
      } finally {
        this.isQuerying = false;
      }
    },
    startProgressCheck() {
      if (this.progressInterval) {
        clearInterval(this.progressInterval);
      }

      this.progressInterval = setInterval(() => {
        this.checkTaskStatus();
      }, 3000);
    },
    async checkTaskStatus() {
  if (!this.taskId) return;

  try {
    const response = await getTaskStatus(this.taskId);
    const { status, progress, task_type } = response.data; 

    this.progress = progress;

    if (status === 'completed') {
      clearInterval(this.progressInterval);
      this.$router.push({ path: '/results', query: { task_id: this.taskId } });
    } else if (status === 'failed') {
      clearInterval(this.progressInterval);
      this.progressInterval = null;
      
      // 根据任务来源显示错误信息
      if (task_type === 'vcf') {
      this.uploadError = response.data.error_message || 'VCF处理失败';
      this.rsidError = '';
    } else if (task_type === 'rsid') {
      this.rsidError = response.data.error_message || 'RSID查询失败';
      this.uploadError = '';
    } else {
      // 未知类型的错误
      this.uploadError = '未知任务类型的错误:'+response.data.error_message || '任务处理失败';
      this.rsidError = '未知任务类型的错误:'+response.data.error_message || '任务处理失败';
    }
    }
  } catch (error) {
    console.error('获取任务状态失败:', error);
    clearInterval(this.progressInterval);
    this.progressInterval = null;
    
    const errorMsg = error.response?.data?.error || 
                    error.message || 
                    '服务不可用，请稍后重试';
    
    // 根据当前操作显示错误
    if (this.isUploading) {
      this.uploadError = `状态检查失败: ${errorMsg}`;
      this.rsidError = '';
    } else if (this.isQuerying) {
      this.rsidError = `状态检查失败: ${errorMsg}`;
      this.uploadError = '';
    }
  }
},
  beforeUnmount() {
  if (this.progressInterval) {
    clearInterval(this.progressInterval);
    this.progressInterval = null;
    }
  },
}}
</script>

<style scoped>
.form-section {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 0.5rem;
}

.progress-container {
  position: relative;
  height: 20px;
  margin: 1rem 0;
}

.progress-bar {
  height: 100%;
}

.progress-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  text-align: center;
  line-height: 20px;
  color: #666;
}

.card-spacing {
  margin-bottom: 1.5rem;
}

.alert {
  opacity: 1;
  transition: opacity 0.3s ease;
}
</style>