import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import * as SecureStore from 'expo-secure-store'
import { authApi } from '../../services/api'
import type { User } from '../../types/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, password2: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null)
  const [loading, setLoading] = React.useState(true)

  useEffect(() => {
    const init = async () => {
      const access = await SecureStore.getItemAsync('aptirecall_access')
      if (access) {
        try {
          const response = await authApi.getCurrentUser()
          const apiUser = (response as { success: boolean; data: User }).data
          setUser(apiUser)
        } catch {
          await SecureStore.deleteItemAsync('aptirecall_access')
          await SecureStore.deleteItemAsync('aptirecall_refresh')
        }
      }
      setLoading(false)
    }
    init()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authApi.login({ email, password })
    const apiResponse = response as { success: boolean; data: { access: string; refresh: string; user: User } }
    await SecureStore.setItemAsync('aptirecall_access', apiResponse.data.access)
    await SecureStore.setItemAsync('aptirecall_refresh', apiResponse.data.refresh)
    setUser(apiResponse.data.user)
  }

  const register = async (email: string, username: string, password: string, password2: string) => {
    const response = await authApi.register({ email, username, password, password2 })
    const apiResponse = response as { success: boolean; data: { access: string; refresh: string; user: User } }
    await SecureStore.setItemAsync('aptirecall_access', apiResponse.data.access)
    await SecureStore.setItemAsync('aptirecall_refresh', apiResponse.data.refresh)
    setUser(apiResponse.data.user)
  }

  const logout = async () => {
    try {
      const refresh = await SecureStore.getItemAsync('aptirecall_refresh')
      if (refresh) {
        await authApi.logout(refresh)
      }
    } catch {
      // ignore logout errors
    } finally {
      await SecureStore.deleteItemAsync('aptirecall_access')
      await SecureStore.deleteItemAsync('aptirecall_refresh')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
