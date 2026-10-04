import { useEffect, useState } from 'react'
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert, TouchableOpacity, TextInput } from 'react-native'
import { router } from 'expo-router'
import { questionApi } from '../services/api'
import type { Question } from '../types/api'

export default function QuestionsScreen() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const response = await questionApi.list({ search: search || undefined })
        const apiResponse = response as { success: boolean; data: Question[] }
        setQuestions(apiResponse.data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load questions.'
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
  }, [search])

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.statusText}>Loading questions...</Text>
      </View>
    )
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => setLoading(true)}>
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search questions..."
          value={search}
          onChangeText={setSearch}
        />
      </View>
      <FlatList
        data={questions}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => router.push(`/questions/${item.id}`)}
          >
            <Text style={styles.title}>{item.question_text}</Text>
            <View style={styles.metaRow}>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{item.topic_name}</Text>
              </View>
              <View style={[styles.badge, styles.badgeSecondary]}>
                <Text style={[styles.badgeText, styles.badgeTextSecondary]}>{item.difficulty}</Text>
              </View>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text>No questions available.</Text>
          </View>
        }
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  searchRow: {
    padding: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  searchInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    fontSize: 15,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 10,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
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
  retryButton: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
  },
  retryText: {
    fontSize: 14,
  },
})
