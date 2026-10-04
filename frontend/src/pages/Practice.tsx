import { useEffect, useState } from 'react'
import { questionApi, practiceApi } from '../services/api'
import type { Question, PracticeGenerateResponse } from '../types/api'

type PracticeStatus = 'idle' | 'loading_questions' | 'selecting' | 'generating' | 'result' | 'error'

const VERIFICATION_STATUS_COPY: Record<string, { label: string; color: string }> = {
  VERIFIED: { label: 'Verified', color: '#16a34a' },
  FAILED: { label: 'Failed', color: '#dc2626' },
  UNABLE: { label: 'Unable to verify', color: '#d97706' },
  NOT_VERIFIED: { label: 'Not verified', color: '#6b7280' },
}

export default function Practice() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [status, setStatus] = useState<PracticeStatus>('idle')
  const [sourceQuestion, setSourceQuestion] = useState<Question | null>(null)
  const [result, setResult] = useState<PracticeGenerateResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadQuestions = async () => {
      setError('')
      setStatus('loading_questions')
      try {
        const res = await questionApi.list()
        setQuestions(res.data)
        setStatus('selecting')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load questions.')
        setStatus('error')
      }
    }
    loadQuestions()
  }, [])

  const handleSelectSource = (question: Question) => {
    setSourceQuestion(question)
    setResult(null)
    setError('')
    setStatus('selecting')
  }

  const handleGenerate = async () => {
    if (!sourceQuestion) return

    setError('')
    setResult(null)
    setStatus('generating')

    try {
      const data = await practiceApi.generate({ question_id: sourceQuestion.id })
      setResult(data)
      setStatus('result')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate practice question.'
      if (message.includes('temporarily unavailable') || message.includes('503')) {
        setError('Practice generation is temporarily unavailable. Please try again.')
      } else if (message.includes('not found') || message.includes('404')) {
        setError('The selected question could not be found.')
      } else if (message.includes('Network') || message.includes('network')) {
        setError('Connection error. Please check your internet and try again.')
      } else {
        setError(message)
      }
      setStatus('selecting')
    }
  }

  const handleReset = () => {
    setSourceQuestion(null)
    setResult(null)
    setError('')
    setStatus('selecting')
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

  const renderSolution = (data: PracticeGenerateResponse) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {data.question_text && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Generated Question</div>
          <div style={{ lineHeight: 1.6 }}>{data.question_text}</div>
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {data.topic?.name && (
          <span style={{ padding: '4px 10px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)', fontSize: '12px' }}>
            {data.topic.name}
          </span>
        )}
        {data.problem_type?.name && (
          <span style={{ padding: '4px 10px', borderRadius: '4px', background: 'var(--social-bg)', fontSize: '12px' }}>
            {data.problem_type.name}
          </span>
        )}
        {data.difficulty && (
          <span style={{ padding: '4px 10px', borderRadius: '4px', background: 'var(--social-bg)', fontSize: '12px', textTransform: 'capitalize' }}>
            {data.difficulty}
          </span>
        )}
      </div>

      {data.concept && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Concept</div>
          <div style={{ lineHeight: 1.6 }}>{data.concept}</div>
        </div>
      )}

      {data.approach && (
        <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Approach</div>
          <div style={{ lineHeight: 1.6 }}>{data.approach}</div>
        </div>
      )}

      {data.steps && data.steps.length > 0 && (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Step-by-step Solution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {data.steps.map((step) => (
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
        <div style={{ fontSize: '20px', fontWeight: 500 }}>{data.final_answer}</div>
      </div>

      {data.shortcut && (
        <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Shortcut</h2>
          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.6 }}>{data.shortcut}</p>
        </div>
      )}

      <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Verification</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: data.verification_details && Object.keys(data.verification_details).length > 0 ? '12px' : '0' }}>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '4px',
              background: VERIFICATION_STATUS_COPY[data.verification_status]?.color || 'var(--social-bg)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 500,
            }}
          >
            {VERIFICATION_STATUS_COPY[data.verification_status]?.label || data.verification_status}
          </span>
        </div>
        {renderVerificationDetails(data.verification_details)}
      </div>
    </div>
  )

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px' }}>Similar Practice</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px', lineHeight: 1.6 }}>
        Select a source question and AptiRecall will generate a similar practice question with a step-by-step solution.
      </p>

      {error && (
        <p style={{ margin: '0 0 16px', fontSize: '14px', color: '#dc2626' }}>{error}</p>
      )}

      {status === 'loading_questions' && (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>Loading questions...</p>
        </div>
      )}

      {status === 'selecting' && !result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '8px' }}>Select a Source Question</h2>
          {questions.length === 0 ? (
            <p style={{ color: 'var(--text)', fontSize: '14px' }}>No questions available.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {questions.map((question) => (
                <div
                  key={question.id}
                  onClick={() => handleSelectSource(question)}
                  style={{
                    padding: '16px',
                    borderRadius: '8px',
                    border: sourceQuestion?.id === question.id ? '2px solid var(--accent)' : '1px solid var(--border)',
                    background: sourceQuestion?.id === question.id ? 'var(--accent-bg)' : 'var(--bg)',
                    cursor: 'pointer',
                  }}
                >
                  <p style={{ margin: '0 0 8px', fontSize: '14px', lineHeight: 1.6 }}>{question.question_text}</p>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: 'var(--text)' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                      {question.topic_name}
                    </span>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)' }}>
                      {question.problem_type_name}
                    </span>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)', textTransform: 'capitalize' }}>
                      {question.difficulty}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {sourceQuestion && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button
                type="button"
                onClick={handleGenerate}
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
                Generate Similar Question
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
                Clear Selection
              </button>
            </div>
          )}
        </div>
      )}

      {status === 'generating' && (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>AptiRecall is generating a similar practice question...</p>
        </div>
      )}

      {status === 'result' && result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ padding: '16px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--accent-bg)' }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Source Question</div>
            <div style={{ lineHeight: 1.6 }}>{sourceQuestion?.question_text}</div>
          </div>
          {renderSolution(result)}
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
              alignSelf: 'flex-start',
            }}
          >
            Practice Another
          </button>
        </div>
      )}
    </div>
  )
}
