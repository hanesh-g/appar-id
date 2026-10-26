import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ConsentShareCard from './ConsentShareCard'
import { api, type Page } from './api'
import {
  fieldLabels,
  purposeLabels,
  type FieldName,
  type OwnRecord,
  type StudentRequest,
  type Grant,
  type IssuedGrant,
} from './consent'

function RecordCard({ record }: { record: OwnRecord }) {
  const create = useMutation({
    mutationFn: () =>
      api<{ handle: string; expires_at: string }>(`/me/enrolments/${record.id}/request-handles`, {
        method: 'POST',
        body: JSON.stringify({ expected_version: record.version }),
      }),
  })
  return (
    <article className="panel consent-card">
      <h3>{record.fields.programme}</h3>
      <p>
        {record.fields.institution_name} · {record.fields.academic_year} ·{' '}
        {record.fields.admission_status}
      </p>
      <button className="secondary" disabled={create.isPending} onClick={() => create.mutate()}>
        Create request code
      </button>
      {create.data && (
        <div className="notice">
          <label>
            Request code
            <input
              aria-label="Request code"
              readOnly
              value={create.data.handle}
              autoComplete="off"
            />
          </label>
          <p>
            Give this code to your verifier. It expires at{' '}
            {new Date(create.data.expires_at).toLocaleTimeString()} and can be used once. You will
            review their request before any fields are shared.
          </p>
        </div>
      )}
      {create.error && (
        <p role="alert" className="notice error">
          {create.error.message}
        </p>
      )}
    </article>
  )
}

function RequestCard({
  item,
  issued,
}: {
  item: StudentRequest
  issued: (data: IssuedGrant) => void
}) {
  const [selected, setSelected] = useState<FieldName[]>([])
  const [minutes, setMinutes] = useState(15)
  const client = useQueryClient()
  const action = useMutation({
    mutationFn: (decision: 'approve' | 'deny') =>
      api<IssuedGrant | object>(`/me/verification-requests/${item.id}/${decision}`, {
        method: 'POST',
        body: JSON.stringify({
          expected_version: item.version,
          ...(decision === 'approve'
            ? {
                allowed_fields: selected,
                expires_in_minutes: minutes,
                expected_record_version: item.record?.version,
              }
            : {}),
        }),
      }),
    onSuccess: (data) => {
      if ('newly_issued' in data) issued(data as IssuedGrant)
      void client.invalidateQueries({ queryKey: ['consent'] })
    },
  })
  return (
    <article className="panel consent-card">
      <h3>{item.verifier_organisation}</h3>
      <p>
        {purposeLabels[item.purpose]} · {item.status}
      </p>
      <p>
        {item.record?.fields.programme || 'Record needs institution review'} · Request expires{' '}
        {new Date(item.expires_at).toLocaleString()}
      </p>
      {item.status === 'PENDING' && (
        <>
          <fieldset disabled={action.isPending || !item.record}>
            <legend>Select the fields you approve</legend>
            {item.requested_fields.map((field) => (
              <label className="consent-option" key={field}>
                <input
                  type="checkbox"
                  checked={selected.includes(field)}
                  onChange={(e) =>
                    setSelected(
                      e.target.checked ? [...selected, field] : selected.filter((f) => f !== field),
                    )
                  }
                />
                {fieldLabels[field]}
              </label>
            ))}
          </fieldset>
          <label>
            Access expires in
            <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value))}>
              <option value={5}>5 minutes</option>
              <option value={15}>15 minutes</option>
              <option value={60}>60 minutes</option>
            </select>
          </label>
          <div className="actions">
            <button
              className="primary"
              disabled={action.isPending || !selected.length || !item.record}
              onClick={() => action.mutate('approve')}
            >
              Approve selected fields
            </button>
            <button
              className="secondary"
              disabled={action.isPending}
              onClick={() => action.mutate('deny')}
            >
              Deny request
            </button>
          </div>
        </>
      )}
      {action.error && (
        <p role="alert" className="notice error">
          {action.error.message}
        </p>
      )}
    </article>
  )
}

function GrantCard({
  grant,
  issued,
  revoked,
}: {
  grant: Grant
  issued: (data: IssuedGrant) => void
  revoked: (id: string) => void
}) {
  const client = useQueryClient()
  const action = useMutation({
    mutationFn: (decision: 'revoke' | 'reissue') =>
      api<Grant | IssuedGrant>(`/me/consent-grants/${grant.id}/${decision}`, {
        method: 'POST',
        body: JSON.stringify({ expected_version: grant.version }),
      }),
    onSuccess: (data, decision) => {
      if ('newly_issued' in data) issued(data)
      if (decision === 'revoke') revoked(grant.id)
      void client.invalidateQueries({ queryKey: ['consent'] })
    },
  })
  const expired = new Date(grant.expires_at).getTime() <= Date.now()
  return (
    <article className="panel consent-card">
      <h3>{grant.verifier_organisation}</h3>
      <p>
        {purposeLabels[grant.purpose]} ·{' '}
        {grant.allowed_fields.map((f) => fieldLabels[f]).join(', ')}
      </p>
      <p>
        {grant.revoked_at ? 'Revoked' : expired ? 'Expired' : 'Active'} · Expires{' '}
        {new Date(grant.expires_at).toLocaleString()}
      </p>
      <div className="actions">
        {!grant.revoked_at && !expired && (
          <button
            className="secondary"
            disabled={action.isPending}
            onClick={() => action.mutate('revoke')}
          >
            Revoke access
          </button>
        )}
        {grant.can_reissue && (
          <button
            className="secondary"
            disabled={action.isPending}
            onClick={() => action.mutate('reissue')}
          >
            Replace lost link
          </button>
        )}
      </div>
      {action.error && (
        <p role="alert" className="notice error">
          {action.error.message}
        </p>
      )}
    </article>
  )
}

export default function StudentPortal() {
  const [issued, setIssued] = useState<IssuedGrant | null>(null)
  const [recordPage, setRecordPage] = useState(1)
  const [requestPage, setRequestPage] = useState(1)
  const [grantPage, setGrantPage] = useState(1)
  const [accessPage, setAccessPage] = useState(1)
  const records = useQuery({
    queryKey: ['consent', 'records', recordPage],
    queryFn: () => api<Page<OwnRecord>>(`/me/enrolments?page=${recordPage}`),
  })
  const requests = useQuery({
    queryKey: ['consent', 'requests', requestPage],
    queryFn: () => api<Page<StudentRequest>>(`/me/verification-requests?page=${requestPage}`),
    refetchInterval: 15000,
  })
  const grants = useQuery({
    queryKey: ['consent', 'grants', grantPage],
    queryFn: () => api<Page<Grant>>(`/me/consent-grants?page=${grantPage}`),
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
    refetchInterval: 15000,
  })
  function remember(data: IssuedGrant) {
    if (data.newly_issued) setIssued(data)
  }
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">STUDENT WORKSPACE</div>
          <h1>Your records and consent</h1>
          <p>
            Give a verifier a request code. Review their purpose and fields. Approve only what you
            want to share.
          </p>
        </div>
      </header>
      {[records, requests, grants, accesses].map(
        (q, i) =>
          q.error && (
            <p key={i} className="notice error" role="alert">
              {q.error.message}
            </p>
          ),
      )}
      {issued && (
        <ConsentShareCard key={issued.grant.id} value={issued} clear={() => setIssued(null)} />
      )}
      <h2>Your verified records</h2>
      {records.isPending && <p>Loading records…</p>}
      {records.data?.items.map((record) => (
        <RecordCard key={record.id} record={record} />
      ))}
      {records.data?.total === 0 && (
        <p>
          No verified records are linked to this account. Ask your institution to review your
          record.
        </p>
      )}
      <Pager page={recordPage} total={records.data?.total || 0} change={setRecordPage} />
      <h2>Verification requests</h2>
      {requests.data?.items.map((item) => (
        <RequestCard key={`${item.id}:${item.version}`} item={item} issued={remember} />
      ))}
      {requests.data?.total === 0 && <p>No requests yet.</p>}
      <Pager page={requestPage} total={requests.data?.total || 0} change={setRequestPage} />
      <h2>Your consent grants</h2>
      {grants.data?.items.map((grant) => (
        <GrantCard
          key={grant.id}
          grant={grant}
          issued={remember}
          revoked={(id) => setIssued((current) => (current?.grant.id === id ? null : current))}
        />
      ))}
      <Pager page={grantPage} total={grants.data?.total || 0} change={setGrantPage} />
      <h2>Access history</h2>
      {accesses.data?.items.map((access) => (
        <article className="panel consent-card" key={access.id}>
          <strong>{access.verifier_organisation}</strong>
          <p>
            {purposeLabels[access.purpose]} ·{' '}
            {access.disclosed_fields.map((f) => fieldLabels[f]).join(', ')} ·{' '}
            {new Date(access.accessed_at).toLocaleString()}
          </p>
        </article>
      ))}
      {accesses.data?.total === 0 && <p>No verifier has accessed your records.</p>}
      <Pager page={accessPage} total={accesses.data?.total || 0} change={setAccessPage} />
    </>
  )
}

export function Pager({
  page,
  total,
  change,
}: {
  page: number
  total: number
  change: (page: number) => void
}) {
  return total > 50 ? (
    <div className="actions">
      <button className="secondary" disabled={page === 1} onClick={() => change(page - 1)}>
        Previous
      </button>
      <span>Page {page}</span>
      <button className="secondary" disabled={page * 50 >= total} onClick={() => change(page + 1)}>
        Next
      </button>
    </div>
  ) : null
}
