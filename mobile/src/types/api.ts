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

export interface User {
  id: number
  email: string
  username: string
  phone?: string
  avatar?: string
  level?: string
  streak_days?: number
  last_active?: string
  date_joined?: string
}

export interface AuthResponse {
  success: boolean
  data: {
    access: string
    refresh: string
    user: User
  }
}

export interface Topic {
  id: number
  name: string
  slug: string
  description: string
  icon: string
  order: number
  is_active: boolean
  created_at: string
}

export interface Subtopic {
  id: number
  topic: number
  name: string
  description: string
  order: number
}

export interface ProblemType {
  id: number
  topic: number
  subtopic?: number
  name: string
  description: string
  keywords: unknown[]
  solving_strategy: string
  is_active: boolean
}

export interface Formula {
  id: number
  topic: number
  problem_type?: number
  name: string
  formula_latex: string
  description: string
  variables: unknown[]
  example_usage: string
}

export interface TopicDetail extends Topic {
  subtopics: Subtopic[]
  problem_types: ProblemType[]
  formulas: Formula[]
}

export interface Question {
  id: number
  topic: number
  topic_name: string
  problem_type: number
  problem_type_name: string
  subtopic?: number
  subtopic_name?: string
  difficulty: string
  question_text: string
  correct_answer: string
  is_active: boolean
  created_at: string
}

export interface QuestionDetail extends Question {
  question_latex: string
  correct_answer_latex: string
  explanation_concept: string
  explanation_approach: string
  hints: unknown[]
  tags: unknown[]
  updated_at: string
  solution_steps: SolutionStep[]
  shortcuts: Shortcut[]
}

export interface SolutionStep {
  id: number
  question: number
  step_number: number
  title: string
  description: string
  latex: string
}

export interface Shortcut {
  id: number
  question: number
  title: string
  description: string
  formula: string
  example: string
}

export interface SolveStep {
  step: number
  title: string
  calculation: string
  explanation: string
}

export interface SolveResponse {
  question_text: string
  topic: { id: number; name: string } | null
  problem_type: { id: number; name: string } | null
  concept: string
  approach: string
  steps: SolveStep[]
  final_answer: string
  shortcut: string
  confidence: number
  verification_status: string
  verification_details?: Record<string, unknown>
  source: string
  attempt_id: number
}

export interface PracticeGenerateResponse {
  question_text: string
  topic: { id: number | null; name: string | null }
  problem_type: { id: number | null; name: string | null }
  difficulty: string
  concept: string
  approach: string
  steps: SolveStep[]
  final_answer: string
  shortcut: string
  confidence: number
  verification_status: string
  verification_details?: Record<string, unknown>
  source: string
  attempt: number
}

export interface RecallRecord {
  id: number
  topic: number
  problem_type: number | null
  question: number | null
  recall_score: number
  accuracy_score: number
  practice_count: number
  last_practiced: string | null
  next_practice_at: string | null
  difficulty_at_practice: string
  is_weak: boolean
  created_at: string
  updated_at: string
}

export interface RecallAnalytics {
  total_topics: number
  weak_count: number
  moderate_count: number
  strong_count: number
  average_recall_score: number
}

export interface UserProfile {
  id: number
  total_questions_attempted: number
  total_questions_solved: number
  overall_accuracy: number
  preferred_language: string
}

export interface UploadQuestionResponse {
  upload_id: number
  status: string
  text: string
  questions: Array<{ index: number; text: string }>
  ocr_provider?: string
  ocr_confidence?: number | null
}

export interface UploadSolveRequest {
  upload_id: number
  question_index: number
}

export interface VoiceExplanation {
  id: number
  question: number
  attempt: number | null
  audio_url?: string
  text_content: string
  language: string
  duration_seconds?: number | null
  created_at: string
}
