import { useEffect, useState } from 'react'
import { progressApi } from '../services/api'
import type { ProgressDashboard, ProgressAccuracy, ProgressTopicBreakdown, ProgressRecentMistake } from '../types/api'

type ProgressStatus = 'loading' | 'ready' | 'error'

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function formatSeconds(value: number | null): string {
  if (value === null || value === undefined) return 'N/A'
  if (value < 60) return `${Math.round(value)}s`
  const minutes = Math.floor(value / 60)
  const seconds = Math.round(value % 60)
  return `${minutes}m ${seconds}s`
}

function formatDate(value: string | null): string {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function Progress() {
  const [status, setStatus] = useState<ProgressStatus>('loading')
  const [error, setError] = useState('')

  const [dashboard, setDashboard] = useState<ProgressDashboard | null>(null)
  const [accuracy, setAccuracy] = useState<ProgressAccuracy | null>(null)
  const [topics, setTopics] = useState<ProgressTopicBreakdown[]>([])
  const [mistakes, setMistakes] = useState<ProgressRecentMistake[]>([])

  useEffect(() => {
    const loadAll = async () => {
      setError('')
      setStatus('loading')

      try {
        const [dashboardData, accuracyData, topicsData, mistakesData] = await Promise.all([
          progressApi.getDashboard(),
          progressApi.getAccuracy(),
          progressApi.getTopics(),
          progressApi.getMistakes(),
        ])

        setDashboard(dashboardData)
        setAccuracy(accuracyData)
        setTopics(topicsData)
        setMistakes(mistakesData)
        setStatus('ready')
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load progress data.'
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

  const renderOverview = () => {
    if (!dashboard) return null

    const items = [
      { label: 'Total Attempts', value: String(dashboard.total_attempts) },
      { label: 'Completed', value: String(dashboard.completed_attempts) },
      { label: 'Correct', value: String(dashboard.correct_attempts), color: '#16a34a' },
      { label: 'Incorrect', value: String(dashboard.incorrect_attempts), color: '#dc2626' },
      { label: 'Accuracy', value: formatPercent(dashboard.accuracy), color: '#2563eb' },
      { label: 'Topics Practiced', value: String(dashboard.topics_practiced) },
      { label: 'Questions Solved', value: String(dashboard.questions_solved) },
      { label: 'Avg Time', value: formatSeconds(dashboard.average_time_taken_seconds) },
      { label: 'Hints Used', value: String(dashboard.total_hints_used) },
      { label: 'Retries', value: String(dashboard.total_retry_attempts) },
    ]

    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
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

  const renderAccuracy = () => {
    if (!accuracy) return null

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '16px',
          }}
        >
          <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)' }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '8px' }}>Overall Accuracy</div>
            <div style={{ fontSize: '28px', fontWeight: 500, color: '#2563eb' }}>
              {formatPercent(accuracy.overall.accuracy)}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>
              {accuracy.overall.correct} / {accuracy.overall.total}
            </div>
          </div>
          <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)' }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '8px' }}>Correct</div>
            <div style={{ fontSize: '28px', fontWeight: 500, color: '#16a34a' }}>
              {accuracy.overall.correct}
            </div>
          </div>
          <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)' }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '8px' }}>Incorrect</div>
            <div style={{ fontSize: '28px', fontWeight: 500, color: '#dc2626' }}>
              {accuracy.overall.incorrect}
            </div>
          </div>
        </div>

        {accuracy.by_difficulty.some((d) => d.total > 0) && (
          <div>
            <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>By Difficulty</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {accuracy.by_difficulty
                .filter((d) => d.total > 0)
                .map((item) => (
                  <div
                    key={item.difficulty}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span
                          style={{
                            padding: '2px 10px',
                            borderRadius: '4px',
                            background: 'var(--accent-bg)',
                            color: 'var(--accent)',
                            fontSize: '12px',
                            textTransform: 'capitalize',
                          }}
                        >
                          {item.difficulty}
                        </span>
                        <span style={{ fontSize: '14px', color: 'var(--text)' }}>
                          {item.correct} / {item.total}
                        </span>
                      </div>
                      <span style={{ fontSize: '18px', fontWeight: 500, color: '#2563eb' }}>
                        {formatPercent(item.accuracy)}
                      </span>
                    </div>
                    <div style={{ marginTop: '8px', height: '6px', borderRadius: '3px', background: 'var(--border)', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${item.accuracy * 100}%`,
                          height: '100%',
                          borderRadius: '3px',
                          background: '#16a34a',
                          transition: 'width 0.3s',
                        }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {accuracy.by_topic.length > 0 && (
          <div>
            <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>By Topic</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {accuracy.by_topic.map((item) => (
                <div
                  key={item.topic_id}
                  style={{
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '14px', fontWeight: 500 }}>{item.topic_name}</span>
                      <span style={{ fontSize: '12px', color: 'var(--text)' }}>
                        {item.correct} / {item.total}
                      </span>
                    </div>
                    <span style={{ fontSize: '18px', fontWeight: 500, color: '#2563eb' }}>
                      {formatPercent(item.accuracy)}
                    </span>
                  </div>
                  <div style={{ marginTop: '8px', height: '6px', borderRadius: '3px', background: 'var(--border)', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${item.accuracy * 100}%`,
                        height: '100%',
                        borderRadius: '3px',
                        background: '#16a34a',
                        transition: 'width 0.3s',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderTopics = () => {
    if (topics.length === 0) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>No topic data available yet. Start solving questions to see topic performance.</p>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {topics.map((topic) => (
          <div
            key={topic.topic_id}
            style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'var(--bg)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '240px' }}>
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>{topic.topic_name}</div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', fontSize: '12px', color: 'var(--text)' }}>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                    {topic.attempts} attempts
                  </span>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#dcfce7', color: '#16a34a' }}>
                    {topic.correct} correct
                  </span>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#fef2f2', color: '#dc2626' }}>
                    {topic.incorrect} incorrect
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-end', minWidth: '120px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Accuracy</div>
                <div style={{ fontSize: '20px', fontWeight: 500, color: '#2563eb' }}>
                  {formatPercent(topic.accuracy)}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Avg Time</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {formatSeconds(topic.average_time_taken_seconds)}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text)' }}>Hints</div>
                <div style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-h)' }}>
                  {topic.hints_used}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderMistakes = () => {
    if (mistakes.length === 0) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>No mistakes recorded yet. Keep practicing!</p>
        </div>
      )
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {mistakes.map((mistake) => (
          <div
            key={mistake.attempt_id}
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
                  {mistake.question_text}
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', fontSize: '12px', color: 'var(--text)' }}>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                    {mistake.topic_name}
                  </span>
                  <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)', textTransform: 'capitalize' }}>
                    {mistake.difficulty}
                  </span>
                </div>
                {mistake.user_answer && (
                  <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '8px' }}>
                    <strong>Your answer:</strong> {mistake.user_answer}
                  </div>
                )}
                <div style={{ fontSize: '12px', color: 'var(--text)', marginTop: '4px' }}>
                  {formatDate(mistake.completed_at)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderContent = () => {
    if (status === 'loading') {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>Loading progress data...</p>
        </div>
      )
    }

    if (status === 'error') {
      const isUnavailable = error.includes('501') || error.toLowerCase().includes('not implemented')

      if (isUnavailable) {
        return (
          <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
            <p style={{ fontSize: '18px', marginBottom: '8px' }}>Progress analytics are not available yet</p>
            <p style={{ color: 'var(--text)', marginBottom: '16px' }}>
              Backend progress endpoints are still under development. This section will be enabled once the server-side analytics are implemented.
            </p>
            <button
              type="button"
              onClick={() => {
                setError('')
                setStatus('loading')
                progressApi.getDashboard()
                  .then((d) => { setDashboard(d); return progressApi.getAccuracy() })
                  .then((a) => { setAccuracy(a); return progressApi.getTopics() })
                  .then((t) => { setTopics(t); return progressApi.getMistakes() })
                  .then((m) => { setMistakes(m); setStatus('ready') })
                  .catch((err) => {
                    const message = err instanceof Error ? err.message : 'Failed to load progress data.'
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
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center' }}>
          <p style={{ color: '#dc2626', marginBottom: '12px' }}>{error}</p>
          <button
            type="button"
            onClick={() => {
              setError('')
              setStatus('loading')
              progressApi.getDashboard()
                .then((d) => { setDashboard(d); return progressApi.getAccuracy() })
                .then((a) => { setAccuracy(a); return progressApi.getTopics() })
                .then((t) => { setTopics(t); return progressApi.getMistakes() })
                .then((m) => { setMistakes(m); setStatus('ready') })
                .catch((err) => {
                  const message = err instanceof Error ? err.message : 'Failed to load progress data.'
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
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Overview</h2>
          {renderOverview()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Performance</h2>
          {renderAccuracy()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Topic Performance</h2>
          {renderTopics()}
        </section>

        <section>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Recent Mistakes</h2>
          {renderMistakes()}
        </section>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '960px' }}>
      <h1 style={{ marginBottom: '8px' }}>Progress</h1>
      <p style={{ color: 'var(--text)', marginBottom: '24px', lineHeight: 1.6 }}>
        Track your aptitude-learning progress, accuracy, and performance by topic.
      </p>

      {renderContent()}
    </div>
  )
}
