import { useEffect, useState } from 'react'
import { topicApi } from '../services/api'
import { adminApi } from '../services/api'
import type { Topic, Question } from '../types/api'

type Tab = 'topics' | 'questions' | 'dashboard' | 'users' | 'performance'

export default function Admin() {
  const [tab, setTab] = useState<Tab>('topics')
  const [topics, setTopics] = useState<Topic[]>([])
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadContent = async () => {
    setError('')
    setLoading(true)
    try {
      if (tab === 'topics') {
        const data = await topicApi.list()
        setTopics(data)
      } else if (tab === 'questions') {
        const result = await adminApi.listQuestions()
        setQuestions(result as unknown as Question[])
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load data.'
      if (message.includes('Network') || message.toLowerCase().includes('network')) {
        setError('Connection error. Please check your internet and try again.')
      } else {
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadContent()
  }, [tab])

  const isAdminUnavailable = (message: string) => {
    return message.includes('501') || message.toLowerCase().includes('not implemented')
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'topics', label: 'Topics' },
    { key: 'questions', label: 'Questions' },
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'users', label: 'Users' },
    { key: 'performance', label: 'Performance' },
  ]

  const renderUnavailable = (title: string) => (
    <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
      <p style={{ fontSize: '18px', marginBottom: '8px' }}>{title} are not available yet</p>
      <p style={{ color: 'var(--text)', marginBottom: '16px' }}>
        Backend admin endpoints are still under development. This section will be enabled once the server-side admin features are implemented.
      </p>
      <button
        type="button"
        onClick={loadContent}
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

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center', color: 'var(--text)' }}>
          <p>Loading...</p>
        </div>
      )
    }

    if (error) {
      if (isAdminUnavailable(error) && (tab === 'dashboard' || tab === 'users' || tab === 'performance')) {
        const titles: Record<string, string> = {
          dashboard: 'Admin dashboard',
          users: 'User management',
          performance: 'Performance analytics',
        }
        return renderUnavailable(titles[tab])
      }

      return (
        <div style={{ padding: '24px', borderRadius: '8px', border: '1px solid var(--border)', textAlign: 'center' }}>
          <p style={{ color: '#dc2626', marginBottom: '12px' }}>{error}</p>
          <button
            type="button"
            onClick={loadContent}
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

    if (tab === 'topics') {
      if (topics.length === 0) {
        return <p>No topics available.</p>
      }
      return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {topics.map((topic) => (
            <div key={topic.id} style={{ padding: '20px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)' }}>
              <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>{topic.name}</h3>
              <p style={{ margin: 0, fontSize: '14px', color: 'var(--text)', lineHeight: 1.5 }}>
                {topic.description || 'No description available'}
              </p>
              <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-bg)', color: 'var(--accent)', fontSize: '12px', textTransform: 'capitalize' }}>
                  {topic.is_active ? 'Active' : 'Inactive'}
                </span>
                <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'var(--social-bg)', fontSize: '12px', color: 'var(--text)' }}>
                  Order: {topic.order}
                </span>
              </div>
            </div>
          ))}
        </div>
      )
    }

    if (tab === 'questions') {
      if (questions.length === 0) {
        return <p>No questions available.</p>
      }
      return (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left' }}>
              <th style={{ padding: '12px 8px' }}>ID</th>
              <th style={{ padding: '12px 8px' }}>Question</th>
              <th style={{ padding: '12px 8px' }}>Topic</th>
              <th style={{ padding: '12px 8px' }}>Problem Type</th>
              <th style={{ padding: '12px 8px' }}>Difficulty</th>
              <th style={{ padding: '12px 8px' }}>Status</th>
            </tr>
          </thead>
            <tbody>
              {questions.map((question) => (
                <tr key={question.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 8px' }}>{question.id}</td>
                  <td style={{ padding: '12px 8px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{question.question_text}</td>
                  <td style={{ padding: '12px 8px' }}>{question.topic_name}</td>
                  <td style={{ padding: '12px 8px' }}>{question.problem_type_name}</td>
                  <td style={{ padding: '12px 8px', textTransform: 'capitalize' }}>{question.difficulty}</td>
                  <td style={{ padding: '12px 8px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: question.is_active ? '#dcfce7' : '#fef2f2', color: question.is_active ? '#16a34a' : '#dc2626', fontSize: '12px', textTransform: 'capitalize' }}>
                      {question.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }

    if (tab === 'dashboard') {
      return renderUnavailable('Admin dashboard')
    }

    if (tab === 'users') {
      return renderUnavailable('User management')
    }

    if (tab === 'performance') {
      return renderUnavailable('Performance analytics')
    }

    return null
  }

  return (
    <div style={{ maxWidth: '960px' }}>
      <h1 style={{ marginBottom: '8px' }}>Admin</h1>
      <p style={{ color: 'var(--text)', marginBottom: '24px', lineHeight: 1.6 }}>
        Manage learning content and review platform data.
      </p>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
        {tabs.map((item) => (
          <button
            key={item.key}
            onClick={() => setTab(item.key)}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: tab === item.key ? 'var(--accent-bg)' : 'transparent',
              color: tab === item.key ? 'var(--accent)' : 'var(--text)',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: tab === item.key ? 500 : 400,
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}
