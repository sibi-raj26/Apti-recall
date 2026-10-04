import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { questionApi } from '../services/api'
import type { Question } from '../types/api'

export default function Questions() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchParams] = useSearchParams()
  const topicFilter = searchParams.get('topic')

  useEffect(() => {
    const load = async () => {
      try {
        const params: Record<string, number | string> = {}
        if (topicFilter) {
          params.topic = Number(topicFilter)
        }
        const result = await questionApi.list(params)
        setQuestions(result.data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load questions')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [topicFilter])

  if (loading) {
    return <p>Loading questions...</p>
  }

  if (error) {
    return (
      <div>
        <p style={{ color: '#ef4444' }}>{error}</p>
        <button onClick={() => window.location.reload()} style={{ marginTop: '12px', padding: '8px 16px' }}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '24px' }}>
        {topicFilter ? 'Topic Questions' : 'Questions'}
      </h1>

      {questions.length === 0 ? (
        <p>No questions available.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {questions.map((question) => (
            <Link
              key={question.id}
              to={`/questions/${question.id}`}
              style={{
                display: 'block',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ margin: '0 0 8px', fontSize: '14px', lineHeight: 1.6 }}>
                    {question.question_text}
                  </p>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: 'var(--text)' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'var(--accent-bg)',
                      color: 'var(--accent)',
                    }}>
                      {question.topic_name}
                    </span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'var(--social-bg)',
                    }}>
                      {question.problem_type_name}
                    </span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'var(--social-bg)',
                      textTransform: 'capitalize',
                    }}>
                      {question.difficulty}
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
