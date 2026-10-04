import { useState } from 'react'
import { View, Text, TextInput, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native'
import { router } from 'expo-router'
import { useAuth } from '../contexts/app/AuthContext'

export default function LoginScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter both email and password.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
      router.replace('/')
    } catch (err) {
      Alert.alert('Login failed', err instanceof Error ? err.message : 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>AptiRecall</Text>
      <Text style={styles.subtitle}>AI-Powered Aptitude Learning</Text>

      <TextInput
        style={styles.input}
        placeholder="Email"
        autoCapitalize="none"
        keyboardType="email-address"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />

      {loading ? (
        <ActivityIndicator style={styles.button} />
      ) : (
        <Button title="Login" onPress={handleLogin} />
      )}

      <Button title="Create account" onPress={() => router.push('/register')} />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  button: {
    marginVertical: 8,
  },
})
