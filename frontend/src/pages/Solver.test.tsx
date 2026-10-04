import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Solver from '../pages/Solver'
import { solveApi } from '../services/api'

vi.mock('../services/api', () => ({
  solveApi: {
    solve: vi.fn(),
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

const mockSuccessResponse = (overrides: Record<string, unknown> = {}) => ({
  question_text: 'The question asks to calculate 20% of 250.',
  topic: { id: 1, name: 'Percentages' },
  problem_type: { id: 1, name: 'Percentage Calculation' },
  concept: 'Percentage represents a fraction of 100.',
  approach: 'Convert percentage to decimal and multiply.',
  steps: [
    { step: 1, title: 'Convert percentage', calculation: '20% = 0.20', explanation: 'Divide by 100.' },
    { step: 2, title: 'Multiply', calculation: '0.20 × 250 = 50', explanation: 'Compute the result.' },
  ],
  final_answer: '50',
  shortcut: 'Multiply the number by the percentage divided by 100.',
  confidence: 0.95,
  verification_status: 'VERIFIED',
  verification_details: {
    method: 'numeric',
    confidence: 0.98,
    details: 'Result matches expected value.',
    checks: ['input_valid', 'output_matches'],
    expected: '50',
    actual: '50',
  },
  source: 'ai_generated',
  attempt_id: 1,
  ...overrides,
})

describe('Solver', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders solver page for authenticated user', () => {
    renderWithProviders(<Solver />)
    expect(screen.getByText('Ask AptiRecall')).toBeDefined()
    expect(screen.getByLabelText('Your question')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Solve' })).toBeDefined()
  })

  it('does not send request on empty question', async () => {
    renderWithProviders(<Solver />)
    const form = screen.getByRole('button', { name: 'Solve' }).closest('form')!
    fireEvent.submit(form)
    await waitFor(() => {
      expect(screen.getByText('Please enter a question before solving.')).toBeDefined()
    })
    expect(solveApi.solve).not.toHaveBeenCalled()
  })

  it('renders successful solve response with all fields', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse() as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Question Understanding')).toBeDefined()
    })

    expect(screen.getByText('The question asks to calculate 20% of 250.')).toBeDefined()
    expect(screen.getByText('Percentages')).toBeDefined()
    expect(screen.getByText('Percentage Calculation')).toBeDefined()
    expect(screen.getByText(/Percentage represents/)).toBeDefined()
    expect(screen.getByText(/Convert percentage to decimal/)).toBeDefined()
    expect(screen.getByText('Step 1: Convert percentage')).toBeDefined()
    expect(screen.getByText('Step 2: Multiply')).toBeDefined()
    expect(screen.getAllByText('50').length).toBeGreaterThanOrEqual(1)
  })

  it('displays shortcut when returned', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse() as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Shortcut')).toBeDefined()
    })
    expect(screen.getByText('Multiply the number by the percentage divided by 100.')).toBeDefined()
  })

  it('displays VERIFIED status correctly', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse({ verification_status: 'VERIFIED' }) as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeDefined()
    })
  })

  it('displays FAILED status correctly', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse({ verification_status: 'FAILED' }) as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeDefined()
    })
  })

  it('displays UNABLE_TO_VERIFY status correctly', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse({ verification_status: 'UNABLE_TO_VERIFY' }) as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Unable to verify')).toBeDefined()
    })
  })

  it('shows loading state during API request', async () => {
    let resolve: ((value: any) => void) | undefined
    const promise = new Promise((res) => { resolve = res })
    vi.mocked(solveApi.solve).mockReturnValue(promise as any)

    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    expect(screen.getByText('Solving...')).toBeDefined()
    expect(screen.getByText('AptiRecall is solving your question...')).toBeDefined()
    ;(resolve as any)(mockSuccessResponse())
  })

  it('disables submit button while solving', async () => {
    let resolve: ((value: any) => void) | undefined
    const promise = new Promise((res) => { resolve = res })
    vi.mocked(solveApi.solve).mockReturnValue(promise as any)

    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    const button = screen.getByRole('button', { name: 'Solving...' })
    expect(button).toHaveProperty('disabled', true)
    ;(resolve as any)(mockSuccessResponse())
  })

  it('handles 400 input error', async () => {
    vi.mocked(solveApi.solve).mockRejectedValue(new Error('Invalid request data.'))
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Invalid request data.')).toBeDefined()
    })
  })

  it('handles 503 solver unavailable', async () => {
    vi.mocked(solveApi.solve).mockRejectedValue(new Error('AI solver is temporarily unavailable.'))
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('AI solver is temporarily unavailable.')).toBeDefined()
    })
  })

  it('handles 500 error', async () => {
    vi.mocked(solveApi.solve).mockRejectedValue(new Error('An unexpected error occurred.'))
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('An unexpected error occurred.')).toBeDefined()
    })
  })

  it('handles network error', async () => {
    vi.mocked(solveApi.solve).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Network request failed')).toBeDefined()
    })
  })

  it('Solve Another clears the current result', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse() as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Question Understanding')).toBeDefined()
    })

    fireEvent.click(screen.getByRole('button', { name: 'Solve Another' }))
    expect(screen.queryByText('Question Understanding')).toBeNull()
    expect((screen.getByLabelText('Your question') as HTMLTextAreaElement).value).toBe('')
  })

  it('solves with expected request payload', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse() as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(solveApi.solve).toHaveBeenCalledWith('What is 20% of 250?')
    })
  })

  it('does not render shortcut when absent', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse({ shortcut: '' }) as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Question Understanding')).toBeDefined()
    })
    expect(screen.queryByText('Shortcut')).toBeNull()
  })

  it('displays voice explanation unavailable state', async () => {
    vi.mocked(solveApi.solve).mockImplementation(async () => mockSuccessResponse() as any)
    renderWithProviders(<Solver />)
    const textarea = screen.getByLabelText('Your question')
    fireEvent.change(textarea, { target: { value: 'What is 20% of 250?' } })
    fireEvent.submit(textarea.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText('Voice Explanation')).toBeDefined()
    })
    expect(screen.getByText('Voice explanation is not available yet.')).toBeDefined()
  })
})
