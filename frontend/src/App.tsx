import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Topics from './pages/Topics'
import TopicDetail from './pages/TopicDetail'
import Questions from './pages/Questions'
import QuestionDetail from './pages/QuestionDetail'
import Solver from './pages/Solver'
import ImageSolver from './pages/ImageSolver'
import Practice from './pages/Practice'
import Recall from './pages/Recall'
import Progress from './pages/Progress'
import Profile from './pages/Profile'
import Admin from './pages/Admin'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ padding: '2rem' }}>
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/dashboard" replace /> : <Login />}
      />
      <Route
        path="/register"
        element={user ? <Navigate to="/dashboard" replace /> : <Register />}
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/topics"
        element={
          <ProtectedRoute>
            <Layout>
              <Topics />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/topics/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <TopicDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/questions"
        element={
          <ProtectedRoute>
            <Layout>
              <Questions />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/questions/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <QuestionDetail />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/solve"
        element={
          <ProtectedRoute>
            <Layout>
              <Solver />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/solve/image"
        element={
          <ProtectedRoute>
            <Layout>
              <ImageSolver />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/practice"
        element={
          <ProtectedRoute>
            <Layout>
              <Practice />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/recall"
        element={
          <ProtectedRoute>
            <Layout>
              <Recall />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <ProtectedRoute>
            <Layout>
              <Progress />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Layout>
              <Profile />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <Layout>
              <Admin />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to={user ? '/dashboard' : '/login'} replace />} />
    </Routes>
  )
}

export default App
