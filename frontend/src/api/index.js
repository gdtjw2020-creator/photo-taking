import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 60000
})


// 请求拦截器：注入 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// 响应拦截器：处理 401
api.interceptors.response.use(response => {
  return response
}, error => {
  if (error.response && error.response.status === 401) {
    // 可以在这里触发跳转到登录页或清除过期 Token
    localStorage.removeItem('token')
    // window.location.href = '/profile' // 或者显示登录弹窗
  }
  return Promise.reject(error)
})

export default api
