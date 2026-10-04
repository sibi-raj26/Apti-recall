import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Admin from '../pages/Admin'
import { topicApi, adminApi } from '../services/api'

vi.mock('../services/api', () => ({
  topicApi: {
    list: vi.fn(),
  },
  adminApi: {
    listQuestions: vi.fn(),
    listUsers: vi.fn(),
    getDashboard: vi.fn(),
    getPerformance: vi.fn(),
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

describe('Admin', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(topicApi.list).mockResolvedValue([
      { id: 1, name: 'Percentage', slug: 'percentage', description: 'Learn percentages', icon: '', order: 1, is_active: true, created_at: '' },
    ])
    vi.mocked(adminApi.listQuestions).mockResolvedValue([
      { id: 1, topic: 1, topic_name: 'Percentage', problem_type: 1, problem_type_name: 'of', subtopic: null, subtopic_name: '', difficulty: 'easy', question_text: 'What is 10% of 100?', question_latex: '', correct_answer: '10', correct_answer_latex: '', explanation_concept: '', explanation_approach: '', explanation_steps: [], hints: [], tags: [], is_active: true, created_at: '' },
    ] as any)
    vi.mocked(adminApi.listUsers).mockRejectedValue(new Error('Not implemented in Phase 11.'))
    vi.mocked(adminApi.getDashboard).mockRejectedValue(new Error('Not implemented in Phase 11.'))
    vi.mocked(adminApi.getPerformance).mockRejectedValue(new Error('Not implemented in Phase 11.'))
  })

  it('renders admin page for authenticated user', async () => {
    renderWithProviders(<Admin />)
    expect(screen.getByText('Admin')).toBeDefined()
  })

  it('shows topics tab by default', async () => {
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(screen.getByText('Percentage')).toBeDefined()
    })
  })

  it('loads topics from topicApi.list on mount', async () => {
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(topicApi.list).toHaveBeenCalledTimes(1)
    })
  })

  it('switches to questions tab', async () => {
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(screen.getByText('Percentage')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Questions'))
    await waitFor(() => {
      expect(screen.getByText('What is 10% of 100?')).toBeDefined()
    })
  })

  it('switches to dashboard tab and shows unavailable', async () => {
    renderWithProviders(<Admin />)
    fireEvent.click(screen.getByText('Dashboard'))
    await waitFor(() => {
      expect(screen.getByText('Admin dashboard are not available yet')).toBeDefined()
    })
  })

  it('switches to users tab and shows unavailable', async () => {
    renderWithProviders(<Admin />)
    fireEvent.click(screen.getByText('Users'))
    await waitFor(() => {
      expect(screen.getByText('User management are not available yet')).toBeDefined()
    })
  })

  it('switches to performance tab and shows unavailable', async () => {
    renderWithProviders(<Admin />)
    fireEvent.click(screen.getByText('Performance'))
    await waitFor(() => {
      expect(screen.getByText('Performance analytics are not available yet')).toBeDefined()
    })
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Admin />)
    expect(screen.getByText('Loading...')).toBeDefined()
  })

  it('shows error on API failure', async () => {
    vi.mocked(topicApi.list).mockRejectedValue(new Error('Failed to load'))
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(screen.getByText('Failed to load')).toBeDefined()
    })
  })

  it('shows retry button on error', async () => {
    vi.mocked(topicApi.list).mockRejectedValue(new Error('Failed to load'))
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
  })

  it('retries loading data when retry is clicked', async () => {
    vi.mocked(topicApi.list).mockRejectedValue(new Error('Failed to load'))
    renderWithProviders(<Admin />)
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeDefined()
    })
    vi.mocked(topicApi.list).mockResolvedValue([
      { id: 1, name: 'Percentage', slug: 'percentage', description: 'Learn percentages', icon: '', order: 1, is_active: true, created_at: '' },
    ])
    fireEvent.click(screen.getByText('Retry'))
    await waitFor(() => {
      expect(topicApi.list).toHaveBeenCalledTimes(2)
    })
  })
})
