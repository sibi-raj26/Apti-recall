import { describe, it, expect, vi } from 'vitest'

vi.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: vi.fn(),
  launchCameraAsync: vi.fn(),
  MediaTypeOptions: { images: 'images' },
}))

vi.mock('expo-media-library', () => ({
  requestPermissionsAsync: vi.fn().mockResolvedValue({ granted: true }),
}))

vi.mock('expo-router', () => ({
  router: { replace: vi.fn(), push: vi.fn(), back: vi.fn() },
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), back: vi.fn() }),
  useLocalSearchParams: () => ({}),
}))

describe('ImageSolverScreen', () => {
  it('module loads without throwing', async () => {
    const module = await import('../src/app/image-solver')
    expect(typeof module.default).toBe('function')
  })
})
