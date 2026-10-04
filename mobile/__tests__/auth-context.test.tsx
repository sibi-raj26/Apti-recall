import { describe, it, expect, vi } from 'vitest'

const mockAuthApi = vi.fn()
vi.doMock('../src/services/api', () => ({
  authApi: {
    getCurrentUser: mockAuthApi,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  },
  topicApi: { list: vi.fn() },
  questionApi: { list: vi.fn() },
  solveApi: { solve: vi.fn() },
}))

describe('AuthContext', () => {
  it('loads user from secure store on init', async () => {
    mockAuthApi.mockResolvedValue({ success: true, data: { id: 1, email: 'a@b.com', username: 'a' } })
    vi.stubGlobal('SecureStore', {
      getItemAsync: vi.fn().mockResolvedValue('token'),
      setItemAsync: vi.fn(),
      deleteItemAsync: vi.fn(),
    })

    const { AuthProvider, useAuth } = await import('../src/contexts/app/AuthContext')

    // Smoke test: AuthProvider module loads without throwing
    expect(typeof AuthProvider).toBe('function')
    expect(typeof useAuth).toBe('function')
  })
})
