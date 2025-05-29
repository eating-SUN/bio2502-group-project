// src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api', // 后端 Flask 地址
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 文件上传 API
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

// 查询任务状态 API
export const getTaskStatus = (taskId) => {
  return api.get(`/status/${taskId}`);
};

// 查询 RSID API
export const queryRsid = (rsid) => {
  return api.post('/query_rsid', { rsid });
};

// 获取结果 API
export const getResults = (taskId) => {
  return api.get(`/results?task_id=${taskId}`);
};

export default api;