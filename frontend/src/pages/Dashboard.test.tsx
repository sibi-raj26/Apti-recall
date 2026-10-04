import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Dashboard from '../pages/Dashboard'

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Dashboard', () => {
  it('renders dashboard for authenticated user', () => {
    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Dashboard')).toBeDefined()
  })

  it('renders feature cards with correct links', () => {
    renderWithProviders(<Dashboard />)
    expect(screen.getByText('AI Solver')).toBeDefined()
    expect(screen.getByText('Image Solver')).toBeDefined()
    expect(screen.getByText('Similar Practice')).toBeDefined()
    expect(screen.getByText('Adaptive Recall')).toBeDefined()
  })

  it('links AI Solver card to /solve', () => {
    renderWithProviders(<Dashboard />)
    const aiSolverLink = screen.getByText('AI Solver').closest('a')
    expect(aiSolverLink?.getAttribute('href')).toBe('/solve')
  })

  it('links Image Solver card to /solve/image', () => {
    renderWithProviders(<Dashboard />)
    const imageSolverLink = screen.getByText('Image Solver').closest('a')
    expect(imageSolverLink?.getAttribute('href')).toBe('/solve/image')
  })

  it('links Similar Practice card to /practice', () => {
    renderWithProviders(<Dashboard />)
    const practiceLink = screen.getByText('Similar Practice').closest('a')
    expect(practiceLink?.getAttribute('href')).toBe('/practice')
  })

  it('links Adaptive Recall card to /recall', () => {
    renderWithProviders(<Dashboard />)
    const recallLink = screen.getByText('Adaptive Recall').closest('a')
    expect(recallLink?.getAttribute('href')).toBe('/recall')
  })

  it('links Topics card to /topics', () => {
    renderWithProviders(<Dashboard />)
    const topicsLink = screen.getByText('Browse').closest('a')
    expect(topicsLink?.getAttribute('href')).toBe('/topics')
  })

  it('links Questions card to /questions', () => {
    renderWithProviders(<Dashboard />)
    const questionsLink = screen.getByText('Practice').closest('a')
    expect(questionsLink?.getAttribute('href')).toBe('/questions')
  })
})
