import { Stack } from 'expo-router'
import { AuthProvider } from '../contexts/app/AuthContext'

export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="login" />
        <Stack.Screen name="register" />
        <Stack.Screen name="topics" />
        <Stack.Screen name="topics/[id]" />
        <Stack.Screen name="questions" />
        <Stack.Screen name="questions/[id]" />
        <Stack.Screen name="solver" />
      <Stack.Screen name="image-solver" />
      <Stack.Screen name="camera" />
      </Stack>
    </AuthProvider>
  )
}
