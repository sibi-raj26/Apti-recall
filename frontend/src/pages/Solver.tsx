import { useState } from 'react'
import { solveApi } from '../services/api'
import type { SolveResponse } from '../types/api'

type SolveStatus = 'idle' | 'loading' | 'success' | 'error'

const VERIFICATION_STATUS_COPY: Record<string, { label: string; color: string }> = {
  VERIFIED: { label: 'Verified', color: '#16a34a' },
  FAILED: { label: 'Failed', color: '#dc2626' },
  UNABLE_TO_VERIFY: { label: 'Unable to verify', color: '#d97706' },
  NOT_VERIFIED: { label: 'Not verified', color: '#6b7280' },
}

export default function Solver() {
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState<SolveStatus>('idle')
  const [result, setResult] = useState<SolveResponse | null>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = question.trim()
    if (!trimmed) {
      setError('Please enter a question before solving.')
      return
    }

    setError('')
    setResult(null)
    setStatus('loading')

    try {
      const data = await solveApi.solve(trimmed)
      setResult(data)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong while solving.')
      setStatus('error')
    }
  }

  const handleReset = () => {
    setQuestion('')
    setResult(null)
    setError('')
    setStatus('idle')
  }

  const renderVerificationDetails = () => {
    if (!result?.verification_details || Object.keys(result.verification_details).length === 0) {
      return null
    }
    const details = result.verification_details as Record<string, unknown>
    const method = typeof details.method === 'string' ? details.method : null
    const confidence = typeof details.confidence === 'number' ? details.confidence : null
    const detailText = typeof details.details === 'string' ? details.details : null
    const checks = Array.isArray(details.checks) ? details.checks : []
    const expected = details.expected != null ? String(details.expected) : null
    const actual = details.actual != null ? String(details.actual) : null
    return (
      <div style={{ fontSize: '14px', color: 'var(--text)', lineHeight: 1.6 }}>
        {method && (
          <div><strong>Method:</strong> {method}</div>
        )}
        {confidence != null && (
          <div><strong>Confidence:</strong> {confidence.toFixed(2)}</div>
        )}
        {detailText && (
          <div style={{ marginTop: '8px' }}><strong>Details:</strong> {detailText}</div>
        )}
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
        {expected != null && (
          <div style={{ marginTop: '8px' }}><strong>Expected:</strong> {expected}</div>
        )}
        {actual != null && (
          <div style={{ marginTop: '8px' }}><strong>Actual:</strong> {actual}</div>
        )}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px' }}>Ask AptiRecall</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px', lineHeight: 1.6 }}>
        Enter an aptitude question to receive a step-by-step explanation, shortcut, and verification result when available.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
          <label htmlFor="solve-question" style={{ fontSize: '14px', fontWeight: 500 }}>
            Your question
          </label>
          <textarea
            id="solve-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your aptitude question here..."
            rows={5}
            disabled={status === 'loading'}
            style={{
              padding: '12px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--text-h)',
              fontSize: '14px',
              lineHeight: 1.6,
              resize: 'vertical',
              opacity: status === 'loading' ? 0.7 : 1,
            }}
          />
        </div>

        {error && (
          <p style={{ margin: 0, fontSize: '14px', color: '#dc2626' }}>
            {error}
          </p>
        )}

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            type="submit"
            disabled={status === 'loading'}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              background: 'var(--accent)',
              color: '#fff',
              fontSize: '14px',
              fontWeight: 500,
              cursor: status === 'loading' ? 'not-allowed' : 'pointer',
              opacity: status === 'loading' ? 0.7 : 1,
            }}
          >
            {status === 'loading' ? 'Solving...' : 'Solve'}
          </button>

          {(status === 'success' || status === 'error') && (
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
              Solve Another
            </button>
          )}
        </div>
      </form>

      {status === 'loading' && (
        <div style={{
          padding: '24px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          textAlign: 'center',
          color: 'var(--text)',
        }}>
          <p>AptiRecall is solving your question...</p>
        </div>
      )}

      {status === 'success' && result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {result.question_text && (
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Question Understanding</div>
              <div style={{ lineHeight: 1.6 }}>{result.question_text}</div>
            </div>
          )}

          {result.topic && (
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Topic</div>
              <div style={{ fontWeight: 500 }}>{result.topic.name}</div>
            </div>
          )}

          {result.problem_type && (
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Problem Type</div>
              <div style={{ fontWeight: 500 }}>{result.problem_type.name}</div>
            </div>
          )}

          {result.concept && (
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Concept</div>
              <div style={{ lineHeight: 1.6 }}>{result.concept}</div>
            </div>
          )}

          {result.approach && (
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Approach</div>
              <div style={{ lineHeight: 1.6 }}>{result.approach}</div>
            </div>
          )}

          {result.steps && result.steps.length > 0 && (
            <div style={{
              padding: '24px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Step-by-step Solution</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {result.steps.map((step) => (
                  <div
                    key={step.step}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: '1px solid var(--border)',
                    }}
                  >
                    <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
                      Step {step.step}: {step.title}
                    </div>
                    {step.calculation && (
                      <code style={{
                        display: 'block',
                        marginBottom: '8px',
                        padding: '8px',
                        background: 'var(--code-bg)',
                        borderRadius: '4px',
                        fontSize: '14px',
                      }}>
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

          <div style={{
            padding: '20px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--accent-bg)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Final Answer</div>
            <div style={{ fontSize: '20px', fontWeight: 500 }}>{result.final_answer}</div>
          </div>

          {result.shortcut && (
            <div style={{
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Shortcut</h2>
              <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.6 }}>{result.shortcut}</p>
            </div>
          )}

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
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
            {renderVerificationDetails()}
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '8px' }}>Voice Explanation</div>
            <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.6 }}>
              Voice explanation is not available yet.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
