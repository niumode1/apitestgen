import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default apiClient

// API modules
export * from './projects'
export * from './specs'
export * from './endpoints'
export * from './llm'
