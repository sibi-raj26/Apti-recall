import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Recall from '../pages/Recall'
import { recallApi } from '../services/api'

vi.mock('../services/api', () => ({
  recallApi: {
    getSchedule: vi.fn(),
    getWeakTopics: vi.fn(),
    getAnalytics: vi.fn(),
    submit: vi.fn(),
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

const mockRecallRecord = (overrides: Record<string, unknown> = {}): any => ({
  id: 1,
  topic: 1,
  problem_type: 2,
  question: 10,
  recall_score: 0.75,
  accuracy_score: 0.8,
  practice_count: 3,
  last_practiced: '2024-06-01T10:00:00Z',
  next_practice_at: '2024-06-08T10:00:00Z',
  difficulty_at_practice: 'medium',
  is_weak: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-06-01T10:00:00Z',
  ...overrides,
})

const mockAnalytics = (overrides: Record<string, unknown> = {}): any => ({
  total_topics: 5,
  weak_count: 1,
  moderate_count: 2,
  strong_count: 2,
  average_recall_score: 0.65,
  ...overrides,
})

describe('Recall', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(recallApi.getSchedule).mockResolvedValue([mockRecallRecord()] as any)
    vi.mocked(recallApi.getWeakTopics).mockResolvedValue([mockRecallRecord({ id: 2, is_weak: true })] as any)
    vi.mocked(recallApi.getAnalytics).mockResolvedValue(mockAnalytics() as any)
    vi.mocked(recallApi.submit).mockResolvedValue(mockRecallRecord({ id: 3, practice_count: 4 }) as any)
  })

  it('renders recall page for authenticated user', async () => {
    renderWithProviders(<Recall />)
    expect(screen.getByText('Adaptive Recall')).toBeDefined()
  })

  it('calls schedule, weak-topics, and analytics APIs on mount', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(recallApi.getSchedule).toHaveBeenCalledTimes(1)
    })
    expect(recallApi.getWeakTopics).toHaveBeenCalledTimes(1)
    expect(recallApi.getAnalytics).toHaveBeenCalledTimes(1)
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Recall />)
    expect(screen.getByText('Loading recall data...')).toBeDefined()
  })

  it('displays due questions after loading', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('Question #10').length).toBeGreaterThanOrEqual(1)
  })

  it('shows empty state when no due questions', async () => {
    vi.mocked(recallApi.getSchedule).mockResolvedValue([] as any)
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('No recall questions are due right now.')).toBeDefined()
    })
  })

  it('displays weak topics after loading', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Weak Topics')).toBeDefined()
    })
    expect(screen.getAllByText('Weak').length).toBeGreaterThanOrEqual(1)
  })

  it('shows empty state when no weak topics', async () => {
    vi.mocked(recallApi.getWeakTopics).mockResolvedValue([] as any)
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('No weak topics detected. Keep practicing!')).toBeDefined()
    })
  })

  it('displays analytics after loading', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Total Topics')).toBeDefined()
    })
    expect(screen.getByText('5')).toBeDefined()
    expect(screen.getByText('65%')).toBeDefined()
  })

  it('shows error when schedule API fails', async () => {
    vi.mocked(recallApi.getSchedule).mockRejectedValue(new Error('Schedule failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Schedule failed')).toBeDefined()
    })
  })

  it('shows error when weak-topics API fails', async () => {
    vi.mocked(recallApi.getWeakTopics).mockRejectedValue(new Error('Weak topics failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Weak topics failed')).toBeDefined()
    })
  })

  it('shows error when analytics API fails', async () => {
    vi.mocked(recallApi.getAnalytics).mockRejectedValue(new Error('Analytics failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Analytics failed')).toBeDefined()
    })
  })

  it('displays retry button on error', async () => {
    vi.mocked(recallApi.getSchedule).mockRejectedValue(new Error('Network error'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
  })

  it('retries loading data when retry is clicked', async () => {
    vi.mocked(recallApi.getSchedule).mockRejectedValue(new Error('Network error'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
    vi.mocked(recallApi.getSchedule).mockResolvedValue([mockRecallRecord()] as any)
    fireEvent.click(screen.getByText('Retry'))
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
  })

  it('renders question link when question id exists', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    const links = screen.getAllByRole('link', { name: /Question #10/ })
    expect(links.length).toBeGreaterThanOrEqual(1)
    expect(links[0].getAttribute('href')).toBe('/questions/10')
  })

  it('renders topic text when question is null', async () => {
    vi.mocked(recallApi.getSchedule).mockResolvedValue([mockRecallRecord({ question: null })] as any)
    vi.mocked(recallApi.getWeakTopics).mockResolvedValue([] as any)
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getAllByText('Topic #1').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders formatted dates', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getAllByText(/2024/).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders Never for null dates', async () => {
    vi.mocked(recallApi.getSchedule).mockResolvedValue([mockRecallRecord({ last_practiced: null, next_practice_at: null })] as any)
    vi.mocked(recallApi.getWeakTopics).mockResolvedValue([] as any)
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getAllByText(/Never/).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('displays recall score percentage', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(1)
  })

  it('displays accuracy percentage', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('80%').length).toBeGreaterThanOrEqual(1)
  })

  it('displays practice count', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('3').length).toBeGreaterThanOrEqual(1)
  })

  it('displays weak badge for weak records', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Weak Topics')).toBeDefined()
    })
    expect(screen.getAllByText('Weak').length).toBeGreaterThanOrEqual(1)
  })

  it('displays difficulty badge', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('medium').length).toBeGreaterThanOrEqual(1)
  })

  it('shows Practice This Question link when question exists', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.getAllByText('Practice This Question').length).toBeGreaterThanOrEqual(1)
  })

  it('does not show Practice This Question when question is null', async () => {
    vi.mocked(recallApi.getSchedule).mockResolvedValue([mockRecallRecord({ question: null })] as any)
    vi.mocked(recallApi.getWeakTopics).mockResolvedValue([] as any)
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Due for Practice')).toBeDefined()
    })
    expect(screen.queryByText('Practice This Question')).toBeNull()
  })

  it('shows submit attempt form', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Submit Completed Attempt')).toBeDefined()
    })
    expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
  })

  it('submits recall attempt successfully', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
    })
    const input = screen.getByLabelText('Completed Attempt ID') as HTMLInputElement
    fireEvent.change(input, { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Attempt' }))
    await waitFor(() => {
      expect(screen.getByText(/Recall updated for record/)).toBeDefined()
    })
    expect(recallApi.submit).toHaveBeenCalledWith(5)
  })

  it('shows validation error for invalid attempt id', async () => {
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
    })
    const input = screen.getByLabelText('Completed Attempt ID') as HTMLInputElement
    fireEvent.change(input, { target: { value: '0' } })
    const form = input.closest('form')
    if (form) fireEvent.submit(form)
    await waitFor(() => {
      expect(screen.getByText('Please enter a valid attempt ID.')).toBeDefined()
    })
  })

  it('shows error when submit fails', async () => {
    vi.mocked(recallApi.submit).mockRejectedValue(new Error('Submit failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
    })
    const input = screen.getByLabelText('Completed Attempt ID') as HTMLInputElement
    fireEvent.change(input, { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Attempt' }))
    await waitFor(() => {
      expect(screen.getByText('Submit failed')).toBeDefined()
    })
  })

  it('shows not found error for missing attempt', async () => {
    vi.mocked(recallApi.submit).mockRejectedValue(new Error('Completed attempt not found.'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
    })
    const input = screen.getByLabelText('Completed Attempt ID') as HTMLInputElement
    fireEvent.change(input, { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Attempt' }))
    await waitFor(() => {
      expect(screen.getByText('Completed attempt not found. Make sure the attempt is completed and belongs to you.')).toBeDefined()
    })
  })

  it('shows network error for connection issues on submit', async () => {
    vi.mocked(recallApi.submit).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByLabelText('Completed Attempt ID')).toBeDefined()
    })
    const input = screen.getByLabelText('Completed Attempt ID') as HTMLInputElement
    fireEvent.change(input, { target: { value: '5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Attempt' }))
    await waitFor(() => {
      expect(screen.getByText('Connection error. Please check your internet and try again.')).toBeDefined()
    })
  })

  it('shows connection error message for network failures', async () => {
    vi.mocked(recallApi.getSchedule).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Recall />)
    await waitFor(() => {
      expect(screen.getByText('Connection error. Please check your internet and try again.')).toBeDefined()
    })
  })
})
