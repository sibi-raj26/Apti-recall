import { describe, it, expect, vi } from 'vitest'

vi.mock('expo-camera', () => ({
  CameraView: 'CameraView',
  useCameraPermissions: vi.fn(() => [{ granted: false }, vi.fn()]),
  CameraType: { back: 'back', front: 'front' },
}))

vi.mock('expo-router', () => ({
  router: { replace: vi.fn(), push: vi.fn(), back: vi.fn() },
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), back: vi.fn() }),
  useLocalSearchParams: () => ({}),
  useCameraPermissions: vi.fn(() => [{ granted: false }, vi.fn()]),
}))

describe('CameraScreen', () => {
  it('module loads without throwing', async () => {
    const module = await import('../src/app/camera')
    expect(typeof module.default).toBe('function')
  })
})
