import { useState } from 'react'
import { View, Text, TextInput, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native'
import { router } from 'expo-router'
import { useAuth } from '../contexts/app/AuthContext'

export default function RegisterScreen() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()

  const handleRegister = async () => {
    if (!email.trim() || !username.trim() || !password || !password2) {
      Alert.alert('Error', 'Please fill in all fields.')
      return
    }

    setLoading(true)
    try {
      await register(email.trim(), username.trim(), password, password2)
      router.replace('/')
    } catch (err) {
      Alert.alert('Registration failed', err instanceof Error ? err.message : 'Unable to create account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create account</Text>

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
        placeholder="Username"
        autoCapitalize="none"
        value={username}
        onChangeText={setUsername}
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        secureTextEntry
        value={password}
        onChangeText={setPassword}
      />
      <TextInput
        style={styles.input}
        placeholder="Confirm password"
        secureTextEntry
        value={password2}
        onChangeText={setPassword2}
      />

      {loading ? (
        <ActivityIndicator style={styles.button} />
      ) : (
        <Button title="Register" onPress={handleRegister} />
      )}

      <Button title="Back to login" onPress={() => router.back()} />
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
    fontSize: 24,
    fontWeight: 'bold',
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
