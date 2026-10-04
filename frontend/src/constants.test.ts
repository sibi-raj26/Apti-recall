import { describe, it, expect } from 'vitest'


describe('shared constants', () => {
  it('topics list is non-empty', async () => {
    const { TOPICS } = await import('../../shared/constants/topics')
    expect(TOPICS.length).toBeGreaterThan(0)
  })
})
