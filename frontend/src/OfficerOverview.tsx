import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  Building2,
  ClipboardCheck,
  FileClock,
  RefreshCw,
  ShieldCheck,
  Users,
} from 'lucide-react'
import { api, type Dashboard, type Page } from './api'
import { EmptyState, PageIntro, QueryState } from './PortalUI'
import CategoryBreakdown from './CategoryBreakdown'

export default function OfficerOverview({ auditEnabled }: { auditEnabled: boolean }) {
  const dashboard = useQuery({
    queryKey: ['officer-dashboard'],
    queryFn: () => api<Dashboard>('/dashboard?academic_year=2026-27'),
    refetchInterval: 30000,
  })
  const schools = useQuery({
    queryKey: ['institutions'],
    queryFn: () => api<{ id: string; name: string }[]>('/institutions'),
  })
  const waiting = useQuery({
    queryKey: ['overlaps', 'count', 'OPEN'],
    queryFn: () => api<Page<{ id: string }>>('/overlap-reviews?status=OPEN'),
    refetchInterval: 15000,
  })
  const data = dashboard.data
  return (
    <div className="officer-overview">
      <PageIntro
        eyebrow="OFFICER WORKSPACE"
        title="Admission oversight"
        action={
          <button
            className="secondary"
            onClick={() => {
              void dashboard.refetch()
              void waiting.refetch()
            }}
          >
            <RefreshCw size={15} />
            Refresh overview
          </button>
        }
      >
        See what needs review across colleges, then open the evidence before making a decision.
      </PageIntro>
      <QueryState
        pending={dashboard.isPending}
        error={dashboard.error}
        retry={() => void dashboard.refetch()}
      />
      <div className="officer-metrics">
        <div>
          <span className="metric-icon">
            <Building2 size={21} />
          </span>
          <span>
            <small>Colleges in view</small>
            <strong>{schools.data?.length ?? '—'}</strong>
          </span>
        </div>
        <div>
          <span className="metric-icon">
            <Users size={21} />
          </span>
          <span>
            <small>Active admissions</small>
            <strong>{data?.active ?? '—'}</strong>
          </span>
        </div>
        <div className="metric-attention">
          <span className="metric-icon">
            <ClipboardCheck size={21} />
          </span>
          <span>
            <small>Overlaps awaiting review</small>
            <strong>{waiting.data?.total ?? '—'}</strong>
          </span>
        </div>
      </div>
      <section className="officer-next">
        <div>
          <div className="eyebrow">START HERE</div>
          <h2>
            {waiting.isPending
              ? 'Checking your review queue…'
              : waiting.error
                ? 'Your review queue could not be loaded'
                : waiting.data?.total
                  ? 'Review overlapping enrolments'
                  : 'Your review queue is clear'}
          </h2>
          <p>
            {waiting.data?.total
              ? 'Compare college records with intersecting dates. Record your review without changing either admission.'
              : waiting.data
                ? 'No open date-overlap reviews were returned. You can inspect previous decisions or check activity history.'
                : 'Wait for the queue to load, or open the review page to try again.'}
          </p>
          <Link className="primary" to="/overlaps">
            Open overlap reviews <ArrowRight size={16} />
          </Link>
        </div>
        <span className="officer-next-icon">
          <ClipboardCheck size={55} />
        </span>
      </section>
      {waiting.error && (
        <QueryState pending={false} error={waiting.error} retry={() => void waiting.refetch()} />
      )}
      {schools.error && (
        <QueryState pending={false} error={schools.error} retry={() => void schools.refetch()} />
      )}
      <div className="officer-task-grid">
        <Link className="officer-task" to="/history">
          <span className="task-icon">
            <ShieldCheck size={23} />
          </span>
          <div>
            <h3>{auditEnabled ? 'Check audit integrity' : 'Inspect activity history'}</h3>
            <p>
              {auditEnabled
                ? 'Verify the retained history, then inspect who changed what.'
                : 'Inspect the recorded actions across colleges.'}
            </p>
          </div>
          <ArrowRight size={18} />
        </Link>
        <Link className="officer-task" to="/records">
          <span className="task-icon">
            <FileClock size={23} />
          </span>
          <div>
            <h3>Inspect student enrolments</h3>
            <p>Read admission states and record history. College staff handle corrections.</p>
          </div>
          <ArrowRight size={18} />
        </Link>
      </div>
      <section className="panel">
        <div className="portal-section-heading">
          <div>
            <h2>Intake across colleges</h2>
            <p>Recorded active admissions compared with each programme's basic intake.</p>
          </div>
          <Link to="/programmes">
            All programmes <ArrowRight size={14} />
          </Link>
        </div>
        {data?.programmes.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>College / programme</th>
                  <th>Active / intake</th>
                  <th>Position</th>
                </tr>
              </thead>
              <tbody>
                {[...data.programmes]
                  .sort((a, b) => b.excess - a.excess)
                  .map((programme) => (
                    <tr key={programme.id}>
                      <td>
                        <strong>
                          {schools.data?.find((s) => s.id === programme.institution_id)?.name ||
                            'College'}
                        </strong>
                        <small>
                          {programme.programme} · {programme.academic_year}
                        </small>
                      </td>
                      <td>
                        {programme.active} / {programme.approved}
                      </td>
                      <td>
                        <span className={`status-pill ${programme.excess ? 'attention' : 'good'}`}>
                          {programme.excess
                            ? `${programme.excess} above basic intake`
                            : 'Within basic intake'}
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          !dashboard.isPending &&
          !dashboard.error && (
            <EmptyState title="No programmes recorded">
              College programme data will appear after setup.
            </EmptyState>
          )
        )}
        <p className="privacy-caption">
          Includes every identity state. These are demo intake comparisons, not official eligibility
          findings.
        </p>
      </section>
      {data && (
        <details className="panel officer-data-details">
          <summary>Identity gaps, held submissions, and categories</summary>
          <p>
            Recorded admissions and held work are separate. Missing identity details do not remove
            an active admission from the count.
          </p>
          <div className="officer-quality-grid">
            <div>
              <span>Identity gaps</span>
              <strong>{data.active - (data.identity_counts.VERIFIED || 0)}</strong>
              <small>Missing, invalid, or pending</small>
            </div>
            <div>
              <span>Held candidates</span>
              <strong>{data.held_candidates}</strong>
              <small>Outside recorded admission totals</small>
            </div>
            <div>
              <span>Unassignable rows</span>
              <strong>{data.unassignable_rows}</strong>
              <small>Submitted rows needing a known target</small>
            </div>
          </div>
          {data.categories && <CategoryBreakdown categories={data.categories} />}
        </details>
      )}
    </div>
  )
}
