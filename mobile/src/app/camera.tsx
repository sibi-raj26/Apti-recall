import { useEffect, useState } from 'react'
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, Alert } from 'react-native'
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera'
import { router } from 'expo-router'

type Step = 'permission' | 'camera' | 'preview'

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions()
  const [step, setStep] = useState<Step>('permission')
  const [capturedUri, setCapturedUri] = useState<string | null>(null)
  const [cameraRef, setCameraRef] = useState<CameraView | null>(null)
  const [facing, setFacing] = useState<CameraType>('back')

  useEffect(() => {
    if (!permission) return
    if (permission.granted) {
      setStep('camera')
    } else {
      setStep('permission')
    }
  }, [permission])

  const handleRequestPermission = async () => {
    const result = await requestPermission()
    if (!result.granted) {
      Alert.alert('Permission denied', 'Camera access is required to capture aptitude questions.')
    }
  }

  const handleCapture = async () => {
    if (!cameraRef) return
    try {
      const photo = await cameraRef.takePictureAsync({
        quality: 0.8,
        base64: false,
      })
      if (photo?.uri) {
        setCapturedUri(photo.uri)
        setStep('preview')
      }
    } catch {
      Alert.alert('Error', 'Failed to capture image. Please try again.')
    }
  }

  const handleContinue = () => {
    if (!capturedUri) return
    router.replace(`/image-solver?imageUri=${encodeURIComponent(capturedUri)}`)
  }

  const handleRetake = () => {
    setCapturedUri(null)
    setStep('camera')
  }

  const handleCancel = () => {
    router.back()
  }

  if (!permission) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.statusText}>Loading camera...</Text>
      </View>
    )
  }

  if (step === 'permission' && !permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.title}>Camera Access Required</Text>
        <Text style={styles.message}>AptiRecall needs camera access to capture aptitude questions.</Text>
        <TouchableOpacity style={styles.primaryButton} onPress={handleRequestPermission}>
          <Text style={styles.primaryButtonText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.secondaryButton} onPress={handleCancel}>
          <Text style={styles.secondaryButtonText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    )
  }

  if (step === 'camera') {
    return (
      <View style={styles.container}>
        <CameraView
          ref={(ref) => setCameraRef(ref)}
          style={styles.camera}
          facing={facing}
        >
          <View style={styles.cameraOverlay}>
            <View style={styles.topBar}>
              <TouchableOpacity style={styles.iconButton} onPress={handleCancel}>
                <Text style={styles.iconButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.iconButton} onPress={() => setFacing(facing === 'back' ? 'front' : 'back')}>
                <Text style={styles.iconButtonText}>Flip</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.bottomBar}>
              <TouchableOpacity style={styles.captureButton} onPress={handleCapture}>
                <View style={styles.captureButtonInner} />
              </TouchableOpacity>
            </View>
          </View>
        </CameraView>
      </View>
    )
  }

  if (step === 'preview' && capturedUri) {
    return (
      <View style={styles.container}>
        <Image source={{ uri: capturedUri }} style={styles.preview} resizeMode="contain" />
        <View style={styles.previewActions}>
          <TouchableOpacity style={styles.secondaryButton} onPress={handleRetake}>
            <Text style={styles.secondaryButtonText}>Retake</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.primaryButton} onPress={handleContinue}>
            <Text style={styles.primaryButtonText}>Use Photo</Text>
          </TouchableOpacity>
        </View>
      </View>
    )
  }

  return null
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'space-between',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    paddingTop: 48,
  },
  bottomBar: {
    alignItems: 'center',
    paddingBottom: 32,
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureButtonInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#fff',
  },
  iconButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  iconButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  preview: {
    flex: 1,
    backgroundColor: '#000',
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
    padding: 16,
    paddingBottom: 32,
    backgroundColor: '#000',
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  message: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  statusText: {
    marginTop: 12,
    fontSize: 16,
  },
  primaryButton: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: '#2563eb',
    minWidth: 160,
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
    borderColor: '#fff',
    backgroundColor: 'transparent',
    minWidth: 160,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
})
