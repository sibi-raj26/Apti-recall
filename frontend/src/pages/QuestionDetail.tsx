import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { questionApi } from '../services/api'
import type { QuestionDetail } from '../types/api'

export default function QuestionDetail() {
  const { id } = useParams<{ id: string }>()
  const [question, setQuestion] = useState<QuestionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const data = await questionApi.get(Number(id))
        setQuestion(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load question')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) {
    return <p>Loading question...</p>
  }

  if (error || !question) {
    return (
      <div>
        <p style={{ color: '#ef4444' }}>{error || 'Question not found'}</p>
        <Link to="/questions" style={{ color: 'var(--accent)', textDecoration: 'none', marginTop: '12px', display: 'inline-block' }}>
          Back to Questions
        </Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/questions" style={{ color: 'var(--accent)', textDecoration: 'none', fontSize: '14px', marginBottom: '16px', display: 'inline-block' }}>
        ← Back to Questions
      </Link>

      <h1 style={{ marginBottom: '8px' }}>Question</h1>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', fontSize: '12px', color: 'var(--text)' }}>
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

      <div style={{
        padding: '24px',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        marginBottom: '24px',
      }}>
        <p style={{ fontSize: '16px', lineHeight: 1.6, margin: 0 }}>
          {question.question_text}
        </p>
      </div>

      {question.solution_steps && question.solution_steps.length > 0 && (
        <section style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Solution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {question.solution_steps.map((step) => (
              <div
                key={step.id}
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>
                  Step {step.step_number}: {step.title}
                </div>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.5 }}>
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {question.shortcuts && question.shortcuts.length > 0 && (
        <section style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Shortcuts</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {question.shortcuts.map((shortcut) => (
              <div
                key={shortcut.id}
                style={{
                  padding: '16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>
                  {shortcut.title}
                </div>
                <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.5 }}>
                  {shortcut.description}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <div style={{ marginTop: '24px' }}>
        <p style={{ fontSize: '14px', color: 'var(--text)' }}>
          <strong>Correct Answer:</strong> {question.correct_answer}
        </p>
      </div>
    </div>
  )
}
