import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { topicApi } from '../services/api'
import type { TopicDetail } from '../types/api'

export default function TopicDetail() {
  const { id } = useParams<{ id: string }>()
  const [topic, setTopic] = useState<TopicDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const data = await topicApi.get(Number(id))
        setTopic(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load topic')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) {
    return <p>Loading topic...</p>
  }

  if (error || !topic) {
    return (
      <div>
        <p style={{ color: '#ef4444' }}>{error || 'Topic not found'}</p>
        <Link to="/topics" style={{ color: 'var(--accent)', textDecoration: 'none', marginTop: '12px', display: 'inline-block' }}>
          Back to Topics
        </Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/topics" style={{ color: 'var(--accent)', textDecoration: 'none', fontSize: '14px', marginBottom: '16px', display: 'inline-block' }}>
        ← Back to Topics
      </Link>

      <h1 style={{ marginBottom: '8px' }}>{topic.name}</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px' }}>{topic.description || 'No description available'}</p>

      {topic.subtopics.length > 0 && (
        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Subtopics</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {topic.subtopics.map((subtopic) => (
              <div
                key={subtopic.id}
                style={{
                  padding: '12px 16px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ fontWeight: 500 }}>{subtopic.name}</div>
                {subtopic.description && (
                  <div style={{ fontSize: '14px', color: 'var(--text)', marginTop: '4px' }}>
                    {subtopic.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {topic.problem_types.length > 0 && (
        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Problem Types</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {topic.problem_types.map((pt) => (
              <div
                key={pt.id}
                style={{
                  padding: '12px 16px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ fontWeight: 500 }}>{pt.name}</div>
                {pt.description && (
                  <div style={{ fontSize: '14px', color: 'var(--text)', marginTop: '4px' }}>
                    {pt.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {topic.formulas.length > 0 && (
        <section style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Formulas</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {topic.formulas.map((formula) => (
              <div
                key={formula.id}
                style={{
                  padding: '12px 16px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ fontWeight: 500 }}>{formula.name}</div>
                {formula.formula_latex && (
                  <code style={{
                    display: 'block',
                    marginTop: '8px',
                    padding: '8px',
                    background: 'var(--code-bg)',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}>
                    {formula.formula_latex}
                  </code>
                )}
                {formula.description && (
                  <div style={{ fontSize: '14px', color: 'var(--text)', marginTop: '8px' }}>
                    {formula.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <div style={{ marginTop: '32px' }}>
        <Link
          to={`/questions?topic=${topic.id}`}
          style={{
            display: 'inline-block',
            padding: '10px 16px',
            borderRadius: '6px',
            background: 'var(--accent)',
            color: '#fff',
            textDecoration: 'none',
            fontSize: '14px',
          }}
        >
          Practice Questions
        </Link>
      </div>
    </div>
  )
}
