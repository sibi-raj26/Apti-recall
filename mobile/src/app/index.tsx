import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native'
import { router } from 'expo-router'
import { useAuth } from '../contexts/app/AuthContext'

export default function HomeScreen() {
  const { user, loading, logout } = useAuth()

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.statusText}>Loading...</Text>
      </View>
    )
  }

  if (!user) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>AptiRecall</Text>
        <Text style={styles.subtitle}>AI-Powered Aptitude Learning</Text>
        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.primaryButton} onPress={() => router.push('/login')}>
            <Text style={styles.primaryButtonText}>Login</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryButton} onPress={() => router.push('/register')}>
            <Text style={styles.secondaryButtonText}>Create account</Text>
          </TouchableOpacity>
        </View>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome, {user.username}</Text>
      <Text style={styles.subtitle}>{user.email}</Text>
      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.primaryButton} onPress={() => router.push('/topics')}>
          <Text style={styles.primaryButtonText}>Browse Topics</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryButton} onPress={() => router.push('/questions')}>
          <Text style={styles.secondaryButtonText}>Questions</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.primaryButton} onPress={() => router.push('/image-solver')}>
          <Text style={styles.primaryButtonText}>Ask AptiRecall</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryButton} onPress={() => router.push('/solver')}>
          <Text style={styles.secondaryButtonText}>AI Solver</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={async () => { await logout(); router.replace('/'); }}>
          <Text style={styles.secondaryButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  statusText: {
    marginTop: 12,
    fontSize: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
    justifyContent: 'center',
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
})
