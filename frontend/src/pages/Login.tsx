import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page" style={{ padding: '2rem' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '8px' }}>AptiRecall</h1>
      <p style={{ textAlign: 'center', color: 'var(--text)', marginBottom: '32px' }}>
        Sign in to your account
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {error && (
          <div style={{
            padding: '12px',
            borderRadius: '6px',
            background: 'rgba(239, 68, 68, 0.1)',
            color: '#ef4444',
            fontSize: '14px',
          }}>
            {error}
          </div>
        )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                  <label htmlFor="login-email" style={{ fontSize: '14px', fontWeight: 500 }}>Email</label>
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    style={{
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg)',
                      color: 'var(--text-h)',
                      fontSize: '14px',
                    }}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                  <label htmlFor="login-password" style={{ fontSize: '14px', fontWeight: 500 }}>Password</label>
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    style={{
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      background: 'var(--bg)',
                      color: 'var(--text-h)',
                      fontSize: '14px',
                    }}
                  />
                </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px',
            borderRadius: '6px',
            border: 'none',
            background: 'var(--accent)',
            color: '#fff',
            fontSize: '14px',
            fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>

        <p style={{ textAlign: 'center', fontSize: '14px', color: 'var(--text)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
            Register
          </Link>
        </p>
      </form>
    </div>
  )
}
