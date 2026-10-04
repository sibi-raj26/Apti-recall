import { useState, useRef, useEffect } from 'react'
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native'
import { Audio } from 'expo-av'

interface AudioPlayerProps {
  audioUrl?: string | null
  title?: string
  unavailableText?: string
}

export default function AudioPlayer({ audioUrl, title = 'Audio Explanation', unavailableText = 'Audio explanations are not available yet.' }: AudioPlayerProps) {
  const [loading, setLoading] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [error, setError] = useState('')
  const soundRef = useRef<Audio.Sound | null>(null)

  const isUnavailable = !audioUrl || error.includes('not available') || error.includes('501')

  useEffect(() => {
    return () => {
      soundRef.current?.unloadAsync()
    }
  }, [])

  const handlePlay = async () => {
    if (!audioUrl || isUnavailable) return

    setLoading(true)
    setError('')

    try {
      if (soundRef.current) {
        await soundRef.current.unloadAsync()
        soundRef.current = null
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUrl },
        { shouldPlay: true },
        (status) => {
          if (status.isLoaded && status.didJustFinish) {
            setPlaying(false)
          }
        }
      )
    } catch {
      setError('Failed to play audio. Please try again later.')
      setPlaying(false)
    } finally {
      setLoading(false)
    }
  }

  const handlePause = async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.pauseAsync()
        setPlaying(false)
      }
    } catch {
      // ignore pause errors
    }
  }

  if (isUnavailable) {
    return (
      <View style={styles.unavailableContainer}>
        <Text style={styles.unavailableIcon}>🔇</Text>
        <Text style={styles.unavailableTitle}>{title}</Text>
        <Text style={styles.unavailableText}>{unavailableText}</Text>
      </View>
    )
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
      <View style={styles.actionsRow}>
        {playing ? (
          <TouchableOpacity style={styles.secondaryButton} onPress={handlePause}>
            <Text style={styles.secondaryButtonText}>Pause</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.primaryButton} onPress={handlePlay} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryButtonText}>Play</Text>}
          </TouchableOpacity>
        )}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 12,
  },
  primaryButton: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#2563eb',
    minWidth: 100,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  secondaryButton: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    backgroundColor: '#fff',
    minWidth: 100,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#333',
    fontSize: 15,
    fontWeight: '600',
  },
  unavailableContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    gap: 8,
    alignItems: 'center',
  },
  unavailableIcon: {
    fontSize: 28,
  },
  unavailableTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#666',
  },
  unavailableText: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    lineHeight: 20,
  },
})
