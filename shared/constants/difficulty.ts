export const DIFFICULTY_LEVELS = ['easy', 'medium', 'hard'] as const

export type DifficultyLevel = (typeof DIFFICULTY_LEVELS)[number]

export const ATTEMPT_STATUS = ['in_progress', 'completed', 'abandoned'] as const

export type AttemptStatus = (typeof ATTEMPT_STATUS)[number]

export const UPLOAD_STATUS = ['pending', 'processing', 'completed', 'failed'] as const

export type UploadStatus = (typeof UPLOAD_STATUS)[number]

export const RECALL_STRENGTH = ['strong', 'moderate', 'weak'] as const

export type RecallStrength = (typeof RECALL_STRENGTH)[number]
