import axios from 'axios'
import type { ApiResponse, AuthResponse, LoginRequest, RegisterRequest, Topic, TopicDetail, Question, QuestionDetail, User, UserProfile, SolveResponse, UploadQuestionResponse, UploadSolveRequest, UserAttempt, PracticeGenerateRequest, PracticeGenerateResponse, RecallRecord, RecallAnalytics, ProgressDashboard, ProgressAccuracy, ProgressTopicBreakdown, ProgressRecentMistake, ChangePasswordRequest, ChangePasswordResponse, AdminDashboard, AdminUser, AdminPerformance } from '../types/api'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

const authApiInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const access = localStorage.getItem('aptirecall_access')
    if (access) {
      config.headers.Authorization = `Bearer ${access}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const apiError = error.response?.data?.error || {
      code: 'NETWORK_ERROR',
      message: error.message,
    }

    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('aptirecall_refresh')
      if (refresh) {
        try {
          const { data } = await authApiInstance.post('/auth/refresh/', { refresh })
          const newAccess = data.data.access
          localStorage.setItem('aptirecall_access', newAccess)
          if (data.data.refresh) {
            localStorage.setItem('aptirecall_refresh', data.data.refresh)
          }
          error.config.headers.Authorization = `Bearer ${newAccess}`
          return api.request(error.config)
        } catch {
          localStorage.removeItem('aptirecall_access')
          localStorage.removeItem('aptirecall_refresh')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }

    return Promise.reject(new Error(apiError.message))
  }
)

export const authApi = {
  register: async (payload: RegisterRequest): Promise<AuthResponse> => {
    const { data } = await api.post<ApiResponse<AuthResponse>>('/auth/register/', payload)
    return data.data as AuthResponse
  },

  login: async (payload: LoginRequest): Promise<AuthResponse> => {
    const { data } = await api.post<ApiResponse<AuthResponse>>('/auth/login/', payload)
    return data.data as AuthResponse
  },

  logout: async (refresh: string): Promise<void> => {
    await api.post('/auth/logout/', { refresh })
  },

  refresh: async (refresh: string): Promise<{ access: string; refresh?: string }> => {
    const { data } = await api.post<ApiResponse<{ access: string; refresh?: string }>>('/auth/refresh/', { refresh })
    return data.data as { access: string; refresh?: string }
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await api.get<ApiResponse<User>>('/auth/me/')
    return data.data as User
  },

  getProfile: async (): Promise<UserProfile> => {
    const { data } = await api.get<ApiResponse<UserProfile>>('/auth/profile/')
    return data.data as UserProfile
  },

  updateProfile: async (payload: Partial<UserProfile>): Promise<UserProfile> => {
    const { data } = await api.patch<ApiResponse<UserProfile>>('/auth/profile/', payload)
    return data.data as UserProfile
  },

  changePassword: async (payload: ChangePasswordRequest): Promise<ChangePasswordResponse> => {
    const { data } = await api.post<ApiResponse<ChangePasswordResponse>>('/auth/change-password/', payload)
    return data.data as ChangePasswordResponse
  },
}

export const topicApi = {
  list: async (): Promise<Topic[]> => {
    const { data } = await api.get<ApiResponse<Topic[]>>('/topics/')
    return data.data as Topic[]
  },

  get: async (id: number): Promise<TopicDetail> => {
    const { data } = await api.get<ApiResponse<TopicDetail>>(`/topics/${id}/`)
    return data.data as TopicDetail
  },
}

export const questionApi = {
  list: async (params?: { topic?: number; difficulty?: string; search?: string; page?: number }): Promise<{ data: Question[]; meta?: ApiResponse<Question[]>['meta'] }> => {
    const { data } = await api.get<ApiResponse<Question[]> | { data: Question[]; meta: ApiResponse<Question[]>['meta'] }>('/questions/', { params })
    if ('meta' in data) {
      return { data: data.data as Question[], meta: data.meta }
    }
    return { data: data.data as Question[] }
  },

  get: async (id: number): Promise<QuestionDetail> => {
    const { data } = await api.get<ApiResponse<QuestionDetail>>(`/questions/${id}/`)
    return data.data as QuestionDetail
  },
}

export const healthApi = {
  check: async (): Promise<{ status: string; service: string }> => {
    const { data } = await api.get<ApiResponse<{ status: string; service: string }>>('/health/')
    return data.data as { status: string; service: string }
  },
}

export const solveApi = {
  solve: async (questionText: string): Promise<SolveResponse> => {
    const { data } = await api.post<ApiResponse<SolveResponse>>('/solve/text/', { question_text: questionText })
    return data.data as SolveResponse
  },

  history: async (): Promise<UserAttempt[]> => {
    const { data } = await api.get<ApiResponse<UserAttempt[]>>('/solve/history/')
    return data.data as UserAttempt[]
  },
}

export const uploadApi = {
  uploadImage: async (file: File): Promise<UploadQuestionResponse> => {
    const formData = new FormData()
    formData.append('image', file)
    const { data } = await api.post<ApiResponse<UploadQuestionResponse>>('/upload/image/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data.data as UploadQuestionResponse
  },

  solveUploaded: async (payload: UploadSolveRequest): Promise<SolveResponse> => {
    const { data } = await api.post<ApiResponse<SolveResponse>>('/upload/solve/', payload)
    return data.data as SolveResponse
  },
}

export const practiceApi = {
  generate: async (payload: PracticeGenerateRequest): Promise<PracticeGenerateResponse> => {
    const { data } = await api.post<ApiResponse<PracticeGenerateResponse>>('/practice/generate/', payload)
    return data.data as PracticeGenerateResponse
  },
}

export const recallApi = {
  getSchedule: async (): Promise<RecallRecord[]> => {
    const { data } = await api.get<ApiResponse<RecallRecord[]>>('/recall/schedule/')
    return data.data as RecallRecord[]
  },

  getWeakTopics: async (): Promise<RecallRecord[]> => {
    const { data } = await api.get<ApiResponse<RecallRecord[]>>('/recall/weak-topics/')
    return data.data as RecallRecord[]
  },

  getAnalytics: async (): Promise<RecallAnalytics> => {
    const { data } = await api.get<ApiResponse<RecallAnalytics>>('/recall/analytics/')
    return data.data as RecallAnalytics
  },

  submit: async (attemptId: number): Promise<RecallRecord> => {
    const { data } = await api.post<ApiResponse<RecallRecord>>('/recall/submit/', { attempt_id: attemptId })
    return data.data as RecallRecord
  },
}

export const progressApi = {
  getDashboard: async (): Promise<ProgressDashboard> => {
    const { data } = await api.get<ApiResponse<ProgressDashboard>>('/progress/dashboard/')
    return data.data as ProgressDashboard
  },

  getAccuracy: async (): Promise<ProgressAccuracy> => {
    const { data } = await api.get<ApiResponse<ProgressAccuracy>>('/progress/accuracy/')
    return data.data as ProgressAccuracy
  },

  getTopics: async (): Promise<ProgressTopicBreakdown[]> => {
    const { data } = await api.get<ApiResponse<ProgressTopicBreakdown[]>>('/progress/topics/')
    return data.data as ProgressTopicBreakdown[]
  },

  getMistakes: async (): Promise<ProgressRecentMistake[]> => {
    const { data } = await api.get<ApiResponse<ProgressRecentMistake[]>>('/progress/mistakes/')
    return data.data as ProgressRecentMistake[]
  },
}

export const adminApi = {
  getDashboard: async (): Promise<AdminDashboard> => {
    const { data } = await api.get<ApiResponse<AdminDashboard>>('/admin-panel/dashboard/')
    return data.data as AdminDashboard
  },

  listTopics: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>[]>>('/admin-panel/topics/')
    return data.data as Record<string, unknown>[]
  },

  getTopic: async (_id: number): Promise<Record<string, unknown>> => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/admin-panel/topics/${_id}/')
    return data.data as Record<string, unknown>
  },

  listQuestions: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>[]>>('/admin-panel/questions/')
    return data.data as Record<string, unknown>[]
  },

  getQuestion: async (_id: number): Promise<Record<string, unknown>> => {
    const { data } = await api.get<ApiResponse<Record<string, unknown>>>('/admin-panel/questions/${_id}/')
    return data.data as Record<string, unknown>
  },

  bulkImportQuestions: async (payload: FormData): Promise<Record<string, unknown>> => {
    const { data } = await api.post<ApiResponse<Record<string, unknown>>>('/admin-panel/questions/bulk-import/', payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data.data as Record<string, unknown>
  },

  listUsers: async (): Promise<AdminUser[]> => {
    const { data } = await api.get<ApiResponse<AdminUser[]>>('/admin-panel/users/')
    return data.data as AdminUser[]
  },

  getPerformance: async (): Promise<AdminPerformance> => {
    const { data } = await api.get<ApiResponse<AdminPerformance>>('/admin-panel/performance/')
    return data.data as AdminPerformance
  },
}

export default api
