import { useEffect, useState } from 'react'
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert, TouchableOpacity } from 'react-native'
import { router } from 'expo-router'
import { topicApi } from '../services/api'
import type { Topic } from '../types/api'

export default function TopicsScreen() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const response = await topicApi.list()
        const apiResponse = response as { success: boolean; data: Topic[] }
        setTopics(apiResponse.data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load topics.'
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
  }, [])

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.statusText}>Loading topics...</Text>
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
      <FlatList
        data={topics}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.card}
            onPress={() => router.push(`/topics/${item.id}`)}
          >
            <Text style={styles.title}>{item.name}</Text>
            <Text style={styles.description}>{item.description || 'No description available'}</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{item.is_active ? 'Active' : 'Inactive'}</Text>
            </View>
          </TouchableOpacity>
        )}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text>No topics available.</Text>
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
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  badge: {
    alignSelf: 'flex-start',
    backgroundColor: '#dcfce7',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    color: '#16a34a',
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
