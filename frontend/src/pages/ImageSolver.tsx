import { useState, useRef, useCallback } from 'react'
import { uploadApi } from '../services/api'
import type { UploadQuestionResponse, SolveResponse } from '../types/api'

type Step = 'select' | 'preview' | 'processing' | 'questions' | 'solving' | 'result'

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
const MAX_FILE_SIZE = 10 * 1024 * 1024

const VERIFICATION_STATUS_COPY: Record<string, { label: string; color: string }> = {
  VERIFIED: { label: 'Verified', color: '#16a34a' },
  FAILED: { label: 'Failed', color: '#dc2626' },
  UNABLE_TO_VERIFY: { label: 'Unable to verify', color: '#d97706' },
  NOT_VERIFIED: { label: 'Not verified', color: '#6b7280' },
}

export default function ImageSolver() {
  const [step, setStep] = useState<Step>('select')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [ocrResult, setOcrResult] = useState<UploadQuestionResponse | null>(null)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [solution, setSolution] = useState<SolveResponse | null>(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const previewUrlRef = useRef<string | null>(null)

  const clearPreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setImagePreview(null)
  }, [])

  const validateFile = (file: File): string | null => {
    if (!file) return 'Please select an image file.'
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Please select a supported image file.'
    }
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Please select a supported image file.'
    }
    if (file.size > MAX_FILE_SIZE) {
      return `Image size exceeds the allowed limit of ${MAX_FILE_SIZE / 1024 / 1024}MB.`
    }
    return null
  }

  const processFile = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      setStep('select')
      return
    }

    clearPreview()
    const url = URL.createObjectURL(file)
    previewUrlRef.current = url
    setImagePreview(url)
    setSelectedFile(file)
    setStep('preview')
    setError('')
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) processFile(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer.files?.[0]
    if (file) processFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleRemove = () => {
    clearPreview()
    setSelectedFile(null)
    setStep('select')
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setError('')
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
    setStep('processing')

    try {
      const data = await uploadApi.uploadImage(selectedFile)
      setOcrResult(data)
      if (data.questions && data.questions.length > 0 && data.questions.length === 1) {
        setSelectedIndex(data.questions[0].index)
      }
      setStep('questions')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process image.'
      if (message.includes('temporarily unavailable') || message.includes('503')) {
        setError('Image processing is temporarily unavailable. Please try again.')
      } else if (message.includes('size') || message.includes('limit')) {
        setError('Image size exceeds the allowed limit.')
      } else if (message.includes('Unsupported') || message.includes('VALIDATION_ERROR')) {
        setError('Please select a supported image file.')
      } else if (message.includes('Network') || message.includes('network')) {
        setError('Connection error. Please check your internet and try again.')
      } else {
        setError('Failed to process the image. Please try again.')
      }
      setStep('preview')
    }
  }

  const handleSolve = async () => {
    if (!ocrResult || selectedIndex === null) return

    setError('')
    setSolution(null)
    setStep('solving')

    try {
      const data = await uploadApi.solveUploaded({
        upload_id: ocrResult.upload_id,
        question_index: selectedIndex,
      })
      setSolution(data)
      setStep('result')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong while solving.'
      if (message.includes('temporarily unavailable') || message.includes('503')) {
        setError('Image processing is temporarily unavailable. Please try again.')
      } else {
        setError(message)
      }
      setStep('questions')
    }
  }

  const handleReset = () => {
    clearPreview()
    setSelectedFile(null)
    setStep('select')
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSolveAnother = () => {
    clearPreview()
    setSelectedFile(null)
    setStep('select')
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const renderVerificationDetails = (details: Record<string, unknown> | undefined) => {
    if (!details || Object.keys(details).length === 0) return null
    const method = typeof details.method === 'string' ? details.method : null
    const confidence = typeof details.confidence === 'number' ? details.confidence : null
    const detailText = typeof details.details === 'string' ? details.details : null
    const checks = Array.isArray(details.checks) ? details.checks : []
    const expected = details.expected != null ? String(details.expected) : null
    const actual = details.actual != null ? String(details.actual) : null
    return (
      <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.6 }}>
        {method && <div><strong>Method:</strong> {method}</div>}
        {confidence != null && <div><strong>Confidence:</strong> {confidence.toFixed(2)}</div>}
        {detailText && <div style={{ marginTop: '8px' }}><strong>Details:</strong> {detailText}</div>}
        {checks.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            <strong>Checks:</strong>
            <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
              {checks.map((check, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{String(check)}</li>
              ))}
            </ul>
          </div>
        )}
        {expected != null && <div style={{ marginTop: '8px' }}><strong>Expected:</strong> {expected}</div>}
        {actual != null && <div style={{ marginTop: '8px' }}><strong>Actual:</strong> {actual}</div>}
      </div>
    )
  }

  const renderSolution = (result: SolveResponse) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {result.question_text && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Question Understanding</div>
          <div style={{ lineHeight: 1.6 }}>{result.question_text}</div>
        </div>
      )}

      {result.topic && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Topic</div>
          <div style={{ fontWeight: 500 }}>{result.topic.name}</div>
        </div>
      )}

      {result.problem_type && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Problem Type</div>
          <div style={{ fontWeight: 500 }}>{result.problem_type.name}</div>
        </div>
      )}

      {result.concept && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Concept</div>
          <div style={{ lineHeight: 1.6 }}>{result.concept}</div>
        </div>
      )}

      {result.approach && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Approach</div>
          <div style={{ lineHeight: 1.6 }}>{result.approach}</div>
        </div>
      )}

      {result.steps && result.steps.length > 0 && (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Step-by-step Solution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {result.steps.map((step) => (
              <div key={step.step} style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
                  Step {step.step}: {step.title}
                </div>
                {step.calculation && (
                  <code style={{ display: 'block', marginBottom: '8px', padding: '8px', background: 'var(--code-bg)', borderRadius: '4px', fontSize: '14px' }}>
                    {step.calculation}
                  </code>
                )}
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.6 }}>
                  {step.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--accent-bg)' }}>
        <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Final Answer</div>
        <div style={{ fontSize: '20px', fontWeight: 500 }}>{result.final_answer}</div>
      </div>

      {result.shortcut && (
        <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Shortcut</h2>
          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.6 }}>{result.shortcut}</p>
        </div>
      )}

      <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Verification</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: result.verification_details && Object.keys(result.verification_details).length > 0 ? '12px' : '0' }}>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '4px',
              background: VERIFICATION_STATUS_COPY[result.verification_status]?.color || 'var(--social-bg)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            {VERIFICATION_STATUS_COPY[result.verification_status]?.label || result.verification_status}
          </span>
        </div>
        {renderVerificationDetails(result.verification_details)}
      </div>
    </div>
  )

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px' }}>Solve from Image</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px', lineHeight: 1.6 }}>
        Upload an aptitude question image and AptiRecall will extract the question before solving it.
      </p>

      {error && (
        <p style={{ margin: '0 0 16px', fontSize: '14px', color: '#dc2626' }}>{error}</p>
      )}

      {step === 'select' && (
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={{
            border: '2px dashed var(--border)',
            borderRadius: '8px',
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text)',
            cursor: 'pointer',
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>📷</div>
          <p style={{ marginBottom: '8px', fontSize: '16px', color: 'var(--text-h)' }}>
            Drag and drop an image here, or click to select
          </p>
          <p style={{ fontSize: '14px' }}>
            Supports JPG, PNG, WEBP up to 10MB
          </p>
        </div>
      )}

      {step === 'preview' && selectedFile && imagePreview && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ borderRadius: '8px', border: '1px solid var(--border)', overflow: 'hidden' }}>
            <img
              src={imagePreview}
              alt="Selected question preview"
              style={{ width: '100%', maxHeight: '300px', objectFit: 'contain', display: 'block' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <span style={{ fontSize: '14px', color: 'var(--text)' }}>{selectedFile.name}</span>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                type="button"
                onClick={handleRemove}
                style={{
                  padding: '10px 20px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                  background: 'transparent',
                  color: 'var(--text)',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                Remove
              </button>
              <button
                type="button"
                onClick={handleUpload}
                style={{
                  padding: '10px 20px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent)',
                  color: '#fff',
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                }}
              >
                Process Image
              </button>
            </div>
          </div>
        </div>
      )}

      {step === 'processing' && (
        <div
          style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            textAlign: 'center',
            color: 'var(--text)',
          }}
        >
          <p>Reading your image...</p>
        </div>
      )}

      {step === 'questions' && ocrResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Detected Questions</h2>
            {ocrResult.questions.length === 0 ? (
              <p style={{ color: 'var(--text)', fontSize: '14px' }}>
                No questions were detected in this image. Please try a clearer image.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {ocrResult.questions.map((q) => (
                  <div
                    key={q.index}
                    onClick={() => setSelectedIndex(q.index)}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: selectedIndex === q.index ? '2px solid var(--accent)' : '1px solid var(--border)',
                      background: selectedIndex === q.index ? 'var(--accent-bg)' : 'var(--bg)',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <div
                        style={{
                          width: '20px',
                          height: '20px',
                          borderRadius: '50%',
                          border: selectedIndex === q.index ? '2px solid var(--accent)' : '1px solid var(--border)',
                          background: selectedIndex === q.index ? 'var(--accent)' : 'transparent',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        {selectedIndex === q.index && (
                          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff' }} />
                        )}
                      </div>
                      <span style={{ fontWeight: 500, fontSize: '14px' }}>Question {q.index}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.6, paddingLeft: '32px' }}>
                      {q.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              onClick={handleSolve}
              disabled={selectedIndex === null || ocrResult.questions.length === 0}
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent)',
                color: '#fff',
                fontSize: '14px',
                fontWeight: 500,
                cursor: (selectedIndex === null || ocrResult.questions.length === 0) ? 'not-allowed' : 'pointer',
                opacity: (selectedIndex === null || ocrResult.questions.length === 0) ? 0.7 : 1,
              }}
            >
              Solve Selected
            </button>
            <button
              type="button"
              onClick={handleReset}
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                background: 'transparent',
                color: 'var(--text)',
                fontSize: '14px',
                cursor: 'pointer',
              }}
            >
              Upload New Image
            </button>
          </div>
        </div>
      )}

      {step === 'solving' && (
        <div
          style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            textAlign: 'center',
            color: 'var(--text)',
          }}
        >
          <p>AptiRecall is solving your question...</p>
        </div>
      )}

      {step === 'result' && solution && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {renderSolution(solution)}
          <button
            type="button"
            onClick={handleSolveAnother}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text)',
              fontSize: '14px',
              cursor: 'pointer',
              alignSelf: 'flex-start',
            }}
          >
            Solve Another Image
          </button>
        </div>
      )}
    </div>
  )
}
