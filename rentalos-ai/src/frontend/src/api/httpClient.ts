import axios from 'axios'

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API error', error)
    return Promise.reject(error)
  },
)

export default httpClient
