import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, type Page, type ResolutionCase } from './api'
import RuleHelp from './RuleHelp'
import CorrectionEditor from './CorrectionEditor'

const statuses = ['OPEN', 'WAITING_ON_USER', 'WAITING_ON_AUTHORITY', 'READY_TO_RECHECK', 'RESOLVED']
const owners = ['COLLEGE_STAFF', 'STUDENT_ACTION', 'UPSTREAM_AUTHORITY']
const transitions: Record<string, string[]> = {
  OPEN: ['WAITING_ON_USER', 'WAITING_ON_AUTHORITY', 'READY_TO_RECHECK'],
  WAITING_ON_USER: ['OPEN', 'READY_TO_RECHECK'],
  WAITING_ON_AUTHORITY: ['OPEN', 'READY_TO_RECHECK'],
  READY_TO_RECHECK: ['OPEN', 'WAITING_ON_USER', 'WAITING_ON_AUTHORITY', 'RESOLVED'],
  RESOLVED: ['OPEN'],
}
const label = (value: string) => value.replaceAll('_', ' ').toLowerCase()

function CaseEditor({ item }: { item: ResolutionCase }) {
  const client = useQueryClient()
  const [owner, setOwner] = useState(item.owner_type)
  const [status, setStatus] = useState(item.status)
  const change = useMutation({
    mutationFn: () =>
      api<ResolutionCase>(`/resolution-cases/${item.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          expected_version: item.version,
          owner_type: owner,
          status,
          assignee_id: owner === 'COLLEGE_STAFF' ? item.assignee_id : null,
        }),
      }),
    onSuccess: () => client.invalidateQueries(),
  })
  function submit(event: FormEvent) {
    event.preventDefault()
    change.mutate()
  }
  return (
    <form onSubmit={submit} className="form-stack">
      <div>
        <label htmlFor="case-owner">Next action owner</label>
        <select id="case-owner" value={owner} onChange={(event) => setOwner(event.target.value)}>
          {owners.map((value) => (
            <option key={value} value={value}>
              {label(value)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="case-status">Case status</label>
        <select id="case-status" value={status} onChange={(event) => setStatus(event.target.value)}>
          {[item.status, ...(transitions[item.status] || [])].map((value) => (
            <option key={value} value={value}>
              {label(value)}
            </option>
          ))}
        </select>
      </div>
      {change.error && (
        <p role="alert" className="notice error">
          {change.error.message}
        </p>
      )}
      <button className="primary" disabled={change.isPending} type="submit">
        Update case
      </button>
      <p className="fine-print">
        Routing records the next action. It does not send a message or change an official record.
        Resolution requires a successful correction or eligible simulated recheck.
      </p>
    </form>
  )
}

export default function ResolutionDesk() {
  const { id } = useParams()
  const [status, setStatus] = useState('')
  const [owner, setOwner] = useState('')
  const [page, setPage] = useState(1)
  const list = useQuery({
    queryKey: ['cases', status, owner, page],
    queryFn: () =>
      api<Page<ResolutionCase>>(
        `/resolution-cases?page=${page}${status ? `&status=${status}` : ''}${owner ? `&owner_type=${owner}` : ''}`,
      ),
  })
  const detail = useQuery({
    queryKey: ['case', id],
    queryFn: () => api<ResolutionCase>(`/resolution-cases/${id}`),
    enabled: Boolean(id),
  })
  const item = detail.data
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">CORRECTION WORKSPACE</div>
          <h1>Resolution Desk</h1>
          <p>Give each issue a next action and a traceable outcome.</p>
        </div>
      </header>
      <div className="filter-bar">
        <label>
          Filter case status
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value)
              setPage(1)
            }}
          >
            <option value="">All states</option>
            {statuses.map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Filter owner
          <select
            value={owner}
            onChange={(event) => {
              setOwner(event.target.value)
              setPage(1)
            }}
          >
            <option value="">All owners</option>
            {owners.map((value) => (
              <option key={value} value={value}>
                {label(value)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {list.error && (
        <p role="alert" className="notice error">
          {list.error.message}
        </p>
      )}
      <div className="resolution-grid">
        <section className="panel">
          <h2>Your correction work</h2>
          {list.isPending && <p role="status">Loading cases…</p>}
          {list.data && !list.data.total && (
            <p>No matching cases. Open a reported issue from a batch review.</p>
          )}
          {list.data && list.data.total > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Reference / issue</th>
                    <th>Owner</th>
                    <th>State</th>
                  </tr>
                </thead>
                <tbody>
                  {list.data.items.map((row) => (
                    <tr key={row.id}>
                      <td>
                        <Link to={`/resolution/${row.id}`}>
                          {row.student_ref || 'Unassigned row'}
                        </Link>
                        <small>{label(row.issue_code)}</small>
                      </td>
                      <td>{label(row.owner_type)}</td>
                      <td>{label(row.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="actions">
            <button className="secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>
              Previous cases
            </button>
            <span>Page {page}</span>
            <button
              className="secondary"
              disabled={!list.data || page * 50 >= list.data.total}
              onClick={() => setPage(page + 1)}
            >
              Next cases
            </button>
          </div>
        </section>
        <section className="panel">
          {detail.error && (
            <p role="alert" className="notice error">
              {detail.error.message}
            </p>
          )}
          {id && detail.isPending && <p role="status">Loading case…</p>}
          {!id && <p>Select a case to review its next action and history.</p>}
          {item && (
            <>
              <h2>Case for {item.student_ref || 'unassigned row'}</h2>
              <RuleHelp code={item.issue_code} ruleSetId={item.rule_set_id} />
              <p>
                {label(item.subject_kind)} · Episode {item.episode} · Version {item.version}
              </p>
              {item.origin_batch_id && (
                <p>
                  <Link to={`/batches/${item.origin_batch_id}`}>
                    Open original submission and correction CSV
                  </Link>
                </p>
              )}
              {item.resolution_reason && (
                <p>
                  Outcome: {label(item.resolution_reason)} ·{' '}
                  {item.evidence_kind === 'MOCK' ? 'Simulated verification' : 'Local correction'}
                </p>
              )}
              <CaseEditor key={`${item.id}:${item.version}`} item={item} />
              {item.status !== 'RESOLVED' && (
                <CorrectionEditor key={`correction:${item.id}:${item.version}`} item={item} />
              )}
              <h3>Case history</h3>
              <p className="fine-print">Latest 100 changes. Original reports remain available.</p>
              <ol>
                {item.events?.map((event) => (
                  <li key={event.version}>
                    <strong>{label(event.new_status)}</strong> — {label(event.reason)}
                    <small>{new Date(event.created_at).toLocaleString()}</small>
                  </li>
                ))}
              </ol>
            </>
          )}
        </section>
      </div>
    </>
  )
}
