import { lazy, Suspense, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import ConsentWorkspace from './ConsentWorkspace'
import { takeInitialGrantToken } from './consent'
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  FileCheck2,
  FileUp,
  Fingerprint,
  GraduationCap,
  LayoutDashboard,
  LoaderCircle,
  LogOut,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
} from 'lucide-react'
import Modal from './Dialog'
import RuleHelp from './RuleHelp'
import CategoryBreakdown from './CategoryBreakdown'
import ResolutionDesk from './ResolutionDesk'
import OverlapWorkbench from './OverlapWorkbench'
import AuditIntegrity from './AuditIntegrity'
import OfficerOverview from './OfficerOverview'
import InstitutionApproval, { ApprovalNotice } from './InstitutionApproval'
import {
  api,
  download,
  setToken,
  type Audit,
  type Batch,
  type BatchRow,
  type Dashboard,
  type Enrolment,
  type Page,
  type Programme,
  type ResolutionCase,
  type User,
} from './api'

const IntakeChart = lazy(() => import('./IntakeChart'))

export function Badge({ value }: { value: string }) {
  return (
    <span
      className={`badge ${['VERIFIED', 'COMMITTED', 'OK', 'ENROLLED', 'SUPERSEDED_BY_CORRECTION'].includes(value) ? 'good' : ['INVALID', 'ERROR', 'HELD', 'WITHDRAWN'].includes(value) ? 'danger' : 'neutral'}`}
    >
      {value === 'SUPERSEDED_BY_CORRECTION'
        ? 'Corrected'
        : value.replaceAll('_', ' ').toLowerCase()}
    </span>
  )
}
export function Notice({ error }: { error: unknown }) {
  return error ? (
    <div className="notice error" role="alert">
      {error instanceof Error ? error.message : 'Something went wrong. Try again.'}
    </div>
  ) : null
}
function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle size={20} className="spin" /> Loading records…
    </div>
  )
}
function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="empty">
      <FileCheck2 size={28} />
      <p>{children}</p>
    </div>
  )
}
function Heading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <header className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </header>
  )
}
function Stat({
  label,
  value,
  hint,
  tone = '',
}: {
  label: string
  value: number
  hint: string
  tone?: string
}) {
  return (
    <div className={`stat ${tone}`}>
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
      <small>{hint}</small>
    </div>
  )
}
function Login({ signedIn }: { signedIn: (u: User) => void }) {
  const [email, setEmail] = useState('collegea@example.test')
  const [password, setPassword] = useState('')
  const mutation = useMutation({
    mutationFn: () =>
      api<{ token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    onSuccess: (data) => {
      setToken(data.token)
      signedIn(data.user)
    },
  })
  return (
    <div className="login-page">
      <section className="login-story">
        <div className="wordmark">
          <Fingerprint /> APAAR <span>WORKSPACE</span>
        </div>
        <div>
          <div className="eyebrow">BETTER DATA. CLEARER DECISIONS.</div>
          <h1>
            Every admission.
            <br />A clearer picture.
          </h1>
          <p>
            Review student records, resolve identity gaps, and understand your institution’s intake
            in one place.
          </p>
          <div className="story-item">
            <ShieldCheck /> Institution-scoped access
          </div>
          <div className="story-item">
            <FileCheck2 /> Explainable validation
          </div>
          <div className="story-item">
            <Activity /> Accountable changes
          </div>
        </div>
        <small>SIH 2026 prototype · Synthetic student data only</small>
      </section>
      <section className="login-form">
        <div className="login-box">
          <span className="pill">SIMULATED APAAR REGISTRY</span>
          <h2>Welcome back</h2>
          <p>Sign in to your admission workspace.</p>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate()
            }}
          >
            <label>
              Email address
              <input
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <Notice error={mutation.error} />
            <button className="primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Signing in…' : 'Sign in'}
              <ArrowRight size={16} />
            </button>
          </form>
          <div className="help-box">
            <CircleHelp size={18} />
            <p>
              Use the password chosen during local setup. Demo accounts:{' '}
              <code>collegea@example.test</code>, <code>collegeb@example.test</code>, or{' '}
              <code>officer@example.test</code>.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

function DashboardPage({ user }: { user: User }) {
  const [year, setYear] = useState('2026-27')
  const [institution, setInstitution] = useState('')
  const query = useQuery({
    queryKey: ['dashboard', year, institution],
    queryFn: () =>
      api<Dashboard>(
        `/dashboard?academic_year=${year}${institution ? `&institution_id=${institution}` : ''}`,
      ),
  })
  const schools = useQuery({
    queryKey: ['institutions'],
    queryFn: () => api<{ id: string; name: string }[]>('/institutions'),
  })
  const data = query.data
  return (
    <>
      <Heading
        eyebrow="ADMISSION OVERVIEW"
        title="A clearer view of your intake"
        description="Track recorded admissions and see where your data needs attention."
        action={
          user.institution_id && (
            <Link className="primary" to="/upload">
              <Plus size={17} /> Upload admissions
            </Link>
          )
        }
      />
      <div className="filter-bar">
        <label>
          Academic year
          <select value={year} onChange={(e) => setYear(e.target.value)}>
            <option>2026-27</option>
            <option>2027-28</option>
          </select>
        </label>
        {!user.institution_id && (
          <label>
            Institution
            <select value={institution} onChange={(e) => setInstitution(e.target.value)}>
              <option value="">All institutions</option>
              {schools.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
        )}
        <span className="subtle">
          {data ? `As of ${data.as_of} · India time` : 'Fetching data'}
        </span>
      </div>
      <ApprovalNotice year={year} />
      <Notice error={query.error} />
      {query.isPending && <Loading />}
      {data && (
        <>
          <div className="stats">
            <Stat
              label="Active admissions"
              value={data.active}
              hint="Includes every identity state"
            />
            <Stat
              label="Verified identities"
              value={data.identity_counts.VERIFIED || 0}
              hint="Matched to the simulated registry"
              tone="teal"
            />
            <Stat
              label="Identity gaps"
              value={data.active - (data.identity_counts.VERIFIED || 0)}
              hint="Missing, invalid, or pending"
              tone="amber"
            />
            <Stat
              label="Above basic intake"
              value={data.excess}
              hint="Review programme-level warnings"
              tone={data.excess ? 'rose' : ''}
            />
          </div>
          {data.categories && <CategoryBreakdown categories={data.categories} />}
          <div className="dashboard-grid">
            <section className="panel">
              <div className="section-title">
                <div>
                  <h2>Programme intake</h2>
                  <p>Active recorded admissions against the configured limit</p>
                </div>
                <BookOpen size={20} />
              </div>
              {data.programmes.length ? (
                <>
                  <div className="chart">
                    <Suspense fallback={<Loading />}>
                      <IntakeChart
                        data={data.programmes.map((p) => ({
                          ...p,
                          label: `${p.programme}${!user.institution_id ? ` · ${schools.data?.find((s) => s.id === p.institution_id)?.name || ''}` : ''}`,
                        }))}
                      />
                    </Suspense>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Programme</th>
                          <th>Active / limit</th>
                          <th>Position</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.programmes.map((p) => (
                          <tr key={p.id}>
                            <td>{p.programme}</td>
                            <td>
                              {p.active} / {p.approved}
                            </td>
                            <td>
                              {p.excess ? (
                                <span className="text-danger">{p.excess} above limit</span>
                              ) : (
                                'Within basic limit'
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <Empty>Add a programme for this year to start.</Empty>
              )}
            </section>
            <section className="panel">
              <div className="section-title">
                <div>
                  <h2>Data quality</h2>
                  <p>Unresolved identity details stay visible</p>
                </div>
                <Fingerprint size={20} />
              </div>
              {['VERIFIED', 'MISSING', 'INVALID', 'PENDING_CHECK'].map((state) => (
                <div className="quality-row" key={state}>
                  <Badge value={state} />
                  <strong>{data.identity_counts[state] || 0}</strong>
                </div>
              ))}
              <div className="held-box">
                <strong>{data.held_candidates} held admission candidates</strong>
                <p>
                  Structurally blocked rows with a known programme and unique key. These are
                  separate from committed admissions.
                </p>
                <small>{data.unassignable_rows} unassignable submitted rows</small>
              </div>
              <p className="fine-print">
                Basic intake comparison only. Quota exceptions and official regulatory compliance
                are outside this demo.
              </p>
            </section>
          </div>
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Recent submissions</h2>
                <p>Review a dry run or inspect a committed batch</p>
              </div>
              <FileUp size={20} />
            </div>
            {data.batches.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>File</th>
                      <th>Rows</th>
                      <th>State</th>
                      <th>Submitted</th>
                      <th>
                        <span className="sr-only">Open</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.batches.map((b) => (
                      <tr key={b.id}>
                        <td>
                          <Link to={`/batches/${b.id}`}>{b.filename}</Link>
                        </td>
                        <td>{b.rows_total}</td>
                        <td>
                          <Badge value={b.status} />
                        </td>
                        <td>{new Date(b.created_at).toLocaleDateString()}</td>
                        <td>
                          <Link aria-label={`Open ${b.filename}`} to={`/batches/${b.id}`}>
                            <ChevronRight size={17} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>No submissions yet. Upload your first CSV to begin.</Empty>
            )}
          </section>
        </>
      )}
    </>
  )
}

function UploadPage() {
  const navigate = useNavigate()
  const [year, setYear] = useState('2026-27')
  const [file, setFile] = useState<File | null>(null)
  const [requestKey, setRequestKey] = useState(() => crypto.randomUUID())
  const [error, setError] = useState<unknown>(null)
  const mutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Choose a CSV file first.')
      if (file.size > 2 * 1024 * 1024) throw new Error('The maximum file size is 2 MiB.')
      const body = new FormData()
      body.set('file', file)
      body.set('academic_year', year)
      return api<Batch>('/batches', {
        method: 'POST',
        body,
        headers: { 'Idempotency-Key': `${requestKey}-${year}` },
      })
    },
    onSuccess: (batch) => navigate(`/batches/${batch.id}`),
  })
  return (
    <>
      <Heading
        eyebrow="STUDENT DATA"
        title="Upload admissions"
        description="Review every issue before changing your institution’s enrolment records."
      />
      <ApprovalNotice year={year} />
      <div className="steps">
        <span className="step-number">1</span>
        <b>Prepare your file</b>
        <ChevronRight size={16} />
        <span className="step-number muted">2</span>
        <span>Review the dry run</span>
        <ChevronRight size={16} />
        <span className="step-number muted">3</span>
        <span>Commit acceptable rows</span>
      </div>
      <div className="upload-grid">
        <section className="panel">
          <h2>Prepare and upload</h2>
          <p>Use the exact template headers. Maximum 500 rows and 2 MiB.</p>
          <button
            className="secondary"
            onClick={() =>
              download('/templates/students.csv', 'students-template.csv').catch(setError)
            }
          >
            <ArrowDownToLine size={16} /> Download CSV template
          </button>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate()
            }}
          >
            <label>
              Academic year
              <select value={year} onChange={(e) => setYear(e.target.value)}>
                <option>2026-27</option>
                <option>2027-28</option>
              </select>
            </label>
            <label className="upload-zone">
              <FileUp size={32} />
              <strong>{file ? file.name : 'Choose a student CSV'}</strong>
              <span>UTF-8 CSV · up to 500 rows</span>
              <input
                aria-label="Student CSV"
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null)
                  setRequestKey(crypto.randomUUID())
                }}
              />
            </label>
            <Notice error={mutation.error || error} />
            <button className="primary" disabled={!file || mutation.isPending}>
              {mutation.isPending ? (
                <>
                  <LoaderCircle size={16} className="spin" /> Checking your file…
                </>
              ) : (
                <>
                  Validate and preview <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        </section>
        <aside className="panel guidance">
          <span className="pill">BEFORE YOU UPLOAD</span>
          <h2>Good data starts here</h2>
          <p>
            <Check size={16} /> Add programmes for the selected year first.
          </p>
          <p>
            <Check size={16} /> Keep one row per student reference and programme.
          </p>
          <p>
            <Check size={16} /> Use YYYY-MM-DD for dates.
          </p>
          <p>
            <Check size={16} /> Missing IDs remain visible as identity gaps.
          </p>
          <p>
            <Check size={16} /> Uploading does not commit admissions.
          </p>
          <div className="help-box">
            <CircleHelp size={20} />
            <p>
              Try a synthetic file from the repository’s <code>fixtures/</code> folder. All identity
              checks use a simulated registry.
            </p>
          </div>
        </aside>
      </div>
    </>
  )
}

function BatchPage({ user }: { user: User }) {
  const { id } = useParams()
  const client = useQueryClient()
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [mode, setMode] = useState('commit_valid')
  const [localError, setLocalError] = useState<unknown>(null)
  const query = useQuery({ queryKey: ['batch', id], queryFn: () => api<Batch>(`/batches/${id}`) })
  const rows = useQuery({
    queryKey: ['batch-rows', id, code],
    queryFn: () =>
      api<Page<BatchRow>>(
        `/batches/${id}/rows?page_size=500${code ? `&code=${encodeURIComponent(code)}` : ''}`,
      ),
  })
  const mutation = useMutation({
    mutationFn: (action: string) =>
      api<Batch>(`/batches/${id}/${action}`, {
        method: 'POST',
        ...(action === 'commit' ? { body: JSON.stringify({ mode }) } : {}),
      }),
    onSuccess: () => client.invalidateQueries(),
  })
  const b = query.data
  const openCase = useMutation({
    mutationFn: (data: { batch_row_id: string; issue_code: string }) =>
      api<ResolutionCase>('/resolution-cases', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: (item) => {
      client.invalidateQueries({ queryKey: ['cases'] })
      navigate(`/resolution/${item.id}`)
    },
  })
  return (
    <>
      <Heading
        eyebrow="SUBMISSION REVIEW"
        title={b?.filename || 'Review submission'}
        description="Inspect the exact issues and preview the effect on recorded admissions."
        action={
          <Link className="secondary" to="/">
            Back to overview
          </Link>
        }
      />
      <Notice error={query.error || rows.error || mutation.error || openCase.error || localError} />
      {query.isPending && <Loading />}
      {b && (
        <>
          <div className="report-state">
            <Badge value={b.status} />
            <span>{b.academic_year} · Simulated registry</span>
          </div>
          <div className="stats">
            <Stat label="Submitted rows" value={b.summary.rows_total} hint="Rows in this file" />
            <Stat
              label="Without issues"
              value={b.summary.rows_ok}
              hint="Ready to commit"
              tone="teal"
            />
            <Stat
              label="Warnings"
              value={b.summary.rows_warning}
              hint="Can commit with unresolved identity"
              tone="amber"
            />
            <Stat
              label="Blocking errors"
              value={b.summary.rows_error}
              hint="Held until corrected"
              tone="rose"
            />
          </div>
          {b.result && (
            <div className="notice success" role="status">
              Committed: {b.result.created} created, {b.result.updated} updated,{' '}
              {b.result.unchanged} unchanged, {b.result.held} held.
            </div>
          )}
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Review issues</h2>
                <p>Filter the rows, read what needs attention, then open a case to correct it.</p>
              </div>
              {user.institution_id && (
                <button
                  className="secondary"
                  onClick={() =>
                    download(`/batches/${id}/errors.csv`, 'student-corrections.csv').catch(
                      setLocalError,
                    )
                  }
                >
                  <ArrowDownToLine size={16} /> Correction CSV
                </button>
              )}
            </div>
            <details className="report-help">
              <summary>How to read this report</summary>
              <p>
                Filter counts refer to issues, so one student can appear in more than one filter.
                Original issues remain in this report. Rows marked Corrected have been superseded
                and no longer count as held work.
              </p>
            </details>
            <div className="issue-filters">
              <button className={!code ? 'chip selected' : 'chip'} onClick={() => setCode('')}>
                All rows
              </button>
              {Object.entries(b.summary.issue_counts).map(([name, count]) => (
                <button
                  key={name}
                  className={code === name ? 'chip selected' : 'chip'}
                  onClick={() => setCode(name)}
                >
                  {name.replaceAll('_', ' ').toLowerCase()} <b>{count}</b>
                </button>
              ))}
            </div>
            <div className="table-wrap">
              <table className="batch-rows">
                <thead>
                  <tr>
                    <th>Row / reference</th>
                    <th>Identity</th>
                    <th>Result</th>
                    <th>What to do</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.data?.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <strong>{r.student_ref || 'Missing reference'}</strong>
                        <small>Row {r.row_no}</small>
                      </td>
                      <td>
                        <Badge value={r.identity_status} />
                      </td>
                      <td>
                        <Badge value={r.status} />
                      </td>
                      <td>
                        {r.issues.length ? (
                          r.issues.map((issue, index) => (
                            <div className="row-issue" key={index}>
                              <div className="row-issue-main">
                                <span className="row-issue-field">
                                  {issue.field === 'apaar_id'
                                    ? 'APAAR ID'
                                    : issue.field.replaceAll('_', ' ')}
                                </span>
                                <p>{issue.message}</p>
                                <RuleHelp
                                  code={issue.code}
                                  ruleSetId={b.rule_set_id}
                                  label="Why this issue?"
                                />
                                {r.status === 'SUPERSEDED_BY_CORRECTION' && (
                                  <small>Original issue retained for history.</small>
                                )}
                              </div>
                              {user.institution_id && r.status !== 'SUPERSEDED_BY_CORRECTION' && (
                                <button
                                  className="secondary row-case-button"
                                  disabled={openCase.isPending}
                                  aria-label={`Open ${issue.code} case for ${r.student_ref || `row ${r.row_no}`}`}
                                  onClick={() =>
                                    openCase.mutate({ batch_row_id: r.id, issue_code: issue.code })
                                  }
                                >
                                  Open case <ArrowRight size={13} />
                                </button>
                              )}
                            </div>
                          ))
                        ) : (
                          <span className="subtle">No issues found</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rows.data && !rows.data.total && <Empty>No rows match this issue.</Empty>}
          </section>
          <section className="panel">
            <h2>Intake preview at review time</h2>
            <p>Acceptable updates are overlaid on current records. Held candidates are separate.</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Programme</th>
                    <th>Before</th>
                    <th>After</th>
                    <th>Limit</th>
                    <th>Excess</th>
                  </tr>
                </thead>
                <tbody>
                  {b.summary.intake.map((p) => (
                    <tr key={p.programme}>
                      <td>{p.programme}</td>
                      <td>{p.before}</td>
                      <td>{p.after}</td>
                      <td>{p.approved}</td>
                      <td className={p.excess ? 'text-danger' : ''}>{p.excess}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {b.status === 'DRY_RUN_READY' && user.institution_id && (
            <section className="panel commit-bar">
              <div>
                <h2>Ready to save?</h2>
                <p>Identity warnings stay visible and count toward active admissions.</p>
                <label>
                  Commit mode
                  <select value={mode} onChange={(e) => setMode(e.target.value)}>
                    <option value="commit_valid">Save acceptable rows; hold errors</option>
                    <option value="all_or_nothing">Save only if no blocking errors</option>
                  </select>
                </label>
              </div>
              <div className="actions">
                <button
                  className="secondary"
                  disabled={mutation.isPending}
                  onClick={() => {
                    if (
                      window.confirm('Discard this staged batch? Main enrolments will not change.')
                    )
                      mutation.mutate('discard')
                  }}
                >
                  Discard
                </button>
                <button
                  className="primary"
                  disabled={mutation.isPending}
                  onClick={() => {
                    if (window.confirm('Commit this batch to your institution’s records?'))
                      mutation.mutate('commit')
                  }}
                >
                  {mutation.isPending ? 'Saving…' : 'Commit batch'}
                  <Check size={16} />
                </button>
              </div>
            </section>
          )}
        </>
      )}
    </>
  )
}

function ProgrammesPage({ user }: { user: User }) {
  const client = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Programme | null>(null)
  const query = useQuery({
    queryKey: ['programmes'],
    queryFn: () => api<Programme[]>('/programmes'),
  })
  const mutation = useMutation({
    mutationFn: (data: { name: string; academic_year: string; approved_intake: number }) =>
      api(editing ? `/programmes/${editing.id}` : '/programmes', {
        method: editing ? 'PATCH' : 'POST',
        body: JSON.stringify(editing ? { approved_intake: data.approved_intake } : data),
      }),
    onSuccess: () => {
      setOpen(false)
      setEditing(null)
      client.invalidateQueries()
    },
  })
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = new FormData(e.currentTarget)
    mutation.mutate({
      name: String(data.get('name')),
      academic_year: String(data.get('academic_year')),
      approved_intake: Number(data.get('approved_intake')),
    })
  }
  return (
    <>
      <Heading
        eyebrow="INSTITUTION SETUP"
        title="Programmes & intake"
        description="Set the courses and basic intake limits used by your admissions reports."
        action={
          user.institution_id && (
            <button
              className="primary"
              onClick={() => {
                setEditing(null)
                mutation.reset()
                setOpen(true)
              }}
            >
              <Plus size={17} /> Add programme
            </button>
          )
        }
      />
      <p className="privacy-caption">
        New or changed programmes need matching reviewed evidence before admission submissions.{' '}
        <Link to="/institution-approval">View institution approval</Link>.
      </p>
      <Notice error={query.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        <section className="panel">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Programme</th>
                  <th>Academic year</th>
                  <th>Approved intake</th>
                  {user.institution_id && <th>Action</th>}
                </tr>
              </thead>
              <tbody>
                {query.data?.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <strong>{p.name}</strong>
                    </td>
                    <td>{p.academic_year}</td>
                    <td>{p.approved_intake}</td>
                    {user.institution_id && (
                      <td>
                        <button
                          className="text-button"
                          onClick={() => {
                            setEditing(p)
                            mutation.reset()
                            setOpen(true)
                          }}
                        >
                          Edit intake
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!query.data?.length && (
            <Empty>No programmes yet. Add one before uploading admissions.</Empty>
          )}
        </section>
      )}
      {open && (
        <Modal
          title={editing ? 'Edit approved intake' : 'Add programme'}
          close={() => setOpen(false)}
        >
          <form onSubmit={submit}>
            <label>
              Programme name
              <input
                name="name"
                required
                minLength={2}
                maxLength={120}
                defaultValue={editing?.name}
                readOnly={!!editing}
              />
            </label>
            <label>
              Academic year
              <input
                name="academic_year"
                required
                pattern="20[0-9]{2}-[0-9]{2}"
                defaultValue={editing?.academic_year || '2026-27'}
                readOnly={!!editing}
              />
            </label>
            <label>
              Approved intake
              <input
                name="approved_intake"
                type="number"
                required
                min={0}
                max={100000}
                defaultValue={editing?.approved_intake ?? 60}
              />
            </label>
            <Notice error={mutation.error} />
            <button className="primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving…' : 'Save programme'}
            </button>
          </form>
        </Modal>
      )}
    </>
  )
}

function RecordModal({
  record,
  close,
  user,
}: {
  record: Enrolment
  close: () => void
  user: User
}) {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: ['record', record.id],
    queryFn: () => api<Enrolment>(`/enrolments/${record.id}`),
  })
  const [status, setStatus] = useState(record.status)
  const [end, setEnd] = useState(record.end_date || '')
  const mutation = useMutation({
    mutationFn: () =>
      api(`/enrolments/${record.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          expected_version: record.version,
          status,
          end_date: status === 'ENROLLED' ? null : end || null,
        }),
      }),
    onSuccess: () => {
      client.invalidateQueries()
      close()
    },
  })
  return (
    <Modal title={record.student_name || record.student_ref} close={close}>
      <div className="record-summary">
        <Badge value={record.identity_status} />
        <span>{record.apaar_masked}</span>
        <p>
          {record.programme} · {record.academic_year}
        </p>
      </div>
      {(query.data?.overlap_review_pending ?? record.overlap_review_pending) && (
        <p className="notice">
          A recorded date interval needs officer review. This notice does not establish that an
          enrolment is disallowed.
        </p>
      )}
      {user.institution_id && (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate()
          }}
        >
          <label>
            Enrolment status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {['ENROLLED', 'WITHDRAWN', 'TRANSFERRED', 'COMPLETED'].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          {status !== 'ENROLLED' && (
            <label>
              End date
              <input
                type="date"
                required
                min={record.start_date}
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
          )}
          <Notice error={mutation.error} />
          <button className="primary" disabled={mutation.isPending}>
            Save status
          </button>
        </form>
      )}
      <h3>Record history</h3>
      <Notice error={query.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        query.data?.history?.map((h) => (
          <div className="history-entry" key={h.version}>
            <strong>Version {h.version}</strong>
            <Badge value={String(h.snapshot.status)} />
            <small>{new Date(h.created_at).toLocaleString()}</small>
          </div>
        ))
      )}
    </Modal>
  )
}

function RecordsPage({ user }: { user: User }) {
  const client = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [record, setRecord] = useState<Enrolment | null>(null)
  const query = useQuery({
    queryKey: ['records', search, status, page],
    queryFn: () =>
      api<Page<Enrolment>>(
        `/enrolments?search=${encodeURIComponent(search)}&status=${status}&page=${page}`,
      ),
  })
  const mutation = useMutation({
    mutationFn: () =>
      api<{ checked: number; resolved: number }>('/enrolments/recheck-identities', {
        method: 'POST',
      }),
    onSuccess: () => client.invalidateQueries(),
  })
  return (
    <>
      <Heading
        eyebrow="STUDENT RECORDS"
        title="Enrolments"
        description="Review recorded admissions and preserve their history as status changes."
        action={
          user.institution_id && (
            <button
              className="secondary"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate()}
            >
              <RefreshCw size={16} /> Retry unavailable identities
            </button>
          )
        }
      />
      <div className="filter-bar">
        <label>
          Student reference
          <input
            placeholder="Search local student reference"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </label>
        <label>
          Enrolment status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setPage(1)
            }}
          >
            <option value="">All statuses</option>
            {['ENROLLED', 'WITHDRAWN', 'TRANSFERRED', 'COMPLETED'].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <span className="subtle">{query.data?.total || 0} records</span>
      </div>
      <Notice error={query.error || mutation.error} />
      {mutation.data && (
        <div className="notice success" role="status">
          Checked {mutation.data.checked} pending records; resolved {mutation.data.resolved}{' '}
          registry checks.
        </div>
      )}
      <section className="panel">
        {query.isPending ? (
          <Loading />
        ) : query.data?.items.length ? (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Student / reference</th>
                    <th>Programme</th>
                    <th>Identity</th>
                    <th>Enrolment</th>
                    <th>Version</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <button className="text-button" onClick={() => setRecord(r)}>
                          {r.student_name || r.student_ref}
                        </button>
                        <small>
                          {r.student_name && `${r.student_ref} · `}
                          {r.apaar_masked}
                        </small>
                      </td>
                      <td>
                        {r.programme}
                        <small>{r.academic_year}</small>
                      </td>
                      <td>
                        <Badge value={r.identity_status} />
                      </td>
                      <td>
                        <Badge value={r.status} />
                      </td>
                      <td>{r.version}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <button className="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span>Page {page}</span>
              <button
                className="secondary"
                disabled={page * 50 >= query.data.total}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          </>
        ) : (
          <Empty>No records match. Commit an admission batch or change your filters.</Empty>
        )}
      </section>
      {record && <RecordModal record={record} close={() => setRecord(null)} user={user} />}
    </>
  )
}

function HistoryPage({ user, auditEnabled }: { user: User; auditEnabled: boolean }) {
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['audit', page],
    queryFn: () => api<Page<Audit>>(`/audit-events?page=${page}`),
  })
  return (
    <>
      <Heading
        eyebrow="ACCOUNTABILITY"
        title="Activity history"
        description="A record of who changed what, without exposing sensitive identity details."
      />
      {user.role === 'officer' && auditEnabled && <AuditIntegrity />}
      <Notice error={query.error} />
      <section className="panel">
        {query.isPending ? (
          <Loading />
        ) : query.data?.items.length ? (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Actor</th>
                    <th>Details</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.items.map((e) => (
                    <tr key={e.id}>
                      <td>
                        <strong>{e.action.replaceAll('_', ' ').toLowerCase()}</strong>
                        <small title={e.entity_id}>Record {e.entity_id.slice(0, 8)}</small>
                      </td>
                      <td>{e.actor}</td>
                      <td>
                        {Object.entries(e.details)
                          .map(([key, value]) => `${key.replaceAll('_', ' ')}: ${String(value)}`)
                          .join(' · ') || '—'}
                      </td>
                      <td>{new Date(e.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <button className="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>
                Previous
              </button>
              <span>Page {page}</span>
              <button
                className="secondary"
                disabled={page * 50 >= query.data.total}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          </>
        ) : (
          <Empty>No recorded changes yet.</Empty>
        )}
      </section>
    </>
  )
}

const initialGrantToken = takeInitialGrantToken()

export default function App() {
  const [pendingGrantToken, setPendingGrantToken] = useState(initialGrantToken)
  const [user, setUser] = useState<User | null>(null)
  const client = useQueryClient()
  const navigate = useNavigate()
  const health = useQuery({
    queryKey: ['health'],
    queryFn: () => api<{ database: string; audit_chain_enabled?: boolean }>('/health'),
    refetchInterval: 60000,
    retry: false,
  })
  function signOut() {
    setToken('')
    setUser(null)
    setPendingGrantToken('')
    client.clear()
    navigate('/')
  }
  useEffect(() => {
    const expired = () => {
      setToken('')
      setUser(null)
      client.clear()
      navigate('/')
    }
    window.addEventListener('session-expired', expired)
    return () => window.removeEventListener('session-expired', expired)
  }, [client, navigate])
  if (!user)
    return (
      <Login
        signedIn={(u) => {
          client.clear()
          setUser(u)
          navigate(u.role === 'verifier' && pendingGrantToken ? '/verify' : '/')
        }}
      />
    )
  if (user.role === 'student' || user.role === 'verifier')
    return (
      <ConsentWorkspace
        user={user}
        signOut={signOut}
        initialToken={pendingGrantToken}
        clearToken={() => setPendingGrantToken('')}
      />
    )
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Link className="wordmark" to="/">
          <Fingerprint size={29} /> APAAR<span>WORKSPACE</span>
        </Link>
        <div className="workspace-name">
          <GraduationCap size={19} />
          <div>
            <strong>{user.institution_id ? 'Institution workspace' : 'Officer workspace'}</strong>
            <small>Academic year 2026–27</small>
          </div>
        </div>
        <nav aria-label="Main navigation">
          <span className="nav-label">WORKSPACE</span>
          <NavLink to="/" end>
            <LayoutDashboard size={18} /> Overview
          </NavLink>
          {user.institution_id && (
            <NavLink to="/upload">
              <FileUp size={18} /> Upload admissions
            </NavLink>
          )}
          <NavLink to="/records">
            <Users size={18} /> Enrolments
          </NavLink>
          {user.institution_id && (
            <NavLink to="/resolution">
              <FileCheck2 size={18} /> Resolution Desk
            </NavLink>
          )}
          <NavLink to="/programmes">
            <BookOpen size={18} /> Programmes
          </NavLink>
          <NavLink to="/institution-approval">
            <ShieldCheck size={18} /> Institution approval
          </NavLink>
          <NavLink to="/history">
            <Activity size={18} /> Activity history
          </NavLink>
          {user.role === 'officer' && (
            <NavLink to="/overlaps">
              <ShieldCheck size={18} /> Overlap reviews
            </NavLink>
          )}
        </nav>
        <div className="sidebar-note">
          <ShieldCheck size={20} />
          <strong>Demo environment</strong>
          <p>
            Synthetic students.
            <br />
            Simulated APAAR checks.
          </p>
        </div>
        <div className="user-card">
          <div className="avatar">{user.name.slice(0, 1)}</div>
          <div>
            <strong>{user.name}</strong>
            <small>
              {user.role === 'officer'
                ? 'Officer · admissions review'
                : 'Institution administrator'}
            </small>
          </div>
          <button aria-label="Sign out" onClick={signOut}>
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <div className="main-column">
        <div className="topbar">
          <span>
            Admission management <ChevronRight size={14} /> <b>Workspace</b>
          </span>
          <span className={`health ${health.data ? 'online' : ''}`}>
            <i />
            {health.data
              ? 'Database connected'
              : health.isPending
                ? 'Checking API…'
                : 'API unavailable'}
          </span>
        </div>
        <main>
          <Routes>
            <Route
              path="/"
              element={
                user.role === 'officer' ? (
                  <OfficerOverview auditEnabled={Boolean(health.data?.audit_chain_enabled)} />
                ) : (
                  <DashboardPage user={user} />
                )
              }
            />
            <Route
              path="/upload"
              element={user.institution_id ? <UploadPage /> : <Navigate to="/" />}
            />
            <Route path="/batches/:id" element={<BatchPage user={user} />} />
            <Route path="/records" element={<RecordsPage user={user} />} />
            <Route
              path="/resolution"
              element={user.institution_id ? <ResolutionDesk /> : <Navigate to="/" />}
            />
            <Route
              path="/resolution/:id"
              element={user.institution_id ? <ResolutionDesk /> : <Navigate to="/" />}
            />
            <Route path="/programmes" element={<ProgrammesPage user={user} />} />
            <Route path="/institution-approval" element={<InstitutionApproval user={user} />} />
            <Route
              path="/history"
              element={
                <HistoryPage user={user} auditEnabled={Boolean(health.data?.audit_chain_enabled)} />
              }
            />
            <Route
              path="/overlaps"
              element={user.role === 'officer' ? <OverlapWorkbench /> : <Navigate to="/" />}
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
        <footer>
          APAAR Student Data Platform · SIH prototype{' '}
          <span>Registry results are simulated. Not an official government service.</span>
        </footer>
      </div>
    </div>
  )
}
