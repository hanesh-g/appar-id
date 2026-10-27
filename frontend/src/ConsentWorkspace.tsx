import { Link, NavLink, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import {
  Activity,
  ArrowRightLeft,
  FileCheck2,
  Fingerprint,
  Home,
  Link2,
  LogOut,
  Send,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api, type Page, type User } from './api'
import type { StudentRequest } from './consent'
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
  const student = user.role === 'student'
  const path = useLocation().pathname
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
    document.getElementById('portal-main')?.focus({ preventScroll: true })
  }, [path])
  const pending = useQuery({
    queryKey: ['consent', 'pending-count'],
    queryFn: () => api<Page<StudentRequest>>('/me/verification-requests?status=PENDING'),
    enabled: student,
    refetchInterval: 15000,
  })
  const links = student
    ? [
        { path: '/', label: 'Overview', icon: Home },
        { path: '/records', label: 'My records', icon: FileCheck2 },
        { path: '/requests', label: 'Requests', icon: Send },
        { path: '/sharing', label: 'Shared access', icon: Link2 },
        { path: '/access', label: 'Access history', icon: Activity },
      ]
    : [
        { path: '/', label: 'Overview', icon: Home },
        { path: '/request', label: 'Request access', icon: Send },
        { path: '/verify', label: 'Verify a link', icon: ShieldCheck },
        { path: '/requests', label: 'Request history', icon: Activity },
      ]
  return (
    <div className="portal-layout">
      <a className="skip-link" href="#portal-main">
        Skip to content
      </a>
      <aside className="portal-sidebar">
        <Link to="/" className="portal-brand">
          <Fingerprint size={29} />
          <span>
            APAAR<small>WORKSPACE</small>
          </span>
        </Link>
        <div className="portal-role">
          <span className="portal-role-icon">
            {student ? <UserRound size={19} /> : <ShieldCheck size={19} />}
          </span>
          <div>
            <strong>{student ? 'Student workspace' : 'Verifier workspace'}</strong>
            <small>
              {student ? 'Your records. Your choice.' : 'Checks with student permission'}
            </small>
          </div>
        </div>
        <nav aria-label="Main navigation">
          {links.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'}>
              <Icon size={18} />
              <span>{label}</span>
              {student && path === '/requests' && Boolean(pending.data?.total) && (
                <b className="nav-count" aria-label={`${pending.data?.total} waiting`}>
                  {pending.data?.total}
                </b>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="portal-privacy">
          <ShieldCheck size={20} />
          <strong>{student ? 'You stay in control' : 'Permission comes first'}</strong>
          <p>
            {student
              ? 'No record fields are shared until you approve them. You can stop sharing at any time.'
              : 'Students choose which fields you can see and how long access lasts.'}
          </p>
        </div>
        <div className="portal-account">
          <span className="portal-avatar">{user.name.slice(0, 1)}</span>
          <div>
            <strong>{user.name}</strong>
            <small>{student ? 'Student' : 'Approved demo verifier'}</small>
          </div>
          <button className="icon-button" aria-label="Sign out" onClick={signOut}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <div className="portal-body">
        <header className="portal-topbar">
          <span>
            {student ? 'My student workspace' : 'Record verification'} <ArrowRightLeft size={13} />{' '}
            <b>2026–27</b>
          </span>
          <div>
            <span className="demo-pill">Simulated registry</span>
            <button className="secondary mobile-signout" onClick={signOut}>
              Sign out
            </button>
          </div>
        </header>
        <main id="portal-main" tabIndex={-1}>
          {student ? (
            <StudentPortal user={user} />
          ) : (
            <VerifierPortal initialToken={initialToken} clearToken={clearToken} />
          )}
        </main>
        <footer className="portal-footer">
          <span>SIH prototype · Synthetic adult student data</span>
          <span>Not an official government service</span>
        </footer>
      </div>
    </div>
  )
}
