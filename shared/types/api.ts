export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
  meta?: {
    page: number
    total_pages: number
    total_count: number
  }
}

export interface HealthResponse {
  status: string
  service: string
}
