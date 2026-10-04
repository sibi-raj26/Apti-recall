import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Profile from '../pages/Profile'
import { authApi } from '../services/api'

vi.mock('../services/api', () => ({
  authApi: {
    getCurrentUser: vi.fn(),
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    logout: vi.fn(),
  },
}))

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

const mockUser = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  phone: '+1234567890',
  avatar: '',
  level: 'beginner',
  streak_days: 5,
  last_active: '2024-01-01',
  date_joined: '2023-06-01',
}

const mockProfile = {
  id: 1,
  total_questions_attempted: 10,
  total_questions_solved: 8,
  overall_accuracy: 0.8,
  preferred_language: 'en',
}

describe('Profile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser as any)
    vi.mocked(authApi.getProfile).mockResolvedValue(mockProfile as any)
    vi.mocked(authApi.updateProfile).mockResolvedValue({ ...mockProfile, preferred_language: 'fr' } as any)
    vi.mocked(authApi.changePassword).mockResolvedValue({ message: 'Password changed successfully.' } as any)
    vi.mocked(authApi.logout).mockResolvedValue(undefined as any)
  })

  it('renders profile page for authenticated user', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Profile & Settings')).toBeDefined()
    })
  })

  it('loads user and profile data on mount', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(authApi.getCurrentUser).toHaveBeenCalledTimes(1)
    })
    expect(authApi.getProfile).toHaveBeenCalledTimes(1)
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Profile />)
    expect(screen.getByText('Loading profile...')).toBeDefined()
  })

  it('displays account information after loading', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeDefined()
    })
    expect(screen.getByText('testuser')).toBeDefined()
    expect(screen.getByText('+1234567890')).toBeDefined()
    expect(screen.getByText('beginner')).toBeDefined()
  })

  it('displays profile information after loading', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Profile'))
    await waitFor(() => {
      expect(screen.getByText('10')).toBeDefined()
    })
    expect(screen.getByText('8')).toBeDefined()
    expect(screen.getByText('80%')).toBeDefined()
  })

  it('updates profile successfully', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Profile'))
    const select = screen.getByLabelText('Preferred Language')
    fireEvent.change(select, { target: { value: 'fr' } })
    fireEvent.click(screen.getByText('Save Profile'))
    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully.')).toBeDefined()
    })
    expect(authApi.updateProfile).toHaveBeenCalledWith({ preferred_language: 'fr' })
  })

  it('shows validation error on profile update failure', async () => {
    vi.mocked(authApi.updateProfile).mockRejectedValue(new Error('Validation failed.'))
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Profile'))
    fireEvent.click(screen.getByText('Save Profile'))
    await waitFor(() => {
      expect(screen.getByText('Validation failed.')).toBeDefined()
    })
  })

  it('shows backend error message on network failure', async () => {
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Network request failed')).toBeDefined()
    })
  })

  it('renders password form', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    expect(screen.getByLabelText('Current Password')).toBeDefined()
    expect(screen.getByLabelText('New Password')).toBeDefined()
    expect(screen.getByLabelText('Confirm New Password')).toBeDefined()
  })

  it('submits correct password change payload', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    await waitFor(() => {
      expect(authApi.changePassword).toHaveBeenCalledWith({
        current_password: 'oldpass',
        new_password: 'newpass123',
        new_password2: 'newpass123',
      })
    })
  })

  it('does not expose passwords in UI', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    expect(screen.queryByText('oldpass')).toBeNull()
    expect(screen.queryByText('newpass123')).toBeNull()
  })

  it('shows success message after password change', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    await waitFor(() => {
      expect(screen.getByText('Password changed successfully.')).toBeDefined()
    })
  })

  it('shows validation error on wrong current password', async () => {
    vi.mocked(authApi.changePassword).mockRejectedValue(new Error('Current password is incorrect.'))
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'wrong' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    await waitFor(() => {
      expect(screen.getByText('Current password is incorrect.')).toBeDefined()
    })
  })

  it('handles network failure on password change', async () => {
    vi.mocked(authApi.changePassword).mockRejectedValue(new Error('Network request failed'))
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    await waitFor(() => {
      expect(screen.getByText('Network request failed')).toBeDefined()
    })
  })

  it('clears password form after successful change', async () => {
    renderWithProviders(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('Password')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Password'))
    fireEvent.change(screen.getByLabelText('Current Password'), { target: { value: 'oldpass' } })
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'newpass123' } })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'newpass123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }))
    await waitFor(() => {
      expect(screen.getByText('Password changed successfully.')).toBeDefined()
    })
    expect((screen.getByLabelText('Current Password') as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('New Password') as HTMLInputElement).value).toBe('')
    expect((screen.getByLabelText('Confirm New Password') as HTMLInputElement).value).toBe('')
  })
})
