import { useEffect, useState } from 'react'
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, Alert, TouchableOpacity } from 'react-native'
import { useLocalSearchParams, router } from 'expo-router'
import { questionApi } from '../../services/api'
import type { QuestionDetail } from '../../types/api'

export default function QuestionDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const [question, setQuestion] = useState<QuestionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const response = await questionApi.get(Number(id))
        const apiResponse = response as { success: boolean; data: QuestionDetail }
        setQuestion(apiResponse.data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load question.'
        if (message.includes('401')) {
          Alert.alert('Session expired', 'Please log in again.', [
            { text: 'OK', onPress: () => router.replace('/login') },
          ])
        } else {
          setError(message)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.statusText}>Loading question...</Text>
      </View>
    )
  }

  if (error || !question) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || 'Question not found.'}</Text>
      </View>
    )
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.questionText}>{question.question_text}</Text>
      <View style={styles.metaRow}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{question.topic_name}</Text>
        </View>
        <View style={[styles.badge, styles.badgeSecondary]}>
          <Text style={[styles.badgeText, styles.badgeTextSecondary]}>{question.difficulty}</Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Answer</Text>
        <Text style={styles.answerText}>{question.correct_answer}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Concept</Text>
        <Text style={styles.bodyText}>{question.explanation_concept}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Approach</Text>
        <Text style={styles.bodyText}>{question.explanation_approach}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Steps</Text>
        {question.solution_steps.length === 0 ? (
          <Text style={styles.emptyText}>No steps available.</Text>
        ) : (
          question.solution_steps
            .sort((a, b) => a.step_number - b.step_number)
            .map((step) => (
              <View key={step.id} style={styles.stepCard}>
                <Text style={styles.stepTitle}>{step.title}</Text>
                <Text style={styles.stepDescription}>{step.description}</Text>
              </View>
            ))
        )}
      </View>

      {question.shortcuts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Shortcuts</Text>
          {question.shortcuts.map((shortcut) => (
            <View key={shortcut.id} style={styles.stepCard}>
              <Text style={styles.stepTitle}>{shortcut.title}</Text>
              <Text style={styles.stepDescription}>{shortcut.description}</Text>
              {shortcut.formula ? <Text style={styles.stepMeta}>Formula: {shortcut.formula}</Text> : null}
              {shortcut.example ? <Text style={styles.stepMeta}>Example: {shortcut.example}</Text> : null}
            </View>
          ))}
        </View>
      )}

      <TouchableOpacity style={styles.solveButton} onPress={() => router.push(`/solver?q=${encodeURIComponent(question.question_text)}`)}>
        <Text style={styles.solveButtonText}>Solve with AI</Text>
      </TouchableOpacity>
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
    gap: 16,
  },
  questionText: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 24,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 8,
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
  section: {
    gap: 8,
  },
  sectionTitle: {
    fontSize: 16,
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
  emptyText: {
    color: '#666',
    fontSize: 14,
  },
  stepCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 4,
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  stepDescription: {
    fontSize: 14,
    color: '#444',
    lineHeight: 20,
  },
  stepMeta: {
    fontSize: 12,
    color: '#888',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    gap: 12,
  },
  statusText: {
    marginTop: 12,
    fontSize: 16,
  },
  errorText: {
    color: '#dc2626',
    textAlign: 'center',
  },
  solveButton: {
    marginTop: 8,
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
})
