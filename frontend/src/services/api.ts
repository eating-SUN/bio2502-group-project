import axios from 'axios';

// 使用命名导出而不是默认导出
export const getTaskStatus = (taskId: string) => {
  return axios.get(`/api/status/${taskId}`);
};

export const uploadFile = (formData: FormData) => {
  return axios.post('/api/upload', formData);
};

export const queryRsid = (rsid: string) => {
  return axios.post('/api/query_rsid', { rsid });
};

export const getResults = (taskId: string) => {
  return axios.get('/api/results', { params: { task_id: taskId } });
};