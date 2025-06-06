import axios from 'axios';

// 创建带有基础路径的 axios 实例
const apiClient = axios.create({
  baseURL: './', // 使用当前域名的相对路径
  timeout: 30000 // 增加超时时间
});

export const getTaskStatus = (taskId: string) => {
  return apiClient.get(`api/status/${taskId}`);
};

export const uploadFile = (formData: FormData) => {
  return apiClient.post('api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data' // 确保设置正确的 content-type
    }
  });
};

export const queryRsid = (rsid: string) => {
  return apiClient.post('api/query_rsid', { rsid });
};

export const getResults = (taskId: string) => {
  return apiClient.get('api/results', { params: { task_id: taskId } });
};