import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import ImageSolver from '../pages/ImageSolver'
import { uploadApi } from '../services/api'

vi.mock('../services/api', () => ({
  uploadApi: {
    uploadImage: vi.fn(),
    solveUploaded: vi.fn(),
  },
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

const mockOcrResponse = (overrides: Record<string, unknown> = {}) => ({
  upload_id: 1,
  status: 'ocr_completed',
  text: 'What is 20% of 250?\nA train travels at 60 km/h.',
  questions: [
    { index: 1, text: 'What is 20% of 250?' },
    { index: 2, text: 'A train travels at 60 km/h.' },
  ],
  ocr_provider: 'tesseract',
  ocr_confidence: 0.95,
  ...overrides,
})

const mockSolveResponse = (overrides: Record<string, unknown> = {}) => ({
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

describe('ImageSolver', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders image solver page for authenticated user', () => {
    renderWithProviders(<ImageSolver />)
    expect(screen.getByText('Solve from Image')).toBeDefined()
    expect(screen.getByText(/Upload an aptitude question image/)).toBeDefined()
    expect(screen.getByText('Drag and drop an image here, or click to select')).toBeDefined()
  })

  it('shows validation error for unsupported file type', async () => {
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.txt', { type: 'text/plain' })
    Object.defineProperty(file, 'size', { value: 1024 })
    const dataTransfer = {
      files: [file],
      items: [],
      types: [],
    }
    fireEvent.drop(input, { dataTransfer })
    await waitFor(() => {
      expect(screen.getByText('Please select a supported image file.')).toBeDefined()
    })
  })

  it('shows validation error for oversized file', async () => {
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 })
    const dataTransfer = {
      files: [file],
      items: [],
      types: [],
    }
    fireEvent.drop(input, { dataTransfer })
    await waitFor(() => {
      expect(screen.getByText('Image size exceeds the allowed limit of 10MB.')).toBeDefined()
    })
  })

  it('shows preview after selecting valid image', async () => {
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeDefined()
    })
    expect(screen.getByRole('button', { name: 'Process Image' })).toBeDefined()
    expect(screen.getByRole('button', { name: 'Remove' })).toBeDefined()
  })

  it('calls upload API when processing image', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse() as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Process Image' })).toBeDefined()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(uploadApi.uploadImage).toHaveBeenCalledWith(expect.any(File))
    })
  })

  it('displays detected questions after OCR', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse() as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Detected Questions')).toBeDefined()
    })
    expect(screen.getByText('Question 1')).toBeDefined()
    expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    expect(screen.getByText('Question 2')).toBeDefined()
    expect(screen.getByText('A train travels at 60 km/h.')).toBeDefined()
  })

  it('auto-selects single question', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
  })

  it('solves selected question', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse() as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse() as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Detected Questions')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Question 1'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(uploadApi.solveUploaded).toHaveBeenCalledWith({
        upload_id: 1,
        question_index: 1,
      })
    })
  })

  it('shows loading state during OCR', async () => {
    let resolve: ((value: any) => void) | undefined
    const promise = new Promise((res) => { resolve = res })
    vi.mocked(uploadApi.uploadImage).mockReturnValue(promise as any)

    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    expect(screen.getByText('Reading your image...')).toBeDefined()
    ;(resolve as any)(mockOcrResponse())
  })

  it('shows loading state during solve', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse() as any)
    let resolve: ((value: any) => void) | undefined
    const promise = new Promise((res) => { resolve = res })
    vi.mocked(uploadApi.solveUploaded).mockReturnValue(promise as any)

    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Detected Questions')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Question 1'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    expect(screen.getByText('AptiRecall is solving your question...')).toBeDefined()
    ;(resolve as any)(mockSolveResponse())
  })

  it('handles 503 OCR unavailable', async () => {
    vi.mocked(uploadApi.uploadImage).mockRejectedValue(new Error('Image processing is temporarily unavailable.'))
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Image processing is temporarily unavailable. Please try again.')).toBeDefined()
    })
  })

  it('handles 500 error', async () => {
    vi.mocked(uploadApi.uploadImage).mockRejectedValue(new Error('An unexpected error occurred.'))
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Failed to process the image. Please try again.')).toBeDefined()
    })
  })

  it('handles network error', async () => {
    vi.mocked(uploadApi.uploadImage).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Connection error. Please check your internet and try again.')).toBeDefined()
    })
  })

  it('disables solve button when no question selected', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse() as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('Detected Questions')).toBeDefined()
    })
    const solveButton = screen.getByRole('button', { name: 'Solve Selected' })
    expect(solveButton).toHaveProperty('disabled', true)
  })

  it('removes file when remove button clicked', async () => {
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeDefined()
    })
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    expect(screen.getByText('Drag and drop an image here, or click to select')).toBeDefined()
  })

  it('renders successful solve response after solving', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse() as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(screen.getByText('Question Understanding')).toBeDefined()
    })
    expect(screen.getByText('Percentages')).toBeDefined()
    expect(screen.getByText('Step 1: Convert percentage')).toBeDefined()
  })

  it('displays VERIFIED status after solving', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse({ verification_status: 'VERIFIED' }) as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(screen.getByText('Verified')).toBeDefined()
    })
  })

  it('displays FAILED status after solving', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse({ verification_status: 'FAILED' }) as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(screen.getByText('Failed')).toBeDefined()
    })
  })

  it('displays UNABLE_TO_VERIFY status after solving', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse({ verification_status: 'UNABLE_TO_VERIFY' }) as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(screen.getByText('Unable to verify')).toBeDefined()
    })
  })

  it('displays NOT_VERIFIED status after solving', async () => {
    vi.mocked(uploadApi.uploadImage).mockImplementation(async () => mockOcrResponse({ questions: [{ index: 1, text: 'What is 20% of 250?' }] }) as any)
    vi.mocked(uploadApi.solveUploaded).mockImplementation(async () => mockSolveResponse({ verification_status: 'NOT_VERIFIED' }) as any)
    renderWithProviders(<ImageSolver />)
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    Object.defineProperty(file, 'size', { value: 1024 * 1024 })
    fireEvent.change(input, { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Process Image' }))

    await waitFor(() => {
      expect(screen.getByText('What is 20% of 250?')).toBeDefined()
    })
    fireEvent.click(screen.getByText('What is 20% of 250?'))
    fireEvent.click(screen.getByRole('button', { name: 'Solve Selected' }))

    await waitFor(() => {
      expect(screen.getByText('Not verified')).toBeDefined()
    })
  })
})
