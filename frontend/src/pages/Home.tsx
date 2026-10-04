import { useEffect, useState } from 'react'
import { healthApi } from '../services/api'

function Home() {
  const [health, setHealth] = useState<{ status: string; service: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    healthApi
      .check()
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>AptiRecall</h1>
      <p>AI-Powered Aptitude Learning, Solving & Recall Platform</p>
      <section>
        <h2>Backend Health</h2>
        {health ? (
          <pre>{JSON.stringify(health, null, 2)}</pre>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <p>Checking backend status...</p>
        )}
      </section>
    </div>
  )
}

export default Home
