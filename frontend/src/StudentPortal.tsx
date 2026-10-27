import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileCheck2,
  Link2,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import ConsentShareCard from './ConsentShareCard'
import RecordCard from './StudentRecordTile'
import RequestCard from './StudentRequestReview'
import GrantCard from './StudentGrantCard'
import { api, type Page, type User } from './api'
import { displayTime, EmptyState, PageIntro, Pager, QueryState } from './PortalUI'
import {
  fieldLabels,
  purposeLabels,
  type FieldName,
  type OwnRecord,
  type StudentRequest,
  type Grant,
  type IssuedGrant,
} from './consent'

const views: Record<string, { title: string; description: string }> = {
  '/': {
    title: 'Your student records',
    description: 'Keep your records close. Share only what you choose.',
  },
  '/records': {
    title: 'My records',
    description: 'Choose a verified record to start sharing with an organisation.',
  },
  '/requests': {
    title: 'Review requests',
    description: 'Check who is asking, why they need it, and which fields you want to share.',
  },
  '/sharing': {
    title: 'Manage shared access',
    description: 'See your sharing periods, stop future access, or replace a lost link.',
  },
  '/access': {
    title: 'Access history',
    description: 'See when an organisation opened the fields you approved.',
  },
}

export default function StudentPortal({ user }: { user: User }) {
  const path = useLocation().pathname
  const navigate = useNavigate()
  const client = useQueryClient()
  const [issued, setIssued] = useState<IssuedGrant | null>(null)
  const [recordPage, setRecordPage] = useState(1)
  const [requestPage, setRequestPage] = useState(1)
  const [requestFilter, setRequestFilter] = useState('PENDING')
  const [grantPage, setGrantPage] = useState(1)
  const [accessPage, setAccessPage] = useState(1)
  const records = useQuery({
    queryKey: ['consent', 'records', recordPage],
    queryFn: () => api<Page<OwnRecord>>(`/me/enrolments?page=${recordPage}`),
    enabled: path === '/' || path === '/records',
  })
  const pending = useQuery({
    queryKey: ['consent', 'pending-count'],
    queryFn: () => api<Page<StudentRequest>>('/me/verification-requests?status=PENDING'),
    refetchInterval: 15000,
  })
  const requests = useQuery({
    queryKey: ['consent', 'requests', requestFilter, requestPage],
    queryFn: () =>
      api<Page<StudentRequest>>(
        `/me/verification-requests?page=${requestPage}${requestFilter === 'PENDING' ? '&status=PENDING' : ''}`,
      ),
    enabled: path === '/requests',
    refetchInterval: 15000,
  })
  const grants = useQuery({
    queryKey: ['consent', 'grants', grantPage],
    queryFn: () => api<Page<Grant>>(`/me/consent-grants?page=${grantPage}`),
    enabled: path === '/sharing',
    refetchInterval: 15000,
  })
  const accesses = useQuery({
    queryKey: ['consent', 'accesses', accessPage],
    queryFn: () =>
      api<
        Page<{
          id: string
          verifier_organisation: string
          purpose: keyof typeof purposeLabels
          disclosed_fields: FieldName[]
          accessed_at: string
        }>
      >(`/me/verification-accesses?page=${accessPage}`),
    enabled: path === '/' || path === '/access',
    refetchInterval: 15000,
  })
  const view = views[path]
  if (!view) return <Navigate to="/" replace />
  function remember(data: IssuedGrant) {
    if (data.newly_issued) {
      setIssued(data)
      navigate('/sharing')
    }
  }
  return (
    <>
      <PageIntro
        eyebrow="YOUR PRIVATE WORKSPACE"
        title={view.title}
        action={
          <button
            className="secondary"
            onClick={() => void client.invalidateQueries({ queryKey: ['consent'] })}
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        }
      >
        {view.description}
      </PageIntro>
      {issued && (
        <ConsentShareCard key={issued.grant.id} value={issued} clear={() => setIssued(null)} />
      )}
      {path === '/' && (
        <>
          <section className="student-welcome">
            <div>
              <span className="welcome-icon">
                <ShieldCheck size={26} />
              </span>
              <h2>You decide who sees your records.</h2>
              <p>
                Start with a record. Give the organisation a request code. Then review and approve
                only the fields they need.
              </p>
              <Link className="primary" to="/records">
                Share a record <ArrowRight size={16} />
              </Link>
            </div>
            <ol className="sharing-steps">
              <li>
                <b>1</b>
                <span>
                  <strong>Choose a record</strong>
                  <small>Create a one-use request code.</small>
                </span>
              </li>
              <li>
                <b>2</b>
                <span>
                  <strong>Review their request</strong>
                  <small>Choose the fields and access time.</small>
                </span>
              </li>
              <li>
                <b>3</b>
                <span>
                  <strong>Share your approved link</strong>
                  <small>Stop sharing whenever you choose.</small>
                </span>
              </li>
            </ol>
          </section>
          <div className="student-summary">
            <Link to="/records">
              <FileCheck2 size={21} />
              <div>
                <strong>{records.data?.total ?? '—'}</strong>
                <span>Verified records</span>
              </div>
              <ArrowRight size={17} />
            </Link>
            <Link to="/requests" className={pending.data?.total ? 'needs-action' : ''}>
              <Clock3 size={21} />
              <div>
                <strong>{pending.data?.total ?? '—'}</strong>
                <span>Requests to review</span>
              </div>
              <ArrowRight size={17} />
            </Link>
          </div>
          {Boolean(pending.data?.total) && (
            <div className="attention-banner">
              <div>
                <strong>A verifier is waiting for your approval</strong>
                <p>Review the organisation, purpose, and fields before sharing.</p>
              </div>
              <Link className="primary" to="/requests">
                Review requests <ArrowRight size={15} />
              </Link>
            </div>
          )}
          <div className="portal-section-heading">
            <h2>Your verified records</h2>
            <Link to="/records">
              View all records <ArrowRight size={14} />
            </Link>
          </div>
        </>
      )}
      {(path === '/' || path === '/records') && (
        <>
          <QueryState
            pending={records.isPending}
            error={records.error}
            retry={() => void records.refetch()}
          />
          <div className="record-grid">
            {(path === '/' ? records.data?.items.slice(0, 2) : records.data?.items)?.map(
              (record) => (
                <RecordCard key={record.id} record={record} studentName={user.name} />
              ),
            )}
          </div>
          {records.data?.total === 0 && (
            <section className="panel">
              <EmptyState title="Your records will appear here">
                Your college needs to submit and verify your record first. Ask its admissions team
                if you expected to see one.
              </EmptyState>
            </section>
          )}
          {path === '/records' && (
            <Pager page={recordPage} total={records.data?.total || 0} change={setRecordPage} />
          )}
        </>
      )}
      {path === '/requests' && (
        <>
          <div className="portal-toolbar">
            <label className="portal-field">
              Show requests
              <select
                aria-label="Show requests"
                value={requestFilter}
                onChange={(e) => {
                  setRequestFilter(e.target.value)
                  setRequestPage(1)
                }}
              >
                <option value="PENDING">Waiting for my approval</option>
                <option value="ALL">All requests</option>
              </select>
            </label>
            <span className="subtle">
              {requests.data ? `${requests.data.total} matching requests` : 'Checking requests…'}
            </span>
          </div>
          <QueryState
            pending={requests.isPending}
            error={requests.error}
            retry={() => void requests.refetch()}
          />
          {requests.data?.items.map((item) => (
            <RequestCard key={`${item.id}:${item.version}`} item={item} issued={remember} />
          ))}
          {requests.data?.total === 0 && (
            <section className="panel">
              <EmptyState
                title={
                  requestFilter === 'PENDING' ? 'No requests need your approval' : 'No requests yet'
                }
              >
                Give a verifier a request code from My records. A matching request will appear here
                for you to review.
              </EmptyState>
            </section>
          )}
          <Pager page={requestPage} total={requests.data?.total || 0} change={setRequestPage} />
        </>
      )}
      {path === '/sharing' && (
        <>
          <QueryState
            pending={grants.isPending}
            error={grants.error}
            retry={() => void grants.refetch()}
          />
          {grants.data?.items.map((grant) => (
            <GrantCard
              key={grant.id}
              grant={grant}
              issued={remember}
              revoked={(id) => setIssued((current) => (current?.grant.id === id ? null : current))}
            />
          ))}
          {grants.data?.total === 0 && (
            <section className="panel">
              <EmptyState
                title="You are not sharing any records yet"
                action={
                  <Link className="primary" to="/records">
                    Share a record
                  </Link>
                }
              >
                Once you approve a request, you can manage its access here.
              </EmptyState>
            </section>
          )}
          <Pager page={grantPage} total={grants.data?.total || 0} change={setGrantPage} />
        </>
      )}
      {path === '/access' && (
        <>
          <QueryState
            pending={accesses.isPending}
            error={accesses.error}
            retry={() => void accesses.refetch()}
          />
          <section className="panel activity-list">
            {accesses.data?.items.map((access) => (
              <article key={access.id}>
                <span className="activity-icon">
                  <CheckCircle2 size={19} />
                </span>
                <div>
                  <h3>{access.verifier_organisation}</h3>
                  <p>
                    {purposeLabels[access.purpose]} ·{' '}
                    {access.disclosed_fields.map((f) => fieldLabels[f]).join(', ')}
                  </p>
                  <time dateTime={access.accessed_at}>{displayTime(access.accessed_at)}</time>
                </div>
              </article>
            ))}
            {accesses.data?.total === 0 && (
              <EmptyState title="No record checks yet">
                When a verifier opens your approved link, its organisation, fields, and time will
                appear here.
              </EmptyState>
            )}
          </section>
          <Pager page={accessPage} total={accesses.data?.total || 0} change={setAccessPage} />
        </>
      )}
      {path === '/' && (
        <div className="privacy-strip">
          <Link2 size={18} />
          <p>
            <strong>Already shared a record?</strong> Manage links and stop access from Shared
            access.
          </p>
          <Link to="/sharing">
            Manage access <ArrowRight size={14} />
          </Link>
        </div>
      )}
    </>
  )
}
