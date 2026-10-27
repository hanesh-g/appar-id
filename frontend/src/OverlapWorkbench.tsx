import { useState } from 'react'
import { ClipboardCheck, RefreshCw, ArrowRight } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Page } from './api'
import Dialog from './Dialog'
import { displayDate, EmptyState, PageIntro, QueryState, StatusPill } from './PortalUI'

interface Review {
  id: string
  version: number
  status: string
  overlap_start: string
  overlap_end: string | null
  scheduled: boolean
  apaar_masked: string
  review_reason: string | null
  records: {
    institution: string
    programme: string
    start_date: string
    end_date: string | null
    status: string
    version: number
  }[]
}
const outcomes = {
  REVIEWED_PERMITTED_DUAL: {
    label: 'Dual study reviewed',
    reason: 'DEMO_DUAL_REVIEW',
    help: 'Record that you reviewed the intersection as permitted dual study under this demo assumption.',
  },
  REVIEWED_TRANSFER_LAG: {
    label: 'Transfer delay reviewed',
    reason: 'TRANSFER_RECORD_LAG',
    help: 'Record that you reviewed the intersection as a delay in updating transfer records.',
  },
  ESCALATED: {
    label: 'More evidence needed',
    reason: 'NEEDS_MORE_EVIDENCE',
    help: 'Keep the case flagged for further investigation. No admission is rejected.',
  },
}
type Outcome = keyof typeof outcomes
function Decision({ review, saved }: { review: Review; saved: (label: string) => void }) {
  const [open, setOpen] = useState(false)
  const [outcome, setOutcome] = useState<Outcome | ''>('')
  const client = useQueryClient()
  const change = useMutation({
    mutationFn: () =>
      api(`/overlap-reviews/${review.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          expected_version: review.version,
          status: outcome,
          reason: outcomes[outcome as Outcome].reason,
          policy_reference: 'DEMO_INTERVAL_POLICY_V1',
        }),
      }),
    onSuccess: () => {
      setOpen(false)
      saved(outcomes[outcome as Outcome].label)
      void client.invalidateQueries({ queryKey: ['overlaps'] })
    },
  })
  return (
    <>
      <button className="primary" onClick={() => setOpen(true)}>
        Review this overlap <ArrowRight size={15} />
      </button>
      {open && (
        <Dialog
          title="Record a review decision"
          close={() => {
            if (!change.isPending) setOpen(false)
          }}
        >
          <p>Review for {review.apaar_masked}. Both admissions will remain recorded.</p>
          <label className="portal-field">
            Review outcome
            <select
              aria-label="Review outcome"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value as Outcome | '')}
            >
              <option value="">Choose an outcome</option>
              {Object.entries(outcomes).map(([value, item]) => (
                <option key={value} value={value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          {outcome && <p className="decision-help">{outcomes[outcome].help}</p>}
          <p className="fine-print">
            This is a synthetic demo decision. It does not establish official eligibility.
          </p>
          {change.error && (
            <p role="alert" className="notice error">
              {change.error.message}
            </p>
          )}
          <div className="dialog-actions">
            <button
              className="secondary"
              disabled={change.isPending}
              onClick={() => setOpen(false)}
            >
              Cancel
            </button>
            <button
              className="primary"
              disabled={change.isPending || !outcome}
              onClick={() => change.mutate()}
            >
              {change.isPending ? 'Saving…' : 'Save review'}
            </button>
          </div>
        </Dialog>
      )}
    </>
  )
}

export default function OverlapWorkbench() {
  const [status, setStatus] = useState('OPEN')
  const [page, setPage] = useState(1)
  const [saved, setSaved] = useState('')
  const query = useQuery({
    queryKey: ['overlaps', 'list', status, page],
    queryFn: () =>
      api<Page<Review>>(`/overlap-reviews?page=${page}${status ? `&status=${status}` : ''}`),
    refetchInterval: 15000,
  })
  return (
    <div className="overlap-workspace">
      <PageIntro
        eyebrow="OFFICER REVIEW QUEUE"
        title="Review overlapping enrolments"
        action={
          <button className="secondary" onClick={() => void query.refetch()}>
            <RefreshCw size={15} />
            Refresh reviews
          </button>
        }
      >
        Compare records that share a verified demo identity and overlapping dates. Choose a review
        outcome after checking the evidence.
      </PageIntro>
      <div className="review-guidance">
        <ClipboardCheck size={22} />
        <p>
          <strong>A date overlap is a signal to review.</strong> It does not by itself show fraud or
          a disallowed admission. Your decision keeps both admission records.
        </p>
      </div>
      <div className="portal-toolbar">
        <label className="portal-field">
          Review status
          <select
            aria-label="Review status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value)
              setPage(1)
            }}
          >
            <option value="OPEN">Needs review</option>
            <option value="">All reviews</option>
            <option value="ESCALATED">More evidence needed</option>
            <option value="REVIEWED_PERMITTED_DUAL">Reviewed: dual study</option>
            <option value="REVIEWED_TRANSFER_LAG">Reviewed: transfer delay</option>
            <option value="NO_LONGER_OVERLAPPING">Overlap ended</option>
          </select>
        </label>
        <span className="subtle">
          {query.data ? `${query.data.total} matching reviews` : 'Checking queue…'}
        </span>
      </div>
      {saved && (
        <div role="status" className="notice success">
          <strong>Review saved: {saved}.</strong> Both admission records are unchanged.
        </div>
      )}
      <QueryState
        pending={query.isPending}
        error={query.error}
        retry={() => void query.refetch()}
      />
      {query.data?.total === 0 && (
        <section className="panel">
          <EmptyState
            title={
              status === 'OPEN' ? 'No overlaps waiting for review' : 'No reviews match this filter'
            }
            action={
              <button
                className="secondary"
                onClick={() => {
                  setStatus('')
                  setPage(1)
                }}
              >
                View all reviews
              </button>
            }
          >
            New date intersections will appear when verified records overlap. Previous decisions
            remain in the review history.
          </EmptyState>
        </section>
      )}
      {query.data?.items.map((review) => (
        <section className="panel overlap-review" key={`${review.id}:${review.version}`}>
          <div className="section-title">
            <div>
              <div className="eyebrow">SHARED DEMO IDENTITY</div>
              <h2>{review.apaar_masked}</h2>
            </div>
            <StatusPill value={review.status} />
          </div>
          <div className="overlap-range">
            <span>Overlapping dates</span>
            <strong>
              {displayDate(review.overlap_start)} →{' '}
              {review.overlap_end ? displayDate(review.overlap_end) : 'No end date recorded'}
            </strong>
            {review.scheduled && <span className="status-pill quiet">Scheduled dates</span>}
          </div>
          <div className="interval-comparison">
            {review.records.map((record, index) => (
              <article className="interval-record" key={index}>
                <span className="college-marker">{index === 0 ? 'A' : 'B'}</span>
                <h3>{record.institution}</h3>
                <p>{record.programme}</p>
                <StatusPill value={record.status} />
                <dl>
                  <div>
                    <dt>Starts</dt>
                    <dd>{displayDate(record.start_date)}</dd>
                  </div>
                  <div>
                    <dt>Ends</dt>
                    <dd>
                      {record.end_date ? displayDate(record.end_date) : 'No end date recorded'}
                    </dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
          <div className="review-bottom">
            <p>Evidence version {review.version} · Check both records before saving.</p>
            {review.status !== 'NO_LONGER_OVERLAPPING' && (
              <Decision review={review} saved={setSaved} />
            )}
          </div>
        </section>
      ))}
      {Boolean(query.data && query.data.total > 50) && (
        <div className="portal-pagination">
          <button className="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>
            Previous reviews
          </button>
          <span>Page {page}</span>
          <button
            className="secondary"
            disabled={!query.data || page * 50 >= query.data.total}
            onClick={() => setPage(page + 1)}
          >
            Next reviews
          </button>
        </div>
      )}
      <details className="demo-policy-details">
        <summary>About the demo review rule</summary>
        <p>
          Uses inclusive recorded dates and DEMO_INTERVAL_POLICY_V1. A changed record can reopen a
          review. These findings are not official eligibility decisions.
        </p>
      </details>
    </div>
  )
}
