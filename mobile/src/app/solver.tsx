import { useState } from 'react'
import { View, Text, TextInput, StyleSheet, ActivityIndicator, Alert, ScrollView } from 'react-native'
import { useLocalSearchParams, router } from 'expo-router'
import { solveApi } from '../services/api'
import type { SolveResponse, SolveStep } from '../types/api'

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

export default function SolverScreen() {
  const params = useLocalSearchParams<{ q?: string }>()
  const [questionText, setQuestionText] = useState(params.q || '')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SolveResponse | null>(null)
  const [error, setError] = useState('')

  const handleSolve = async () => {
    const trimmed = questionText.trim()
    if (!trimmed) {
      Alert.alert('Error', 'Please enter a question before solving.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const response = await solveApi.solve(trimmed)
      const apiResponse = response as { success: boolean; data: SolveResponse }
      setResult(apiResponse.data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to solve question.'
      if (message.includes('401')) {
        Alert.alert('Session expired', 'Please log in again.', [
          { text: 'OK', onPress: () => router.replace('/login') },
        ])
      } else if (message.includes('503')) {
        setError('AI solver is temporarily unavailable. Please try again later.')
      } else {
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>AI Solver</Text>
      <Text style={styles.subheading}>Enter an aptitude question and get a step-by-step solution.</Text>

      <TextInput
        style={styles.textarea}
        placeholder="Type your question here..."
        multiline
        numberOfLines={4}
        value={questionText}
        onChangeText={setQuestionText}
      />
      {loading ? (
        <ActivityIndicator style={styles.solveButton} />
      ) : (
        <View style={styles.solveButton}>
          <Text style={styles.solveButtonText} onPress={handleSolve}>Solve</Text>
        </View>
      )}

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {result ? (
        <View style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <Text style={styles.resultTitle}>Solution</Text>
            <VerificationBadge status={result.verification_status} />
          </View>

          {result.topic ? (
            <View style={styles.metaRow}>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{result.topic.name}</Text>
              </View>
              {result.problem_type ? (
                <View style={[styles.badge, styles.badgeSecondary]}>
                  <Text style={[styles.badgeText, styles.badgeTextSecondary]}>{result.problem_type.name}</Text>
                </View>
              ) : null}
            </View>
          ) : null}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Concept</Text>
            <Text style={styles.bodyText}>{result.concept}</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Approach</Text>
            <Text style={styles.bodyText}>{result.approach}</Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Steps</Text>
            {result.steps.map((step: SolveStep) => (
              <View key={step.step} style={styles.stepCard}>
                <Text style={styles.stepTitle}>Step {step.step}: {step.title}</Text>
                <Text style={styles.stepCalculation}>{step.calculation}</Text>
                <Text style={styles.stepDescription}>{step.explanation}</Text>
              </View>
            ))}
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Final Answer</Text>
            <Text style={styles.answerText}>{result.final_answer}</Text>
          </View>

          {result.shortcut ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Shortcut</Text>
              <Text style={styles.bodyText}>{result.shortcut}</Text>
            </View>
          ) : null}
        </View>
      ) : null}
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
  textarea: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  solveButton: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: '#2563eb',
    alignItems: 'center',
  },
  solveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
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
  resultCard: {
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
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
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
})
