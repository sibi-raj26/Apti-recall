import * as SecureStore from 'expo-secure-store'

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const accessToken = await SecureStore.getItemAsync('aptirecall_access')

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const text = await response.text()
    let message = text || `HTTP ${response.status}`

    try {
      const parsed = JSON.parse(text)
      if (parsed?.error?.message) {
        message = parsed.error.message
      } else if (parsed?.detail) {
        message = String(parsed.detail)
      }
    } catch {
      // keep raw text message
    }

    throw new Error(message)
  }

  return response.json()
}

export const authApi = {
  register: async (payload: { email: string; username: string; password: string; password2: string }) => {
    const data = await request<{ success: boolean; data: { access: string; refresh: string; user: unknown } }>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return data
  },

  login: async (payload: { email: string; password: string }) => {
    const data = await request<{ success: boolean; data: { access: string; refresh: string; user: unknown } }>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return data
  },

  logout: async (refreshToken: string) => {
    await request<{ success: boolean; data: { message: string } }>('/auth/logout/', {
      method: 'POST',
      body: JSON.stringify({ refresh: refreshToken }),
    })
  },

  refresh: async (refreshToken: string) => {
    const data = await request<{ success: boolean; data: { access: string; refresh?: string } }>('/auth/refresh/', {
      method: 'POST',
      body: JSON.stringify({ refresh: refreshToken }),
    })
    return data
  },

  getCurrentUser: async () => {
    const data = await request<{ success: boolean; data: unknown }>('/auth/me/')
    return data
  },

  getProfile: async () => {
    const data = await request<{ success: boolean; data: unknown }>('/auth/profile/')
    return data
  },
}

export const topicApi = {
  list: async () => {
    const data = await request<{ success: boolean; data: unknown[] }>('/topics/')
    return data
  },

  get: async (id: number) => {
    const data = await request<{ success: boolean; data: unknown }>(`/topics/${id}/`)
    return data
  },
}

export const questionApi = {
  list: async (params?: { topic?: number; difficulty?: string; search?: string; page?: number }) => {
    const query = new URLSearchParams()
    if (params?.topic) query.set('topic', String(params.topic))
    if (params?.difficulty) query.set('difficulty', params.difficulty)
    if (params?.search) query.set('search', params.search)
    if (params?.page) query.set('page', String(params.page))

    const qs = query.toString()
    const data = await request<{ success: boolean; data: unknown[]; meta?: unknown }>(`/questions/${qs ? `?${qs}` : ''}`)
    return data
  },

  get: async (id: number) => {
    const data = await request<{ success: boolean; data: unknown }>(`/questions/${id}/`)
    return data
  },
}

export const solveApi = {
  solve: async (questionText: string) => {
    const data = await request<{ success: boolean; data: unknown }>('/solve/text/', {
      method: 'POST',
      body: JSON.stringify({ question_text: questionText }),
    })
    return data
  },
}

export const practiceApi = {
  generate: async (payload: { question_id?: number }) => {
    const data = await request<{ success: boolean; data: unknown }>('/practice/generate/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return data
  },
}

export const recallApi = {
  getSchedule: async () => {
    const data = await request<{ success: boolean; data: unknown[] }>('/recall/schedule/')
    return data
  },

  getAnalytics: async () => {
    const data = await request<{ success: boolean; data: unknown }>('/recall/analytics/')
    return data
  },
}

export const uploadApi = {
  uploadImage: async (image: { uri: string; name?: string; type?: string }) => {
    const formData = new FormData()
    formData.append('image', {
      uri: image.uri,
      name: image.name || 'photo.jpg',
      type: image.type || 'image/jpeg',
    } as unknown as Blob)

    const data = await request<{ success: boolean; data: unknown }>('/upload/image/', {
      method: 'POST',
      body: formData as unknown as BodyInit,
      headers: {},
    })
    return data
  },

  solveUploaded: async (payload: { upload_id: number; question_index: number }) => {
    const data = await request<{ success: boolean; data: unknown }>('/upload/solve/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    return data
  },
}

export { request }


