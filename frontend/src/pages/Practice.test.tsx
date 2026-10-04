import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Practice from '../pages/Practice'
import { questionApi, practiceApi } from '../services/api'

vi.mock('../services/api', () => ({
  questionApi: {
    list: vi.fn(),
  },
  practiceApi: {
    generate: vi.fn(),
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

const mockQuestion = (overrides: Record<string, unknown> = {}): any => ({
  id: 1,
  topic: 1,
  topic_name: 'Percentages',
  problem_type: 1,
  problem_type_name: 'Percentage Calculation',
  subtopic: null,
  subtopic_name: null,
  difficulty: 'easy',
  question_text: 'What is 20% of 250?',
  question_latex: '',
  correct_answer: '50',
  correct_answer_latex: '',
  explanation_concept: 'Percentage represents a fraction of 100.',
  explanation_approach: 'Convert percentage to decimal and multiply.',
  explanation_steps: [],
  hints: [],
  tags: [],
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

const mockPracticeResponse = (overrides: Record<string, unknown> = {}): any => ({
  question_text: 'What is 15% of 300?',
  topic: { id: 1, name: 'Percentages' },
  problem_type: { id: 1, name: 'Percentage Calculation' },
  difficulty: 'easy',
  concept: 'Percentage represents a fraction of 100.',
  approach: 'Convert percentage to decimal and multiply.',
  steps: [
    { step: 1, title: 'Convert percentage', calculation: '15% = 0.15', explanation: 'Divide by 100.' },
    { step: 2, title: 'Multiply', calculation: '0.15 × 300 = 45', explanation: 'Compute the result.' },
  ],
  final_answer: '45',
  shortcut: 'Multiply the number by the percentage divided by 100.',
  confidence: 0.95,
  verification_status: 'VERIFIED',
  verification_details: {
    method: 'numeric',
    confidence: 0.98,
    details: 'Result matches expected value.',
    checks: ['input_valid', 'output_matches'],
    expected: '45',
    actual: '45',
  },
  source: 'practice_generated',
  attempt: 1,
  ...overrides,
})

describe('Practice', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(questionApi.list).mockResolvedValue({ data: [mockQuestion()] } as any)
  })

  it('renders practice page for authenticated user', async () => {
    renderWithProviders(<Practice />)
    expect(screen.getByText('Similar Practice')).toBeDefined()
  })

  it('shows loading state while loading questions', async () => {
    let resolve: ((value: any) => void) | undefined
    const promise = new Promise((res) => { resolve = res })
    vi.mocked(questionApi.list).mockReturnValue(promise as any)

    renderWithProviders(<Practice />)
    expect(screen.getByText('Loading questions...')).toBeDefined()
    ;(resolve as any)({ data: [mockQuestion()] })
  })

  it('displays source questions after loading', async () => {
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    expect(screen.getByText('Select a Source Question')).toBeDefined()
  })

  it('allows selecting a source question', async () => {
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    expect(screen.getByRole('button', { name: 'Generate Similar Question' })).toBeDefined()
  })

  it('calls practice generate API with selected question_id', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(practiceApi.generate).toHaveBeenCalledWith({ question_id: 1 })
    })
  })

  it('shows loading state during generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    expect(screen.getByText('AptiRecall is generating a similar practice question...')).toBeDefined()
  })

  it('displays generated question after successful generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Generated Question')).toBeDefined()
    })
    expect(screen.getByText('What is 15% of 300?')).toBeDefined()
    expect(screen.getByText('Percentages')).toBeDefined()
    expect(screen.getByText('Percentage Calculation')).toBeDefined()
  })

  it('displays solution steps after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Step-by-step Solution')).toBeDefined()
    })
    expect(screen.getByText('Step 1: Convert percentage')).toBeDefined()
    expect(screen.getByText('Step 2: Multiply')).toBeDefined()
  })

  it('displays final answer after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Final Answer')).toBeDefined()
    })
    expect(screen.getAllByText('45').length).toBeGreaterThanOrEqual(1)
  })

  it('displays VERIFIED status after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse({ verification_status: 'VERIFIED' }) as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeDefined()
    })
  })

  it('displays FAILED status after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse({ verification_status: 'FAILED' }) as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeDefined()
    })
  })

  it('displays UNABLE status after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse({ verification_status: 'UNABLE' }) as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Unable to verify')).toBeDefined()
    })
  })

  it('displays NOT_VERIFIED status after generation', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse({ verification_status: 'NOT_VERIFIED' }) as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Not verified')).toBeDefined()
    })
  })

  it('handles 400 validation error', async () => {
    vi.mocked(practiceApi.generate).mockRejectedValue(new Error('Provide either question_id, or upload_id with question_index, or topic+problem_type+difficulty+question_text.'))
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText(/Provide either question_id/)).toBeDefined()
    })
  })

  it('shows empty state when no questions are available', async () => {
    vi.mocked(questionApi.list).mockResolvedValue({ data: [] } as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('No questions available.')).toBeDefined()
    })
  })

  it('handles 503 service unavailable', async () => {
    vi.mocked(practiceApi.generate).mockRejectedValue(new Error('AI service is temporarily unavailable.'))
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Practice generation is temporarily unavailable. Please try again.')).toBeDefined()
    })
  })

  it('handles network error', async () => {
    vi.mocked(practiceApi.generate).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Connection error. Please check your internet and try again.')).toBeDefined()
    })
  })

  it('Practice Another resets to question selection', async () => {
    vi.mocked(practiceApi.generate).mockImplementation(async () => mockPracticeResponse() as any)
    renderWithProviders(<Practice />)
    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Generate Similar Question' }))

    await waitFor(() => {
      expect(screen.getByText('Generated Question')).toBeDefined()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Practice Another' }))
    expect(screen.getByText('Select a Source Question')).toBeDefined()
    expect(screen.queryByText('Generated Question')).toBeNull()
  })
})
