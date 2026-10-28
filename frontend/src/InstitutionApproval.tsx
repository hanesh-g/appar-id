import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowRight, Building2, RefreshCw, ShieldCheck } from 'lucide-react'
import { api, type User } from './api'
import Dialog from './Dialog'
import { PageIntro, QueryState, displayDate, displayTime } from './PortalUI'
import './approval.css'

interface Evidence {
  mode: 'DEMO_FIXTURE'
  catalogue_version: string
  catalogue_hash: string
  aicte_id: string
  campus: string
  approval_reference: string
  valid_from: string
  valid_until: string
  programmes: { id: string; name: string; intake: number }[]
}
interface Approval {
  institution_id: string
  institution_name: string
  institution_reference: string
  academic_year: string
  status: string
  version: number
  mode: 'DEMO_FIXTURE'
  can_approve: boolean
  evidence_digest: string
  candidate_evidence: Evidence | null
  reviewed_evidence: Evidence | null
  reviewed_at: string | null
  reviewer: string | null
  programmes: {
    id: string
    name: string
    intake: number
    source_intake: number | null
    source_matches: boolean
    admissions_enabled: boolean
  }[]
  events: { version: number; status: string; actor: string; created_at: string }[]
}
const statusNames: Record<string, string> = {
  PENDING: 'Officer review needed',
  APPROVED: 'Demo approval active',
  SUSPENDED: 'Demo access suspended',
  EXPIRED: 'Evidence has expired',
  REVIEW_REQUIRED: 'Evidence needs review',
}

export function ApprovalNotice({ year }: { year: string }) {
  const query = useQuery({
    queryKey: ['institution-approvals', year],
    queryFn: () => api<Approval[]>(`/institution-approvals?academic_year=${year}`),
    refetchInterval: 15000,
  })
  const approval = query.data?.[0]
  return (
    <div className="approval-notice" role="status">
      <ShieldCheck size={20} aria-hidden="true" />
      <div>
        <strong>
          {query.isPending
            ? 'Checking institution approval…'
            : query.error
              ? 'Institution approval could not be checked'
              : approval
                ? statusNames[approval.status]
                : 'Institution approval unavailable'}
        </strong>
        <p>
          {approval?.status === 'APPROVED'
            ? `${approval.programmes.filter((p) => p.admissions_enabled).length} of ${approval.programmes.length} programmes enabled for ${year}. Synthetic evidence only.`
            : 'New admissions need an officer-reviewed institution and programme for this year. Existing records remain available.'}
        </p>
      </div>
      <Link to="/institution-approval">
        View approval <ArrowRight size={14} />
      </Link>
    </div>
  )
}

export default function InstitutionApproval({ user }: { user: User }) {
  const [year, setYear] = useState('2026-27')
  const [review, setReview] = useState<{
    approval: Approval
    action: 'APPROVE_DEMO' | 'SUSPEND'
  } | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [feedback, setFeedback] = useState('')
  const client = useQueryClient()
  const query = useQuery({
    queryKey: ['institution-approvals', year],
    queryFn: () => api<Approval[]>(`/institution-approvals?academic_year=${year}`),
  })
  const mutation = useMutation({
    mutationFn: async () => {
      if (!review || !confirmed) throw new Error('Review the evidence and confirm your decision.')
      return api<Approval>(`/institution-approvals/${review.approval.institution_id}/decisions`, {
        method: 'POST',
        body: JSON.stringify({
          academic_year: review.approval.academic_year,
          expected_version: review.approval.version,
          evidence_digest: review.approval.evidence_digest,
          action: review.action,
        }),
      })
    },
    onSuccess: (result) => {
      setFeedback(`${result.institution_name}: ${statusNames[result.status]}.`)
      setReview(null)
      void client.invalidateQueries()
    },
  })
  const evidence = review?.approval.candidate_evidence
  return (
    <div className="institution-approval">
      <PageIntro
        eyebrow="INSTITUTION ONBOARDING"
        title="Institution approval"
        action={
          <button className="secondary" onClick={() => void query.refetch()}>
            <RefreshCw size={15} /> Refresh approvals
          </button>
        }
      >
        {user.role === 'officer'
          ? 'Review the college, academic year, and programme evidence before enabling admission submissions.'
          : 'See whether your institution and programmes are enabled for admission submissions.'}
      </PageIntro>
      <div className="approval-scope">
        <ShieldCheck size={23} aria-hidden="true" />
        <div>
          <strong>Simulated AICTE approval review</strong>
          <p>
            These colleges, identifiers, and approval references are invented. This workflow uses a
            synthetic catalogue, not an AICTE connection or official approval.
          </p>
        </div>
      </div>
      <div className="filter-bar">
        <label>
          Academic year
          <select
            value={year}
            onChange={(e) => {
              setYear(e.target.value)
              setFeedback('')
            }}
          >
            <option>2026-27</option>
            <option>2027-28</option>
          </select>
        </label>
        <span className="subtle">Only an officer can record an approval decision.</span>
      </div>
      {feedback && (
        <div className="notice success" role="status">
          {feedback}
        </div>
      )}
      <QueryState
        pending={query.isPending}
        error={query.error}
        retry={() => void query.refetch()}
      />
      {query.data?.map((approval) => (
        <article className="panel approval-card" key={approval.institution_id}>
          <div className="approval-card-heading">
            <div>
              <span className="eyebrow">
                {approval.institution_reference} · {year}
              </span>
              <h2>
                <Building2 size={22} aria-hidden="true" /> {approval.institution_name}
              </h2>
            </div>
            <span
              className={`status-pill ${approval.status === 'APPROVED' ? 'good' : 'attention'}`}
            >
              {statusNames[approval.status]}
            </span>
          </div>
          <p>
            {approval.status === 'APPROVED'
              ? 'Admissions are enabled only for programmes that still match the reviewed evidence.'
              : 'New admission submissions are blocked. Existing records and history remain available.'}
          </p>
          {approval.candidate_evidence ? (
            <dl className="approval-facts">
              <div>
                <dt>Synthetic institution ID</dt>
                <dd>{approval.candidate_evidence.aicte_id}</dd>
              </div>
              <div>
                <dt>Campus in demo source</dt>
                <dd>{approval.candidate_evidence.campus}</dd>
              </div>
              <div>
                <dt>Synthetic approval reference</dt>
                <dd>{approval.candidate_evidence.approval_reference}</dd>
              </div>
              <div>
                <dt>Evidence validity</dt>
                <dd>
                  {displayDate(approval.candidate_evidence.valid_from)} –{' '}
                  {displayDate(approval.candidate_evidence.valid_until)}
                </dd>
              </div>
            </dl>
          ) : (
            <div className="notice">
              No matching synthetic evidence for this institution and year. This is an unverified
              state, not an official finding of non-approval.
            </div>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Programme</th>
                  <th>Configured / source intake</th>
                  <th>Admission access</th>
                </tr>
              </thead>
              <tbody>
                {approval.programmes.map((programme) => {
                  return (
                    <tr key={programme.id}>
                      <td>
                        <strong>{programme.name}</strong>
                        <small>{year}</small>
                      </td>
                      <td>
                        {programme.intake} / {programme.source_intake ?? 'No source entry'}
                      </td>
                      <td>
                        <span
                          className={`status-pill ${programme.admissions_enabled ? 'good' : 'attention'}`}
                        >
                          {programme.admissions_enabled
                            ? 'Enabled in demo'
                            : programme.source_matches
                              ? 'Awaiting officer review'
                              : 'Evidence does not match'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
                {!approval.programmes.length && (
                  <tr>
                    <td colSpan={3}>No programmes configured for this year.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          {approval.reviewed_at && (
            <p className="privacy-caption">
              Last decision: {approval.reviewer} · {displayTime(approval.reviewed_at)} · Version{' '}
              {approval.version}
            </p>
          )}
          {user.role === 'officer' ? (
            <div className="actions">
              <button
                className="primary"
                disabled={!approval.can_approve}
                onClick={() => {
                  setReview({ approval, action: 'APPROVE_DEMO' })
                  setConfirmed(false)
                  mutation.reset()
                }}
              >
                Review demo evidence <ArrowRight size={15} />
              </button>
              {approval.status === 'APPROVED' && (
                <button
                  className="secondary"
                  onClick={() => {
                    setReview({ approval, action: 'SUSPEND' })
                    setConfirmed(false)
                    mutation.reset()
                  }}
                >
                  Suspend demo access
                </button>
              )}
            </div>
          ) : (
            <p className="privacy-caption">
              Your officer reviews this evidence. Changing a programme or intake does not update
              approval automatically.
            </p>
          )}
          <details className="approval-history">
            <summary>Evidence and decision history</summary>
            <p>
              Source: {approval.candidate_evidence?.catalogue_version ?? 'No source match'} ·
              Synthetic fixture only.
            </p>
            {approval.reviewed_evidence && (
              <p>
                Retained reviewed reference: {approval.reviewed_evidence.approval_reference}.
                Reviewed programme intake:{' '}
                {approval.reviewed_evidence.programmes
                  .map((p) => `${p.name}: ${p.intake}`)
                  .join('; ')}
                .
              </p>
            )}
            {approval.events.length ? (
              approval.events.map((event) => (
                <p key={event.version}>
                  Version {event.version} ·{' '}
                  {event.status === 'APPROVED' ? 'Demo access approved' : 'Demo access suspended'} ·{' '}
                  {event.actor} · {displayTime(event.created_at)}
                </p>
              ))
            ) : (
              <p>No decisions recorded yet.</p>
            )}
          </details>
        </article>
      ))}
      {review && (
        <Dialog
          title={
            review.action === 'APPROVE_DEMO'
              ? 'Review synthetic approval evidence'
              : 'Suspend admission submissions'
          }
          close={() => {
            if (!mutation.isPending) setReview(null)
          }}
        >
          <p>
            <strong>{review.approval.institution_name}</strong> · {review.approval.academic_year}
          </p>
          <div className="approval-scope">
            <p>
              {review.action === 'APPROVE_DEMO'
                ? 'This enables demo submissions for the matching programmes below. It does not verify real AICTE approval or the identity of a college representative.'
                : 'New uploads, commits, corrections and identity retries will be blocked. Existing admissions remain readable; historical status updates remain available.'}
            </p>
          </div>
          {review.action === 'APPROVE_DEMO' && evidence && (
            <>
              <p>
                {evidence.aicte_id} · {evidence.campus}
                <br />
                Reference: {evidence.approval_reference}
                <br />
                Valid: {displayDate(evidence.valid_from)} – {displayDate(evidence.valid_until)}
              </p>
              <ul>
                {evidence.programmes.map((p) => (
                  <li key={p.id}>
                    {p.name} · Intake {p.intake}
                  </li>
                ))}
              </ul>
              <p>Source: {evidence.catalogue_version} · Synthetic fixture.</p>
            </>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate()
            }}
          >
            <label className="approval-confirm">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              {review.action === 'APPROVE_DEMO'
                ? 'I reviewed the synthetic evidence and matching programmes.'
                : 'I understand that this blocks new admission submissions.'}
            </label>
            {mutation.error && (
              <div className="notice error" role="alert">
                {mutation.error.message} Refresh approvals and open the review again if evidence
                changed.
              </div>
            )}
            <button className="primary" disabled={!confirmed || mutation.isPending}>
              {mutation.isPending
                ? 'Saving decision…'
                : review.action === 'APPROVE_DEMO'
                  ? 'Approve demo access'
                  : 'Confirm suspension'}
            </button>
          </form>
        </Dialog>
      )}
    </div>
  )
}
