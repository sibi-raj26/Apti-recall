import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { topicApi } from '../services/api'
import type { Topic } from '../types/api'

export default function Topics() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const data = await topicApi.list()
        setTopics(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load topics')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <p>Loading topics...</p>
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
      <h1 style={{ marginBottom: '24px' }}>Topics</h1>

      {topics.length === 0 ? (
        <p>No topics available.</p>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '16px',
        }}>
          {topics.map((topic) => (
            <Link
              key={topic.id}
              to={`/topics/${topic.id}`}
              style={{
                display: 'block',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                textDecoration: 'none',
                color: 'inherit',
                transition: 'box-shadow 0.2s',
              }}
            >
              <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>{topic.name}</h3>
              <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.5 }}>
                {topic.description || 'No description available'}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
