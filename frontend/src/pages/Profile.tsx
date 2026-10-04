import { useState, useEffect } from 'react'
import { authApi } from '../services/api'
import type { User, UserProfile, ChangePasswordRequest } from '../types/api'

type Tab = 'account' | 'profile' | 'password'

export default function Profile() {
  const [activeTab, setActiveTab] = useState<Tab>('account')
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const [preferredLanguage, setPreferredLanguage] = useState('en')
  const [passwordForm, setPasswordForm] = useState<ChangePasswordRequest>({
    current_password: '',
    new_password: '',
    new_password2: '',
  })

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, profileData] = await Promise.all([
          authApi.getCurrentUser(),
          authApi.getProfile(),
        ])
        setUser(userData)
        setProfile(profileData)
        setPreferredLanguage(profileData.preferred_language)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile data.')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)
    try {
      const updated = await authApi.updateProfile({ preferred_language: preferredLanguage })
      setProfile(updated)
      setMessage('Profile updated successfully.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)
    try {
      await authApi.changePassword(passwordForm)
      setMessage('Password changed successfully.')
      setPasswordForm({ current_password: '', new_password: '', new_password2: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password.')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = async () => {
    const refresh = localStorage.getItem('aptirecall_refresh')
    if (refresh) {
      try {
        await authApi.logout(refresh)
      } catch {
        // ignore logout errors
      }
    }
    localStorage.removeItem('aptirecall_access')
    localStorage.removeItem('aptirecall_refresh')
    window.location.href = '/login'
  }

  if (loading) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <p>Loading profile...</p>
      </div>
    )
  }

  if (error && !user) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <p style={{ color: '#dc2626' }}>{error}</p>
      </div>
    )
  }

  const formatDate = (value?: string) => {
    if (!value) return 'Never'
    return new Date(value).toLocaleDateString()
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px' }}>Profile & Settings</h1>
      <p style={{ color: 'var(--text)', marginBottom: '32px', lineHeight: 1.6 }}>
        Manage your account information, preferences, and security.
      </p>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        {(['account', 'profile', 'password'] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => { setActiveTab(tab); setError(''); setMessage('') }}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              background: activeTab === tab ? 'var(--accent-bg)' : 'transparent',
              color: activeTab === tab ? 'var(--text-h)' : 'var(--text)',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              textTransform: 'capitalize',
            }}
          >
            {tab === 'account' ? 'Account' : tab === 'profile' ? 'Profile' : 'Password'}
          </button>
        ))}
      </div>

      {message && (
        <div style={{
          padding: '12px',
          borderRadius: '6px',
          background: 'rgba(22, 163, 74, 0.1)',
          color: '#16a34a',
          fontSize: '14px',
          marginBottom: '24px',
        }}>
          {message}
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px',
          borderRadius: '6px',
          background: 'rgba(239, 68, 68, 0.1)',
          color: '#dc2626',
          fontSize: '14px',
          marginBottom: '24px',
        }}>
          {error}
        </div>
      )}

      {activeTab === 'account' && user && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Email</div>
            <div style={{ fontWeight: 500 }}>{user.email}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Username</div>
            <div style={{ fontWeight: 500 }}>{user.username}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Phone</div>
            <div style={{ fontWeight: 500 }}>{user.phone || 'Not set'}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Level</div>
            <div style={{ fontWeight: 500, textTransform: 'capitalize' }}>{user.level || 'beginner'}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Streak Days</div>
            <div style={{ fontWeight: 500 }}>{user.streak_days ?? 0}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Last Active</div>
            <div style={{ fontWeight: 500 }}>{formatDate(user.last_active)}</div>
          </div>

          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Member Since</div>
            <div style={{ fontWeight: 500 }}>{formatDate(user.date_joined)}</div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <button
              onClick={handleLogout}
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                background: 'transparent',
                color: '#dc2626',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Logout
            </button>
          </div>
        </div>
      )}

      {activeTab === 'profile' && profile && (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Questions Attempted</div>
              <div style={{ fontWeight: 500 }}>{profile.total_questions_attempted}</div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Questions Solved</div>
              <div style={{ fontWeight: 500 }}>{profile.total_questions_solved}</div>
            </div>

            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '4px' }}>Overall Accuracy</div>
              <div style={{ fontWeight: 500 }}>{(profile.overall_accuracy * 100).toFixed(0)}%</div>
            </div>
          </div>

          <form onSubmit={handleProfileUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}>
              <label htmlFor="preferred-language" style={{ fontSize: '14px', fontWeight: 500 }}>Preferred Language</label>
              <select
                id="preferred-language"
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg)',
                  color: 'var(--text-h)',
                  fontSize: '14px',
                }}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="hi">Hindi</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={saving}
              style={{
                padding: '10px 20px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent)',
                color: '#fff',
                fontSize: '14px',
                fontWeight: 500,
                cursor: saving ? 'not-allowed' : 'pointer',
                opacity: saving ? 0.7 : 1,
              }}
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </>
      )}

      {activeTab === 'password' && (
        <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}>
            <div style={{ fontSize: '14px', fontWeight: 500 }}>Change Password</div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
              <label htmlFor="current-password" style={{ fontSize: '14px', fontWeight: 500 }}>Current Password</label>
              <input
                id="current-password"
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
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
              <label htmlFor="new-password" style={{ fontSize: '14px', fontWeight: 500 }}>New Password</label>
              <input
                id="new-password"
                type="password"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
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
              <label htmlFor="new-password2" style={{ fontSize: '14px', fontWeight: 500 }}>Confirm New Password</label>
              <input
                id="new-password2"
                type="password"
                value={passwordForm.new_password2}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password2: e.target.value })}
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
          </div>

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              background: 'var(--accent)',
              color: '#fff',
              fontSize: '14px',
              fontWeight: 500,
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? 'Changing Password...' : 'Change Password'}
          </button>
        </form>
      )}
    </div>
  )
}
