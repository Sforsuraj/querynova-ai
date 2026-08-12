import axios from 'axios';
const API_URL = (import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8080' : ''))
  .replace(/\/+$/, '')
  .replace(/\/api$/, '');
const API = `${API_URL}/api`;
export const conversationApi = {
  list: search => axios.get(`${API}/conversations`, {params: search ? {search} : {}}).then(r => r.data),
  create: () => axios.post(`${API}/conversations`, {}).then(r => r.data),
  get: id => axios.get(`${API}/conversations/${id}`).then(r => r.data),
  rename: (id, title) => axios.put(`${API}/conversations/${id}`, {title}).then(r => r.data),
  remove: id => axios.delete(`${API}/conversations/${id}`),
  send: (id, message) => axios.post(`${API}/conversations/${id}/messages`, {message}).then(r => r.data),
  regenerate: (conversationId, messageId) => axios.post(`${API}/conversations/${conversationId}/messages/${messageId}/regenerate`).then(r => r.data)
};
