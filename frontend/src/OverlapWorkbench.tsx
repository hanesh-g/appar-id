import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Page } from './api'

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
const label = (value: string) => value.replaceAll('_', ' ').toLowerCase()

function Decision({ review }: { review: Review }) {
  const client = useQueryClient()
  const change = useMutation({
    mutationFn: (status: string) =>
      api(`/overlap-reviews/${review.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          expected_version: review.version,
          status,
          reason: (
            {
              REVIEWED_PERMITTED_DUAL: 'DEMO_DUAL_REVIEW',
              REVIEWED_TRANSFER_LAG: 'TRANSFER_RECORD_LAG',
              ESCALATED: 'NEEDS_MORE_EVIDENCE',
            } as Record<string, string>
          )[status],
          policy_reference: 'DEMO_INTERVAL_POLICY_V1',
        }),
      }),
    onSuccess: () => client.invalidateQueries(),
  })
  return (
    <>
      <div className="actions">
        <button
          className="secondary"
          disabled={change.isPending}
          onClick={() => change.mutate('REVIEWED_PERMITTED_DUAL')}
        >
          Reviewed: permitted dual
        </button>
        <button
          className="secondary"
          disabled={change.isPending}
          onClick={() => change.mutate('REVIEWED_TRANSFER_LAG')}
        >
          Reviewed: transfer lag
        </button>
        <button
          className="secondary"
          disabled={change.isPending}
          onClick={() => change.mutate('ESCALATED')}
        >
          Needs more evidence
        </button>
      </div>
      {change.error && (
        <p role="alert" className="notice error">
          {change.error.message}
        </p>
      )}
    </>
  )
}

export default function OverlapWorkbench() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['overlaps', status, page],
    queryFn: () =>
      api<Page<Review>>(`/overlap-reviews?page=${page}${status ? `&status=${status}` : ''}`),
    refetchInterval: 15000,
  })
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">OFFICER REVIEW</div>
          <h1>Enrolment interval reviews</h1>
          <p>
            Review recorded date intersections. An overlap does not establish fraud or disallowed
            dual study.
          </p>
        </div>
      </header>
      <p className="notice">
        Synthetic identities and inclusive demo dates. Decisions use DEMO_INTERVAL_POLICY_V1 and are
        not official eligibility findings. A changed record reopens the review.
      </p>
      <div className="filter-bar">
        <label htmlFor="overlap-status">Review status</label>
        <select
          id="overlap-status"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value)
            setPage(1)
          }}
        >
          <option value="">All reviews</option>
          {[
            'OPEN',
            'ESCALATED',
            'REVIEWED_PERMITTED_DUAL',
            'REVIEWED_TRANSFER_LAG',
            'NO_LONGER_OVERLAPPING',
          ].map((value) => (
            <option key={value} value={value}>
              {label(value)}
            </option>
          ))}
        </select>
        <button className="secondary" onClick={() => query.refetch()}>
          Refresh reviews
        </button>
      </div>
      {query.error && (
        <p role="alert" className="notice error">
          {query.error.message}
        </p>
      )}
      {query.isPending && <p role="status">Loading interval evidence…</p>}
      {query.data?.total === 0 && (
        <section className="panel">
          <p>No matching date-interval reviews.</p>
        </section>
      )}
      {query.data?.items.map((review) => (
        <section className="panel overlap-review" key={review.id}>
          <div className="section-title">
            <div>
              <h2>{review.apaar_masked}</h2>
              <p>
                {label(review.status)} · Evidence version {review.version}
              </p>
            </div>
            <span>{review.scheduled ? 'Scheduled interval' : 'Recorded interval'}</span>
          </div>
          <p>
            {review.status === 'NO_LONGER_OVERLAPPING' ? 'Previous intersection' : 'Intersection'}:{' '}
            {review.overlap_start} to {review.overlap_end || 'open-ended'}.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Institution</th>
                  <th>Programme</th>
                  <th>Recorded dates</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {review.records.map((record, index) => (
                  <tr key={index}>
                    <td>{record.institution}</td>
                    <td>{record.programme}</td>
                    <td>
                      {record.start_date} to {record.end_date || 'open-ended'}
                    </td>
                    <td>{label(record.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {review.status !== 'NO_LONGER_OVERLAPPING' && <Decision review={review} />}
        </section>
      ))}
      <div className="filter-bar">
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
    </>
  )
}
