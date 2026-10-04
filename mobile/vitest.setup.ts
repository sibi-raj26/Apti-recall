import { vi } from 'vitest'

vi.mock('react-native', () => ({
  View: 'View',
  Text: 'Text',
  TextInput: 'TextInput',
  ScrollView: 'ScrollView',
  FlatList: 'FlatList',
  TouchableOpacity: 'TouchableOpacity',
  StyleSheet: { create: (styles: Record<string, unknown>) => styles },
  ActivityIndicator: 'ActivityIndicator',
  Alert: { alert: vi.fn() },
}))

vi.mock('expo-secure-store', () => ({
  getItemAsync: vi.fn(),
  setItemAsync: vi.fn(),
  deleteItemAsync: vi.fn(),
}))

vi.mock('expo-router', () => ({
  router: { replace: vi.fn(), push: vi.fn(), back: vi.fn() },
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), back: vi.fn() }),
  useLocalSearchParams: () => ({}),
  Link: 'Link',
}))
