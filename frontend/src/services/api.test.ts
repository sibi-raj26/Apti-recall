import { describe, it, expect } from 'vitest'
import api from './api'

describe('api configuration', () => {
  it('configures baseURL from VITE_API_URL with /api fallback', () => {
    const expected = (import.meta.env.VITE_API_URL as string | undefined) || '/api'
    expect(api.defaults.baseURL).toBe(expected)
  })
})
