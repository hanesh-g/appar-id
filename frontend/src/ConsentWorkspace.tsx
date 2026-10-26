import { Navigate, Route, Routes } from 'react-router-dom'
import { type User } from './api'
import StudentPortal from './StudentPortal'
import VerifierPortal from './VerifierPortal'

export default function ConsentWorkspace({
  user,
  signOut,
  initialToken,
  clearToken,
}: {
  user: User
  signOut: () => void
  initialToken: string
  clearToken: () => void
}) {
  return (
    <div className="consent-workspace">
      <header className="consent-bar">
        <strong>APAAR workspace</strong>
        <span>{user.name}</span>
        <button className="secondary" onClick={signOut}>
          Sign out
        </button>
      </header>
      <main>
        <Routes>
          <Route
            path="/"
            element={
              user.role === 'student' ? (
                <StudentPortal />
              ) : (
                <VerifierPortal initialToken={initialToken} clearToken={clearToken} />
              )
            }
          />
          <Route
            path="/verify"
            element={
              user.role === 'verifier' ? (
                <VerifierPortal initialToken={initialToken} clearToken={clearToken} />
              ) : (
                <Navigate to="/" replace />
              )
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer>
        Synthetic adult student demo · Simulated APAAR checks · Not an official government service.
      </footer>
    </div>
  )
}
