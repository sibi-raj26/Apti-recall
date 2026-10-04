import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Topics from '../pages/Topics'

vi.mock('../services/api', () => ({
  topicApi: {
    list: vi.fn().mockResolvedValue([
      { id: 1, name: 'Percentage', slug: 'percentage', description: 'Learn percentages', icon: '', order: 1, is_active: true, created_at: '' },
      { id: 2, name: 'Time Speed Distance', slug: 'time-speed-distance', description: 'TSD problems', icon: '', order: 2, is_active: true, created_at: '' },
    ]),
  },
}))

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Topics', () => {
  it('renders topics list', async () => {
    renderWithProviders(<Topics />)
    await waitFor(() => {
      expect(screen.getByText('Percentage')).toBeDefined()
    })
    expect(screen.getByText('Time Speed Distance')).toBeDefined()
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Topics />)
    expect(screen.getByText('Loading topics...')).toBeDefined()
  })
})
