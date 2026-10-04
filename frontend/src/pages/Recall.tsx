import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { recallApi } from '../services/api'
import type { RecallRecord, RecallAnalytics } from '../types/api'

type RecallStatus = 'loading' | 'ready' | 'error'

function formatDate(value: string | null): string {
  if (!value) return 'Never'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Never'
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function scorePercent(value: number): number {
  return Math.round(value * 100)
}

export default function Recall() {
  const [status, setStatus] = useState<RecallStatus>('loading')
  const [error, setError] = useState('')

  const [schedule, setSchedule] = useState<RecallRecord[]>([])
  const [weakTopics, setWeakTopics] = useState<RecallRecord[]>([])
  const [analytics, setAnalytics] = useState<RecallAnalytics | null>(null)

  const [submitting, setSubmitting] = useState(false)
  const [submitAttemptId, setSubmitAttemptId] = useState('')
  const [submitResult, setSubmitResult] = useState('')
  const [submitError, setSubmitError] = useState('')

  useEffect(() => {
    const loadAll = async () => {
      setError('')
      setStatus('loading')

      try {
        const [scheduleData, weakData, analyticsData] = await Promise.all([
          recallApi.getSchedule(),
          recallApi.getWeakTopics(),
          recallApi.getAnalytics(),
        ])

        setSchedule(scheduleData)
        setWeakTopics(weakData)
        setAnalytics(analyticsData)
        setStatus('ready')
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load recall data.'
        if (message.includes('Network') || message.includes('network')) {
          setError('Connection error. Please check your internet and try again.')
        } else {
          setError(message)
        }
        setStatus('error')
      }
    }

    loadAll()
  }, [])

  const handleSubmitAttempt = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = submitAttemptId.trim()
    if (!trimmed) return

    const attemptId = Number(trimmed)
    if (!Number.isInteger(attemptId) || attemptId <= 0) {
      setSubmitError('Please enter a valid attempt ID.')
      setSubmitResult('')
      return
    }

    setSubmitting(true)
    setSubmitError('')
    setSubmitResult('')

    try {
      const record = await recallApi.submit(attemptId)
      setSubmitResult(`Recall updated for record #${record.id}. Practice count: ${record.practice_count}.`)
      setSubmitAttemptId('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit recall attempt.'
      if (message.includes('not found') || message.includes('404')) {
        setSubmitError('Completed attempt not found. Make sure the attempt is completed and belongs to you.')
      } else if (message.includes('VALIDATION_ERROR') || message.includes('attempt_id')) {
        setSubmitError(message)
      } else if (message.includes('Network') || message.includes('network')) {
        setSubmitError('Connection error. Please check your internet and try again.')
      } else {
        setSubmitError(message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const renderSchedule = () => {
    if (schedule.length === 0) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>No recall questions are due right now.</p>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {schedule.map((record) => (
          <div
            key={record.id}
            style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '240px' }}>
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px', lineHeight: 1.5 }}>
                  {record.question ? (
                    <Link
                      to={`/questions/${record.question}`}
                      style={{ color: 'var(--accent)', textDecoration: 'none' }}
                    >
                      Question #{record.question}
                    </Link>
                  ) : (
                    <span>Topic #{record.topic}</span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', fontSize: '12px', color: 'var(--text)', marginBottom: '8px' }}>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                    Topic #{record.topic}
                  </span>
                  {record.problem_type && (
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)' }}>
                      Problem Type #{record.problem_type}
                    </span>
                  )}
                  {record.difficulty_at_practice && (
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'var(--social-bg)',
                        textTransform: 'capitalize',
                      }}
                    >
                      {record.difficulty_at_practice}
                    </span>
                  )}
                  {record.is_weak && (
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#fef2f2', color: '#dc2626', fontSize: '12px' }}>
                      Weak
                    </span>
                  )}
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text)', lineHeight: 1.6 }}>
                  <div>Next practice: {formatDate(record.next_practice_at)}</div>
                  {record.last_practiced && (
                    <div>Last practiced: {formatDate(record.last_practiced)}</div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-end', minWidth: '120px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Recall Score</div>
                <div style={{ fontSize: '20px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {scorePercent(record.recall_score)}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Accuracy</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {scorePercent(record.accuracy_score)}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Practices</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {record.practice_count}
                </div>
              </div>
            </div>

            {record.question && (
              <div style={{ marginTop: '12px' }}>
                <Link
                  to={`/questions/${record.question}`}
                  style={{
                    display: 'inline-block',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'var(--accent)',
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: 500,
                    textDecoration: 'none',
                    cursor: 'pointer',
                  }}
                >
                  Practice This Question
                </Link>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderWeakTopics = () => {
    if (weakTopics.length === 0) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>No weak topics detected. Keep practicing!</p>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {weakTopics.map((record) => (
          <div
            key={record.id}
            style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '240px' }}>
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px', lineHeight: 1.5 }}>
                  {record.question ? (
                    <Link
                      to={`/questions/${record.question}`}
                      style={{ color: 'var(--accent)', textDecoration: 'none' }}
                    >
                      Question #{record.question}
                    </Link>
                  ) : (
                    <span>Topic #{record.topic}</span>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', fontSize: '12px', color: 'var(--text)', marginBottom: '8px' }}>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                    Topic #{record.topic}
                  </span>
                  {record.problem_type && (
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)' }}>
                      Problem Type #{record.problem_type}
                    </span>
                  )}
                  {record.difficulty_at_practice && (
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'var(--social-bg)',
                        textTransform: 'capitalize',
                      }}
                    >
                      {record.difficulty_at_practice}
                    </span>
                  )}
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#fef2f2', color: '#dc2626', fontSize: '12px' }}>
                    Weak
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text)', lineHeight: 1.6 }}>
                  <div>Next practice: {formatDate(record.next_practice_at)}</div>
                  {record.last_practiced && (
                    <div>Last practiced: {formatDate(record.last_practiced)}</div>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-end', minWidth: '120px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Recall Score</div>
                <div style={{ fontSize: '20px', fontWeight: 500, color: '#dc2626' }}>
                  {scorePercent(record.recall_score)}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Accuracy</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {scorePercent(record.accuracy_score)}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Practices</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {record.practice_count}
                </div>
              </div>
            </div>

            {record.question && (
              <div style={{ marginTop: '12px' }}>
                <Link
                  to={`/questions/${record.question}`}
                  style={{
                    display: 'inline-block',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'var(--accent)',
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: 500,
                    textDecoration: 'none',
                    cursor: 'pointer',
                  }}
                >
                  Practice This Question
                </Link>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderAnalytics = () => {
    if (!analytics) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>Analytics data is not available.</p>
        </div>
      )
    }

    const items = [
      { label: 'Total Topics', value: String(analytics.total_topics) },
      { label: 'Weak', value: String(analytics.weak_count), color: '#dc2626' },
      { label: 'Moderate', value: String(analytics.moderate_count), color: '#d97706' },
      { label: 'Strong', value: String(analytics.strong_count), color: '#16a34a' },
      { label: 'Average Recall', value: `${scorePercent(analytics.average_recall_score)}%` },
    ]

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '16px',
        }}
      >
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
            }}
          >
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '8px' }}>{item.label}</div>
            <div style={{ fontSize: '28px', fontWeight: 500, color: item.color || 'var(--text-h)' }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderSubmit = () => (
    <div style={{ maxWidth: '520px' }}>
      <p style={{ color: 'var(--text)', marginBottom: '16px', lineHeight: 1.6 }}>
        After solving a question through AptiRecall, you can submit the completed attempt here to update your recall record.
      </p>

      <form onSubmit={handleSubmitAttempt} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
          <label htmlFor="recall-attempt-id" style={{ fontSize: '14px', fontWeight: 500 }}>
            Completed Attempt ID
          </label>
          <input
            id="recall-attempt-id"
            type="number"
            min="1"
            value={submitAttemptId}
            onChange={(e) => setSubmitAttemptId(e.target.value)}
            placeholder="Enter the attempt ID from your solve result"
            disabled={submitting}
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
              color: 'var(--text-h)',
              fontSize: '14px',
              opacity: submitting ? 0.7 : 1,
            }}
          />
        </div>

        {submitError && (
          <p style={{ margin: 0, fontSize: '14px', color: '#dc2626' }}>{submitError}</p>
        )}

        {submitResult && (
          <p style={{ margin: 0, fontSize: '14px', color: '#16a34a' }}>{submitResult}</p>
        )}

        <button
          type="submit"
          disabled={submitting || !submitAttemptId.trim()}
          style={{
            padding: '10px 20px',
            borderRadius: '6px',
            border: 'none',
            background: 'var(--accent)',
            color: '#fff',
            fontSize: '14px',
            fontWeight: 500,
            cursor: submitting || !submitAttemptId.trim() ? 'not-allowed' : 'pointer',
            opacity: submitting || !submitAttemptId.trim() ? 0.7 : 1,
            alignSelf: 'flex-start',
          }}
        >
          {submitting ? 'Submitting...' : 'Submit Attempt'}
        </button>
      </form>
    </div>
  )

  const renderContent = () => {
    if (status === 'loading') {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>Loading recall data...</p>
        </div>
      )
    }

    if (status === 'error') {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center' }}>
          <p style={{ color: '#dc2626', marginBottom: '12px' }}>{error}</p>
          <button
            type="button"
            onClick={() => {
              setError('')
              setStatus('loading')
              recallApi.getSchedule()
                .then((data) => { setSchedule(data); return recallApi.getWeakTopics() })
                .then((data) => { setWeakTopics(data); return recallApi.getAnalytics() })
                .then((data) => { setAnalytics(data); setStatus('ready') })
                .catch((err) => {
                  const message = err instanceof Error ? err.message : 'Failed to load recall data.'
                  setError(message)
                  setStatus('error')
                })
            }}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text)',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Due for Practice</h2>
          {renderSchedule()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Weak Topics</h2>
          {renderWeakTopics()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Recall Analytics</h2>
          {renderAnalytics()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Submit Completed Attempt</h2>
          {renderSubmit()}
        </section>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '960px' }}>
      <h1 style={{ marginBottom: '8px' }}>Adaptive Recall</h1>
      <p style={{ color: 'var(--text)', marginBottom: '24px', lineHeight: 1.6 }}>
        Review questions due for spaced repetition and track your weak areas.
      </p>

      {renderContent()}
    </div>
  )
}
