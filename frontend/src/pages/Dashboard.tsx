import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { user } = useAuth()

  return (
    <div>
      <h1 style={{ marginBottom: '8px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px' }}>
        Welcome back, {user?.username || user?.email}!
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '32px',
      }}>
        <Link to="/topics" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>Topics</h3>
            <p style={{ margin: 0, fontSize: '28px', fontWeight: 500 }}>Browse</p>
          </div>
        </Link>
        <Link to="/questions" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>Questions</h3>
            <p style={{ margin: 0, fontSize: '28px', fontWeight: 500 }}>Practice</p>
          </div>
        </Link>
        <Link to="/solve" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>AI Solver</h3>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)' }}>Solve questions with AI</p>
          </div>
        </Link>
        <Link to="/solve/image" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>Image Solver</h3>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)' }}>Upload and solve images</p>
          </div>
        </Link>
        <Link to="/practice" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>Similar Practice</h3>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)' }}>Generate practice questions</p>
          </div>
        </Link>
        <Link to="/recall" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            background: 'var(--bg)',
          }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '14px', color: 'var(--text)' }}>Adaptive Recall</h3>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)' }}>Review and retain</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
