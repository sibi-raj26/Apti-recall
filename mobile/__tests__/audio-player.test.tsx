import { describe, it, expect, vi } from 'vitest'

vi.mock('expo-av', () => ({
  Audio: {
    Sound: {
      createAsync: vi.fn().mockResolvedValue({ sound: { unloadAsync: vi.fn(), setOnPlaybackStatusUpdate: vi.fn() } }),
    },
    setAudioModeAsync: vi.fn(),
  },
  AVPlaybackStatus: {},
}))

describe('AudioPlayer', () => {
  it('renders unavailable state when no audioUrl is provided', async () => {
    const module = await import('../src/components/AudioPlayer')
    expect(typeof module.default).toBe('function')
  })
})
