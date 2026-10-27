import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { ArrowRight, CheckCircle2, Clock3, Link2, Send, ShieldCheck } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Page, ApiError } from './api'
import {
  displayTime,
  displayFieldValue,
  EmptyState,
  FieldPicker,
  PageIntro,
  Pager,
  QueryState,
  StatusPill,
} from './PortalUI'
import {
  extractGrantToken,
  fieldLabels,
  purposeLabels,
  type FieldName,
  type Purpose,
  type SubmittedRequest,
} from './consent'

export default function VerifierPortal({
  initialToken,
  clearToken,
}: {
  initialToken: string
  clearToken: () => void
}) {
  const path = useLocation().pathname
  const [handle, setHandle] = useState('')
  const [purpose, setPurpose] = useState<Purpose>('ADMISSION_CONFIRMATION')
  const [requested, setRequested] = useState<FieldName[]>([])
  const [requestKey, setRequestKey] = useState(() => crypto.randomUUID())
  const [link, setLink] = useState(initialToken)
  const [checkedAt, setCheckedAt] = useState('')
  const [page, setPage] = useState(1)
  const client = useQueryClient()
  const submit = useMutation({
    mutationFn: () =>
      api('/verification-requests', {
        method: 'POST',
        headers: { 'Idempotency-Key': requestKey },
        body: JSON.stringify({ handle, purpose, requested_fields: requested }),
      }),
    onSuccess: () => {
      setHandle('')
      setRequestKey(crypto.randomUUID())
      void client.invalidateQueries({ queryKey: ['consent', 'submissions'] })
    },
  })
  const resolve = useMutation({
    mutationFn: () =>
      api<{ fields: Partial<Record<FieldName, string>>; valid_until: string }>(
        '/verification/resolve',
        { method: 'POST', body: JSON.stringify({ token: extractGrantToken(link) }) },
      ),
    onSuccess: () => {
      setCheckedAt(new Date().toISOString())
      setLink('')
      clearToken()
    },
  })
  const submissions = useQuery({
    queryKey: ['consent', 'submissions', page],
    queryFn: () => api<Page<SubmittedRequest>>(`/me/verification-requests/submitted?page=${page}`),
    enabled: path === '/requests',
    refetchInterval: 15000,
  })
  function request(event: FormEvent) {
    event.preventDefault()
    submit.mutate()
  }
  function open(event: FormEvent) {
    event.preventDefault()
    resolve.reset()
    resolve.mutate()
  }
  function changed() {
    setRequestKey(crypto.randomUUID())
    submit.reset()
  }
  const views: Record<string, { title: string; description: string }> = {
    '/': {
      title: 'Verify a student record',
      description: 'Start with a student request code, or open a link they have already approved.',
    },
    '/request': {
      title: 'Request student permission',
      description:
        'Paste their request code, explain your purpose, and choose only the fields you need.',
    },
    '/verify': {
      title: 'Open an approved link',
      description: 'Only fields approved for your verifier account can be opened here.',
    },
    '/requests': {
      title: 'Your request history',
      description:
        'Track submitted requests. Student record fields stay private until they approve access.',
    },
  }
  const view = views[path]
  if (!view) return <Navigate to="/" replace />
  return (
    <>
      <PageIntro eyebrow="VERIFIER WORKSPACE" title={view.title}>
        {view.description}
      </PageIntro>
      {path === '/' && (
        <>
          <div className="verifier-choices">
            <Link className="verifier-choice" to="/request">
              <span className="task-icon">
                <Send size={23} />
              </span>
              <span className="step-caption">START A NEW CHECK</span>
              <h2>I have a request code</h2>
              <p>Ask the student for permission to check specific fields in their record.</p>
              <span className="choice-action">
                Request access <ArrowRight size={16} />
              </span>
            </Link>
            <Link className="verifier-choice" to="/verify">
              <span className="task-icon">
                <Link2 size={23} />
              </span>
              <span className="step-caption">STUDENT ALREADY APPROVED</span>
              <h2>I have a sharing link</h2>
              <p>Open the fields the student approved for your account, while consent is valid.</p>
              <span className="choice-action">
                Verify a link <ArrowRight size={16} />
              </span>
            </Link>
          </div>
          <section className="panel verifier-explainer">
            <h2>How a record check works</h2>
            <ol className="sharing-steps">
              <li>
                <b>1</b>
                <span>
                  <strong>Request permission</strong>
                  <small>Use the code given to you by the student.</small>
                </span>
              </li>
              <li>
                <b>2</b>
                <span>
                  <strong>The student decides</strong>
                  <small>They choose fields and an access period.</small>
                </span>
              </li>
              <li>
                <b>3</b>
                <span>
                  <strong>Open their approved link</strong>
                  <small>Sign in with this verifier account.</small>
                </span>
              </li>
            </ol>
            <Link to="/requests">
              View your request history <ArrowRight size={14} />
            </Link>
          </section>
        </>
      )}
      {path === '/request' && (
        <div className="task-layout">
          <section className="panel task-form">
            <div className="form-heading">
              <span className="task-icon">
                <Send size={21} />
              </span>
              <div>
                <h2>Request access</h2>
                <p>The student reviews this before any fields are shared.</p>
              </div>
            </div>
            <form className="portal-form" onSubmit={request}>
              <div className="form-two-columns">
                <label className="portal-field">
                  Student request code
                  <input
                    aria-label="Student request code"
                    type="password"
                    placeholder="Paste the code from the student"
                    autoComplete="off"
                    required
                    maxLength={200}
                    value={handle}
                    onChange={(e) => {
                      setHandle(e.target.value)
                      changed()
                    }}
                  />
                  <small>Ask the student to start sharing from My records.</small>
                </label>
                <label className="portal-field">
                  Purpose
                  <select
                    aria-label="Purpose"
                    value={purpose}
                    onChange={(e) => {
                      setPurpose(e.target.value as Purpose)
                      changed()
                    }}
                  >
                    {Object.entries(purposeLabels).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <small>The student sees why you are requesting access.</small>
                </label>
              </div>
              <FieldPicker
                fields={Object.keys(fieldLabels) as FieldName[]}
                selected={requested}
                change={(value) => {
                  setRequested(value)
                  changed()
                }}
                disabled={submit.isPending}
              />
              <div className="form-submit-row">
                <p>
                  <ShieldCheck size={15} />
                  The student can approve fewer fields or decline.
                </p>
                <button
                  className="primary"
                  disabled={submit.isPending || !requested.length || !handle.trim()}
                  type="submit"
                >
                  {submit.isPending ? 'Sending…' : 'Send approval request'} <ArrowRight size={15} />
                </button>
              </div>
            </form>
            {submit.isSuccess && (
              <div role="status" className="notice success">
                <strong>Request submitted</strong>
                <p>
                  If the code matches, the student can review your request. Ask them to share their
                  approved link when ready.
                </p>
                <Link to="/requests">
                  Track your requests <ArrowRight size={14} />
                </Link>
              </div>
            )}
            {submit.error && (
              <p role="alert" className="notice error">
                {submit.error.message}
              </p>
            )}
          </section>
          <aside className="task-aside">
            <h3>What happens next?</h3>
            <p>The student checks your organisation, purpose, and requested fields.</p>
            <p>They choose an access period and send you an approved link.</p>
            <Link to="/verify">
              Already have their link? <ArrowRight size={14} />
            </Link>
          </aside>
        </div>
      )}
      {path === '/verify' && (
        <div className="verify-layout">
          <section className="panel task-form">
            <div className="form-heading">
              <span className="task-icon">
                <ShieldCheck size={22} />
              </span>
              <div>
                <h2>Check approved fields</h2>
                <p>Paste the link the student shared with your organisation.</p>
              </div>
            </div>
            <form className="portal-form" onSubmit={open}>
              <label className="portal-field">
                Student consent link
                <input
                  aria-label="Student consent link"
                  type="password"
                  placeholder="Paste the approved sharing link"
                  autoComplete="off"
                  required
                  maxLength={2000}
                  value={link}
                  onChange={(e) => {
                    setLink(e.target.value)
                    resolve.reset()
                  }}
                />
              </label>
              <div className="form-submit-row">
                <p>
                  <Clock3 size={15} />
                  Expiry and permission are checked each time.
                </p>
                <button
                  className="primary"
                  disabled={resolve.isPending || !link.trim()}
                  type="submit"
                >
                  {resolve.isPending ? 'Checking…' : 'Verify approved fields'}{' '}
                  <ArrowRight size={15} />
                </button>
              </div>
            </form>
            {resolve.error && (
              <div role="alert" className="notice error">
                <strong>
                  {resolve.error instanceof ApiError && resolve.error.status === 404
                    ? 'This link cannot be opened'
                    : resolve.error.message}
                </strong>
                <p>
                  {resolve.error instanceof ApiError && resolve.error.status === 404
                    ? 'It may be expired, stopped, or intended for another verifier. Ask the student for a new link.'
                    : 'Check the link and try again.'}
                </p>
              </div>
            )}
          </section>
          {resolve.data ? (
            <section className="panel verified-result" role="status">
              <div className="verified-result-heading">
                <CheckCircle2 size={25} />
                <div>
                  <div className="eyebrow">CHECK COMPLETED</div>
                  <h2>Approved fields</h2>
                </div>
              </div>
              <dl>
                {Object.entries(resolve.data.fields).map(([field, value]) => (
                  <div key={field}>
                    <dt>{fieldLabels[field as FieldName]}</dt>
                    <dd>{displayFieldValue(field as FieldName, value)}</dd>
                  </div>
                ))}
              </dl>
              <p>
                Checked {displayTime(checkedAt)}.<br />
                Consent expires {displayTime(resolve.data.valid_until)}.
              </p>
              <div className="result-footer">
                <span className="demo-pill">Synthetic demo record</span>
                <button className="text-button" onClick={() => resolve.reset()}>
                  Hide result
                </button>
              </div>
            </section>
          ) : (
            <div className="verify-placeholder">
              <ShieldCheck size={42} />
              <h3>Results appear here</h3>
              <p>You will see only the fields this student approved for your account.</p>
            </div>
          )}
        </div>
      )}
      {path === '/requests' && (
        <>
          <QueryState
            pending={submissions.isPending}
            error={submissions.error}
            retry={() => void submissions.refetch()}
          />
          <section className="panel submission-history">
            {submissions.data?.items.map((item) => (
              <article key={item.id}>
                <span className="activity-icon">
                  <Send size={18} />
                </span>
                <div>
                  <h3>{purposeLabels[item.purpose]}</h3>
                  <p>{item.requested_fields.map((f) => fieldLabels[f]).join(', ')}</p>
                  <small>
                    Sent {displayTime(item.created_at)} · Request expires{' '}
                    {displayTime(item.expires_at)}
                  </small>
                </div>
                <StatusPill value={item.status} />
              </article>
            ))}
            {submissions.data?.total === 0 && (
              <EmptyState
                title="No requests sent yet"
                action={
                  <Link className="primary" to="/request">
                    Request access
                  </Link>
                }
              >
                Ask a student for their request code to start a permission request.
              </EmptyState>
            )}
          </section>
          <Pager page={page} total={submissions.data?.total || 0} change={setPage} />
        </>
      )}
    </>
  )
}
