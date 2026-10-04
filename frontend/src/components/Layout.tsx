import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/topics', label: 'Topics' },
  { path: '/questions', label: 'Questions' },
  { path: '/solve', label: 'AI Solver' },
  { path: '/solve/image', label: 'Image Solver' },
  { path: '/practice', label: 'Practice' },
  { path: '/recall', label: 'Adaptive Recall' },
  { path: '/progress', label: 'Progress' },
  { path: '/profile', label: 'Profile' },
  { path: '/admin', label: 'Admin' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: '240px',
        borderRight: '1px solid var(--border)',
        padding: '24px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}>
        <div style={{ marginBottom: '24px', padding: '0 8px' }}>
          <Link to="/dashboard" style={{ textDecoration: 'none', color: 'inherit' }}>
            <h2 style={{ margin: 0, fontSize: '20px' }}>AptiRecall</h2>
          </Link>
          <p style={{ fontSize: '12px', color: 'var(--text)', margin: '4px 0 0' }}>
            AI-Powered Aptitude Learning
          </p>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: location.pathname === item.path ? 'var(--text-h)' : 'var(--text)',
                background: location.pathname === item.path ? 'var(--accent-bg)' : 'transparent',
                fontSize: '14px',
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', marginTop: '16px' }}>
          <div style={{ padding: '0 8px', marginBottom: '8px', fontSize: '14px' }}>
            {user?.email}
          </div>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: 'transparent',
              color: 'var(--text)',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Logout
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, padding: '32px', overflow: 'auto' }}>
        {children}
      </main>
    </div>
  )
}
