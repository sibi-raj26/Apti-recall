import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Register from '../pages/Register'

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Register', () => {
  it('renders register form', () => {
    renderWithProviders(<Register />)
    expect(screen.getByText('AptiRecall')).toBeDefined()
    expect(screen.getByText('Create your account')).toBeDefined()
    expect(screen.getByLabelText('Email')).toBeDefined()
    expect(screen.getByLabelText('Username')).toBeDefined()
    expect(screen.getByLabelText('Password')).toBeDefined()
    expect(screen.getByLabelText('Confirm Password')).toBeDefined()
  })

  it('navigates to login page', () => {
    renderWithProviders(<Register />)
    expect(screen.getByText('Sign in')).toBeDefined()
  })
})
