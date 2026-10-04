import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { authApi } from '../services/api'
import type { User, AuthResponse } from '../types/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, password2: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const init = async () => {
      const access = localStorage.getItem('aptirecall_access')
      if (!access) {
        setLoading(false)
        return
      }
      try {
        const currentUser = await authApi.getCurrentUser()
        setUser(currentUser)
      } catch {
        localStorage.removeItem('aptirecall_access')
        localStorage.removeItem('aptirecall_refresh')
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const login = async (email: string, password: string) => {
    const result: AuthResponse = await authApi.login({ email, password })
    localStorage.setItem('aptirecall_access', result.access)
    localStorage.setItem('aptirecall_refresh', result.refresh)
    setUser(result.user)
  }

  const register = async (email: string, username: string, password: string, password2: string) => {
    const result: AuthResponse = await authApi.register({ email, username, password, password2 })
    localStorage.setItem('aptirecall_access', result.access)
    localStorage.setItem('aptirecall_refresh', result.refresh)
    setUser(result.user)
  }

  const logout = async () => {
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
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
