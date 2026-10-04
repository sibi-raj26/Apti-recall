import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Progress from '../pages/Progress'
import { progressApi } from '../services/api'

vi.mock('../services/api', () => ({
  progressApi: {
    getDashboard: vi.fn(),
    getAccuracy: vi.fn(),
    getTopics: vi.fn(),
    getMistakes: vi.fn(),
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

describe('Progress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(progressApi.getDashboard).mockRejectedValue(new Error('Not implemented in Phase 11.'))
    vi.mocked(progressApi.getAccuracy).mockRejectedValue(new Error('Not implemented in Phase 11.'))
    vi.mocked(progressApi.getTopics).mockRejectedValue(new Error('Not implemented in Phase 11.'))
    vi.mocked(progressApi.getMistakes).mockRejectedValue(new Error('Not implemented in Phase 11.'))
  })

  it('renders progress page for authenticated user', async () => {
    renderWithProviders(<Progress />)
    expect(screen.getByText('Progress')).toBeDefined()
  })

  it('shows unavailable state when backend returns 501', async () => {
    renderWithProviders(<Progress />)
    await waitFor(() => {
      expect(screen.getByText('Progress analytics are not available yet')).toBeDefined()
    })
    expect(screen.getByText('Backend progress endpoints are still under development. This section will be enabled once the server-side analytics are implemented.')).toBeDefined()
  })

  it('calls all progress APIs on mount', async () => {
    renderWithProviders(<Progress />)
    await waitFor(() => {
      expect(progressApi.getDashboard).toHaveBeenCalledTimes(1)
    })
    expect(progressApi.getAccuracy).toHaveBeenCalledTimes(1)
    expect(progressApi.getTopics).toHaveBeenCalledTimes(1)
    expect(progressApi.getMistakes).toHaveBeenCalledTimes(1)
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Progress />)
    expect(screen.getByText('Loading progress data...')).toBeDefined()
  })

  it('displays retry button on unavailable state', async () => {
    renderWithProviders(<Progress />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
  })

  it('retries loading data when retry is clicked', async () => {
    renderWithProviders(<Progress />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
    vi.mocked(progressApi.getDashboard).mockResolvedValue({} as any)
    fireEvent.click(screen.getByText('Retry'))
    await waitFor(() => {
      expect(progressApi.getDashboard).toHaveBeenCalledTimes(2)
    })
  })

  it('shows connection error message for network failures on unavailable state', async () => {
    vi.mocked(progressApi.getDashboard).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Progress />)
    await waitFor(() => {
      expect(screen.getByText('Connection error. Please check your internet and try again.')).toBeDefined()
    })
  })
})
