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
  access: string
  refresh: string
  user: User
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  password2: string
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

export interface TopicDetail extends Topic {
  subtopics: Subtopic[]
  problem_types: ProblemType[]
  formulas: Formula[]
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
  question_latex: string
  correct_answer: string
  correct_answer_latex: string
  explanation_concept: string
  explanation_approach: string
  explanation_steps: unknown[]
  hints: unknown[]
  tags: unknown[]
  is_active: boolean
  created_at: string
}

export interface QuestionDetail extends Question {
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

export interface UserAttempt {
  id: number
  user: number
  question: number | null
  uploaded_question: number | null
  status: string
  user_answer: string
  is_correct: boolean | null
  hints_used: number
  attempts_count: number
  time_taken_seconds: number | null
  viewed_solution: boolean
  viewed_shortcut: boolean
  viewed_concept: boolean
  solution_feedback: Record<string, unknown>
  created_at: string
  completed_at: string | null
}

export interface PracticeGenerateRequest {
  question_id?: number
  upload_id?: number
  question_index?: number
  topic?: string
  problem_type?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  question_text?: string
  concept?: string
  approach?: string
}

export interface RecallAnalytics {
  total_topics: number
  weak_count: number
  moderate_count: number
  strong_count: number
  average_recall_score: number
}

export interface ProgressDashboard {
  total_attempts: number
  completed_attempts: number
  correct_attempts: number
  incorrect_attempts: number
  accuracy: number
  topics_practiced: number
  questions_solved: number
  average_time_taken_seconds: number | null
  total_hints_used: number
  total_retry_attempts: number
}

export interface ProgressAccuracyOverall {
  total: number
  correct: number
  incorrect: number
  accuracy: number
}

export interface ProgressAccuracyDifficulty {
  difficulty: string
  total: number
  correct: number
  incorrect: number
  accuracy: number
}

export interface ProgressAccuracyTopic {
  topic_id: number
  topic_name: string
  total: number
  correct: number
  incorrect: number
  accuracy: number
}

export interface ProgressAccuracy {
  overall: ProgressAccuracyOverall
  by_difficulty: ProgressAccuracyDifficulty[]
  by_topic: ProgressAccuracyTopic[]
}

export interface ProgressTopicBreakdown {
  topic_id: number
  topic_name: string
  attempts: number
  correct: number
  incorrect: number
  accuracy: number
  hints_used: number
  average_time_taken_seconds: number | null
}

export interface ProgressRecentMistake {
  attempt_id: number
  question_id: number | null
  question_text: string
  topic_name: string
  difficulty: string
  user_answer: string
  created_at: string | null
  completed_at: string | null
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

export interface UserProfile {
  id: number
  total_questions_attempted: number
  total_questions_solved: number
  overall_accuracy: number
  preferred_language: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  new_password2: string
}

export interface ChangePasswordResponse {
  message: string
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
  duplicate_found?: boolean
  duplicate_question_id?: number
}

export interface AdminDashboard {
  total_users: number
  total_topics: number
  total_questions: number
  total_attempts: number
}

export interface AdminUser {
  id: number
  email: string
  username: string
  is_staff: boolean
  is_active: boolean
  date_joined: string
}

export interface AdminPerformance {
  total_attempts: number
  correct_attempts: number
  incorrect_attempts: number
  accuracy: number
}
