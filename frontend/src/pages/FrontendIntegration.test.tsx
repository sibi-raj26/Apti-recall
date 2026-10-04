import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Dashboard from '../pages/Dashboard'
import Solver from '../pages/Solver'
import ImageSolver from '../pages/ImageSolver'
import Topics from '../pages/Topics'

vi.mock('../services/api', () => ({
  topicApi: {
    list: vi.fn().mockRejectedValue(new Error('Network error')),
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

describe('Frontend Integration Tests', () => {
  it('dashboard renders feature cards', async () => {
    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Dashboard')).toBeDefined()
    expect(screen.getByText('Topics')).toBeDefined()
    expect(screen.getByText('AI Solver')).toBeDefined()
  })

  it('solver screen renders input and button', async () => {
    renderWithProviders(<Solver />)
    expect(screen.getByPlaceholderText('Enter your aptitude question here...')).toBeDefined()
    expect(screen.getByText('Solve')).toBeDefined()
  })

  it('image solver screen renders upload options', async () => {
    renderWithProviders(<ImageSolver />)
    expect(screen.getByText('Solve from Image')).toBeDefined()
    expect(screen.getByText('Drag and drop an image here, or click to select')).toBeDefined()
  })

  it('topics screen renders error state when API fails', async () => {
    renderWithProviders(<Topics />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
  })
})
