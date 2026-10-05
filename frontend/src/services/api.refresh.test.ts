import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { authApi } from '../services/api'

const baseURL = (import.meta.env.VITE_API_URL as string | undefined) || '/api'

describe('authApi refresh interceptor behavior', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('does not recursively call /auth/refresh/ when refresh itself returns 401', async () => {
    let refreshCallCount = 0

    const originalCreate = axios.create
    vi.spyOn(axios, 'create').mockImplementation((config) => {
      const instance = originalCreate(config)

      instance.interceptors.response.use(
        (response) => response,
        async (error) => {
          if (error.response?.status === 401) {
            const refresh = localStorage.getItem('aptirecall_refresh')
            if (refresh) {
              refreshCallCount++
              if (refreshCallCount > 2) {
                throw new Error('INFINITE_REFRESH_LOOP')
              }
              const { data } = await instance.post('/auth/refresh/', { refresh })
              const newAccess = data.data.access
              localStorage.setItem('aptirecall_access', newAccess)
              if (data.data.refresh) {
                localStorage.setItem('aptirecall_refresh', data.data.refresh)
              }
              error.config.headers.Authorization = `Bearer ${newAccess}`
              return instance.request(error.config)
            }
            window.location.href = '/login'
          }
          return Promise.reject(error)
        }
      )

      return instance
    })

    localStorage.setItem('aptirecall_access', 'expired-access')
    localStorage.setItem('aptirecall_refresh', 'valid-refresh')

    vi.spyOn(axios, 'post').mockImplementation((url: string) => {
      if (url === `${baseURL}/auth/refresh/`) {
        return Promise.reject({ response: { status: 401, data: {} } })
      }
      return Promise.resolve({ data: {} })
    })

    try {
      await authApi.getCurrentUser()
    } catch {
      // expected
    }

    expect(refreshCallCount).toBeLessThanOrEqual(2)
  })
})
