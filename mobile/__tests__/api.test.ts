import { describe, it, expect, vi } from 'vitest'

vi.mock('expo-secure-store', () => ({
  getItemAsync: vi.fn(),
  setItemAsync: vi.fn(),
  deleteItemAsync: vi.fn(),
}))

describe('API client', () => {
  it('includes Authorization header when access token exists', async () => {
    const { getItemAsync } = await import('expo-secure-store')
    vi.mocked(getItemAsync).mockResolvedValue('token')

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, data: { id: 1 } }),
      text: () => Promise.resolve(''),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { request } = await import('../src/services/api')
    await request('/auth/me/')

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/auth/me/',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Authorization: 'Bearer token',
        }),
      })
    )
  })

  it('throws parsed API error message', async () => {
    const { getItemAsync } = await import('expo-secure-store')
    vi.mocked(getItemAsync).mockResolvedValue(null)

    const errorPayload = { detail: 'Invalid credentials' }
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve(errorPayload),
      text: () => Promise.resolve(JSON.stringify(errorPayload)),
    })
    vi.stubGlobal('fetch', mockFetch)

    const { request } = await import('../src/services/api')
    await expect(request('/auth/me/')).rejects.toThrow('Invalid credentials')
  })
})
