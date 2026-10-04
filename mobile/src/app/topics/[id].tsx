import { useEffect, useState } from 'react'
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert, TouchableOpacity } from 'react-native'
import { useLocalSearchParams, router } from 'expo-router'
import { topicApi } from '../../services/api'
import type { TopicDetail, Subtopic, ProblemType, Formula } from '../../types/api'

export default function TopicDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const [topic, setTopic] = useState<TopicDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      if (!id) return
      try {
        const response = await topicApi.get(Number(id))
        const apiResponse = response as { success: boolean; data: TopicDetail }
        setTopic(apiResponse.data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load topic.'
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
        <Text style={styles.statusText}>Loading topic...</Text>
      </View>
    )
  }

  if (error || !topic) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || 'Topic not found.'}</Text>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <FlatList
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.title}>{topic.name}</Text>
            <Text style={styles.description}>{topic.description || 'No description available'}</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{topic.is_active ? 'Active' : 'Inactive'}</Text>
            </View>
          </View>
        }
        data={[
          { key: 'subtopics', title: 'Subtopics', data: topic.subtopics },
          { key: 'problem_types', title: 'Problem Types', data: topic.problem_types },
          { key: 'formulas', title: 'Formulas', data: topic.formulas },
        ]}
        keyExtractor={(item) => item.key}
        renderItem={({ item }) => (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{item.title}</Text>
            {item.data.length === 0 ? (
              <Text style={styles.emptyText}>None available.</Text>
            ) : (
              item.data.map((entry: Subtopic | ProblemType | Formula) => (
                <View key={entry.id} style={styles.itemCard}>
                  <Text style={styles.itemTitle}>{entry.name}</Text>
                  {'description' in entry && entry.description ? (
                    <Text style={styles.itemDescription}>{entry.description}</Text>
                  ) : null}
                  {'solving_strategy' in entry && entry.solving_strategy ? (
                    <Text style={styles.itemMeta}>Strategy: {entry.solving_strategy}</Text>
                  ) : null}
                  {'formula_latex' in entry && entry.formula_latex ? (
                    <Text style={styles.itemMeta}>Formula: {entry.formula_latex}</Text>
                  ) : null}
                </View>
              ))
            )}
          </View>
        )}
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
    gap: 16,
  },
  header: {
    gap: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
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
  section: {
    gap: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  emptyText: {
    color: '#666',
    fontSize: 14,
  },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 4,
  },
  itemTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  itemDescription: {
    fontSize: 13,
    color: '#666',
    lineHeight: 18,
  },
  itemMeta: {
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
})
