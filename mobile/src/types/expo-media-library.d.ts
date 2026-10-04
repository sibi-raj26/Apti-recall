declare module 'expo-media-library' {
  export function requestPermissionsAsync(): Promise<{ granted: boolean }>
}
