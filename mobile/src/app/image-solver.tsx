import { useState, useEffect } from 'react'
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, Alert, ScrollView } from 'react-native'
import { useLocalSearchParams, router } from 'expo-router'
import { launchImageLibraryAsync, MediaTypeOptions, launchCameraAsync } from 'expo-image-picker'
import * as MediaLibrary from 'expo-media-library'
import { uploadApi } from '../services/api'
import type { UploadQuestionResponse, SolveResponse, SolveStep } from '../types/api'

type Step = 'select' | 'preview' | 'processing' | 'questions' | 'solving' | 'result'

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
const MAX_FILE_SIZE = 10 * 1024 * 1024

function VerificationBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase()
  let color = '#666'
  let label = status
  if (normalized === 'VERIFIED') {
    color = '#16a34a'
    label = 'Verified'
  } else if (normalized === 'FAILED') {
    color = '#dc2626'
    label = 'Failed'
  } else if (normalized === 'UNABLE_TO_VERIFY') {
    color = '#d97706'
    label = 'Unable to verify'
  } else if (normalized === 'NOT_VERIFIED') {
    color = '#666'
    label = 'Not verified'
  }

  return (
    <View style={[styles.badge, { backgroundColor: `${color}20` }]}>
      <Text style={[styles.badgeText, { color }]}>{label}</Text>
    </View>
  )
}

export default function ImageSolverScreen() {
  const params = useLocalSearchParams<{ imageUri?: string }>()
  const [step, setStep] = useState<Step>('select')
  const [imageUri, setImageUri] = useState<string | null>(params.imageUri || null)
  const [ocrResult, setOcrResult] = useState<UploadQuestionResponse | null>(null)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [solution, setSolution] = useState<SolveResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (params.imageUri) {
      setImageUri(params.imageUri)
      setStep('preview')
    }
  }, [params.imageUri])

  const validateImage = (uri: string, name?: string | null, size?: number | null): string | null => {
    const extension = name?.split('.').pop()?.toLowerCase() || ''
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return 'Please select a supported image file.'
    }
    if (size && size > MAX_FILE_SIZE) {
      return 'Image size exceeds the allowed limit of 10MB.'
    }
    return null
  }

  const handleTakePhoto = async () => {
    const permission = await launchCameraAsync({
      mediaTypes: ['images'],
      quality: 0.8,
      allowsEditing: false,
    })

    if (permission.canceled) return

    const asset = permission.assets[0]
    if (!asset) return

    const validationError = validateImage(asset.uri, asset.fileName, asset.fileSize)
    if (validationError) {
      Alert.alert('Invalid image', validationError)
      return
    }

    setImageUri(asset.uri)
    setStep('preview')
  }

  const handlePickImage = async () => {
    const permission = await MediaLibrary.requestPermissionsAsync()
    if (!permission.granted) {
      Alert.alert('Permission denied', 'Media library access is required to select images.')
      return
    }

    const result = await launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
      allowsEditing: false,
    })

    if (result.canceled) return

    const asset = result.assets[0]
    if (!asset) return

    const validationError = validateImage(asset.uri, asset.fileName, asset.fileSize)
    if (validationError) {
      Alert.alert('Invalid image', validationError)
      return
    }

    setImageUri(asset.uri)
    setStep('preview')
  }

  const handleProcess = async () => {
    if (!imageUri) return

    setError('')
    setStep('processing')

    try {
      const data = await uploadApi.uploadImage({
        uri: imageUri,
        name: `upload_${Date.now()}.jpg`,
        type: 'image/jpeg',
      })
      const response = data as { success: boolean; data: UploadQuestionResponse }
      setOcrResult(response.data)
      if (response.data.questions && response.data.questions.length > 0 && response.data.questions.length === 1) {
        setSelectedIndex(response.data.questions[0].index)
      }
      setStep('questions')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process image.'
      if (message.includes('temporarily unavailable') || message.includes('503')) {
        setError('Image processing is temporarily unavailable. Please try again.')
      } else if (message.includes('size') || message.includes('limit')) {
        setError('Image size exceeds the allowed limit.')
      } else if (message.includes('Unsupported') || message.includes('VALIDATION_ERROR')) {
        setError('Please select a supported image file.')
      } else if (message.includes('Network') || message.includes('network')) {
        setError('Connection error. Please check your internet and try again.')
      } else {
        setError('Failed to process the image. Please try again.')
      }
      setStep('preview')
    }
  }

  const handleSolve = async () => {
    if (!ocrResult || selectedIndex === null) return

    setError('')
    setStep('solving')

    try {
      const data = await uploadApi.solveUploaded({
        upload_id: ocrResult.upload_id,
        question_index: selectedIndex,
      })
      const response = data as { success: boolean; data: SolveResponse }
      setSolution(response.data)
      setStep('result')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to solve question.'
      if (message.includes('503')) {
        setError('AI solver is temporarily unavailable. Please try again later.')
      } else {
        setError(message)
      }
      setStep('questions')
    }
  }

  const handleReset = () => {
    setImageUri(null)
    setOcrResult(null)
    setSelectedIndex(null)
    setSolution(null)
    setError('')
    setStep('select')
  }

  const handleBackToQuestions = () => {
    setSolution(null)
    setError('')
    setStep('questions')
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Ask AptiRecall</Text>
      <Text style={styles.subheading}>Capture or upload an aptitude question image to get a step-by-step solution.</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {step === 'select' && (
        <View style={styles.selectContainer}>
          <TouchableOpacity style={styles.optionButton} onPress={handleTakePhoto}>
            <Text style={styles.optionIcon}>📷</Text>
            <Text style={styles.optionTitle}>Take Photo</Text>
            <Text style={styles.optionDescription}>Capture a question with your camera</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.optionButton} onPress={handlePickImage}>
            <Text style={styles.optionIcon}>🖼️</Text>
            <Text style={styles.optionTitle}>Choose from Gallery</Text>
            <Text style={styles.optionDescription}>Select an existing image</Text>
          </TouchableOpacity>
        </View>
      )}

      {step === 'preview' && imageUri && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="contain" />
          <View style={styles.previewActions}>
            <TouchableOpacity style={styles.secondaryButton} onPress={handleReset}>
              <Text style={styles.secondaryButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.primaryButton} onPress={handleProcess}>
              <Text style={styles.primaryButtonText}>Process Image</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {step === 'processing' && (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.statusText}>Reading your image...</Text>
          <Text style={styles.statusSubtext}>This may take a few seconds.</Text>
        </View>
      )}

      {step === 'questions' && ocrResult && (
        <View style={styles.questionsContainer}>
          <Text style={styles.sectionTitle}>Detected Questions</Text>
          {ocrResult.questions.length === 0 ? (
            <Text style={styles.emptyText}>No questions were detected in this image. Please try a clearer image.</Text>
          ) : (
            <View style={styles.questionsList}>
              {ocrResult.questions.map((q) => (
                <TouchableOpacity
                  key={q.index}
                  style={[
                    styles.questionCard,
                    selectedIndex === q.index && styles.questionCardSelected,
                  ]}
                  onPress={() => setSelectedIndex(q.index)}
                >
                  <Text style={styles.questionIndex}>Question {q.index}</Text>
                  <Text style={styles.questionText}>{q.text}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
          <View style={styles.actionsRow}>
            <TouchableOpacity style={styles.secondaryButton} onPress={handleReset}>
              <Text style={styles.secondaryButtonText}>Start Over</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.primaryButton, selectedIndex === null && styles.buttonDisabled]}
              onPress={handleSolve}
              disabled={selectedIndex === null}
            >
              <Text style={styles.primaryButtonText}>Solve Selected</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {step === 'solving' && (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
          <Text style={styles.statusText}>AptiRecall is solving your question...</Text>
        </View>
      )}

      {step === 'result' && solution && (
        <View style={styles.resultContainer}>
          <View style={styles.resultHeader}>
            <Text style={styles.resultTitle}>Solution</Text>
            <VerificationBadge status={solution.verification_status} />
          </View>

          {solution.topic ? (
            <View style={styles.metaRow}>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{solution.topic.name}</Text>
              </View>
              {solution.problem_type ? (
                <View style={[styles.badge, styles.badgeSecondary]}>
                  <Text style={[styles.badgeText, styles.badgeTextSecondary]}>{solution.problem_type.name}</Text>
                </View>
              ) : null}
            </View>
          ) : null}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Concept</Text>
            <Text style={styles.bodyText}>{solution.concept}</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Approach</Text>
            <Text style={styles.bodyText}>{solution.approach}</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Steps</Text>
            {solution.steps.map((step) => (
              <View key={step.step} style={styles.stepCard}>
                <Text style={styles.stepTitle}>Step {step.step}: {step.title}</Text>
                <Text style={styles.stepCalculation}>{step.calculation}</Text>
                <Text style={styles.stepDescription}>{step.explanation}</Text>
              </View>
            ))}
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Final Answer</Text>
            <Text style={styles.answerText}>{solution.final_answer}</Text>
          </View>

          {solution.shortcut ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Shortcut</Text>
              <Text style={styles.bodyText}>{solution.shortcut}</Text>
            </View>
          ) : null}

          <View style={styles.resultActions}>
            <TouchableOpacity style={styles.secondaryButton} onPress={handleBackToQuestions}>
              <Text style={styles.secondaryButtonText}>Back to Questions</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.primaryButton} onPress={handleReset}>
              <Text style={styles.primaryButtonText}>Solve Another</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  content: {
    padding: 16,
    gap: 12,
  },
  heading: {
    fontSize: 22,
    fontWeight: '700',
  },
  subheading: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  selectContainer: {
    gap: 12,
    marginTop: 16,
  },
  optionButton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 8,
  },
  optionIcon: {
    fontSize: 32,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  optionDescription: {
    fontSize: 14,
    color: '#666',
  },
  previewContainer: {
    gap: 12,
  },
  preview: {
    width: '100%',
    height: 300,
    borderRadius: 12,
    backgroundColor: '#000',
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
  },
  centerContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    gap: 12,
  },
  statusText: {
    marginTop: 12,
    fontSize: 16,
    fontWeight: '600',
  },
  statusSubtext: {
    fontSize: 14,
    color: '#666',
  },
  processingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    gap: 12,
  },
  questionsContainer: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  emptyText: {
    color: '#666',
    fontSize: 14,
  },
  questionsList: {
    gap: 10,
  },
  questionCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 6,
  },
  questionCardSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
  },
  questionIndex: {
    fontSize: 12,
    fontWeight: '700',
    color: '#2563eb',
    textTransform: 'uppercase',
  },
  questionText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  resultContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 12,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    color: '#0369a1',
  },
  badgeSecondary: {
    backgroundColor: '#f3e8ff',
  },
  badgeTextSecondary: {
    color: '#7e22ce',
    textTransform: 'capitalize',
  },
  metaRow: {
    flexDirection: 'row',
    gap: 8,
  },
  section: {
    gap: 6,
  },
  bodyText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  answerText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#16a34a',
  },
  stepCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 4,
  },
  stepTitle: {
    fontSize: 14,
    fontWeight: '600',
  },
  stepCalculation: {
    fontSize: 14,
    color: '#2563eb',
    fontFamily: 'monospace',
  },
  stepDescription: {
    fontSize: 13,
    color: '#444',
    lineHeight: 18,
  },
  resultActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  errorBox: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
  },
  errorText: {
    color: '#dc2626',
    textAlign: 'center',
  },
  primaryButton: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: '#2563eb',
    minWidth: 140,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
    minWidth: 140,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
})
