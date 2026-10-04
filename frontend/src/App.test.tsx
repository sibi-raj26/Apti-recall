import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import App from './App'

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('App', () => {
  it('renders AptiRecall title', () => {
    renderWithRouter(<App />)
    expect(screen.getByText('AptiRecall')).toBeDefined()
  })
})
