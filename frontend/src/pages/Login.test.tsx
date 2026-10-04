import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Login from '../pages/Login'

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Login', () => {
  it('renders login form', () => {
    renderWithProviders(<Login />)
    expect(screen.getByText('AptiRecall')).toBeDefined()
    expect(screen.getByText('Sign in to your account')).toBeDefined()
    expect(screen.getByLabelText('Email')).toBeDefined()
    expect(screen.getByLabelText('Password')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDefined()
  })

  it('shows validation errors on empty submit', async () => {
    renderWithProviders(<Login />)
    const form = screen.getByRole('button', { name: 'Sign in' }).closest('form')!
    form.dispatchEvent(new Event('submit'))
    await waitFor(() => {
      expect(screen.getByLabelText('Email').hasAttribute('required')).toBe(true)
    })
  })

  it('navigates to register page', () => {
    renderWithProviders(<Login />)
    expect(screen.getByText('Register')).toBeDefined()
  })
})
