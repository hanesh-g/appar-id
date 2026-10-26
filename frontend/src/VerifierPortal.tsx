import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Page } from './api'
import {
  extractGrantToken,
  fieldLabels,
  purposeLabels,
  type FieldName,
  type Purpose,
  type SubmittedRequest,
} from './consent'
import { Pager } from './StudentPortal'

export default function VerifierPortal({
  initialToken,
  clearToken,
}: {
  initialToken: string
  clearToken: () => void
}) {
  const [handle, setHandle] = useState('')
  const [purpose, setPurpose] = useState<Purpose>('ADMISSION_CONFIRMATION')
  const [requested, setRequested] = useState<FieldName[]>([])
  const [requestKey, setRequestKey] = useState(() => crypto.randomUUID())
  const [link, setLink] = useState(initialToken)
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
      setLink('')
      clearToken()
    },
  })
  const submissions = useQuery({
    queryKey: ['consent', 'submissions', page],
    queryFn: () => api<Page<SubmittedRequest>>(`/me/verification-requests/submitted?page=${page}`),
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
  return (
    <>
      <header className="page-heading">
        <div>
          <div className="eyebrow">VERIFIER WORKSPACE</div>
          <h1>Request and verify</h1>
          <p>
            Ask the student for a request code. They choose whether to approve your purpose and
            fields.
          </p>
        </div>
      </header>
      <section className="panel consent-card">
        <h2>Request student consent</h2>
        <form className="form-stack" onSubmit={request}>
          <label>
            Student request code
            <input
              aria-label="Student request code"
              type="password"
              autoComplete="off"
              required
              maxLength={200}
              value={handle}
              onChange={(e) => {
                setHandle(e.target.value)
                changed()
              }}
            />
          </label>
          <label>
            Purpose
            <select
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
          </label>
          <fieldset>
            <legend>Fields to request</legend>
            {(Object.keys(fieldLabels) as FieldName[]).map((field) => (
              <label key={field} className="consent-option">
                <input
                  type="checkbox"
                  checked={requested.includes(field)}
                  onChange={(e) => {
                    setRequested(
                      e.target.checked
                        ? [...requested, field]
                        : requested.filter((f) => f !== field),
                    )
                    changed()
                  }}
                />
                {fieldLabels[field]}
              </label>
            ))}
          </fieldset>
          <button
            className="primary"
            disabled={submit.isPending || !requested.length}
            type="submit"
          >
            Submit consent request
          </button>
        </form>
        {submit.isSuccess && (
          <p role="status" className="notice">
            Request submitted. The student can review a matching request in their workspace.
          </p>
        )}
        {submit.error && (
          <p role="alert" className="notice error">
            {submit.error.message}
          </p>
        )}
      </section>
      <section className="panel consent-card">
        <h2>Open an approved link</h2>
        <form className="form-stack" onSubmit={open}>
          <label>
            Student consent link
            <input
              aria-label="Student consent link"
              type="password"
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
          <button className="primary" disabled={resolve.isPending} type="submit">
            Verify approved fields
          </button>
        </form>
        {resolve.error && (
          <p role="alert" className="notice error">
            {resolve.error.message}
          </p>
        )}
        {resolve.data && (
          <div role="status" className="notice">
            <h3>Approved fields</h3>
            <dl>
              {Object.entries(resolve.data.fields).map(([field, value]) => (
                <div key={field}>
                  <dt>{fieldLabels[field as FieldName]}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
            <p>
              Verified at {new Date().toLocaleTimeString()}. Consent expires{' '}
              {new Date(resolve.data.valid_until).toLocaleString()}. Synthetic demo record.
            </p>
            <button className="secondary" onClick={() => resolve.reset()}>
              Hide result
            </button>
          </div>
        )}
      </section>
      <h2>Your submitted requests</h2>
      {submissions.error && (
        <p role="alert" className="notice error">
          {submissions.error.message}
        </p>
      )}
      {submissions.data?.items.map((item) => (
        <article className="panel consent-card" key={item.id}>
          <strong>{purposeLabels[item.purpose]}</strong>
          <p>
            {item.status} · {item.requested_fields.map((f) => fieldLabels[f]).join(', ')}
          </p>
        </article>
      ))}
      <Pager page={page} total={submissions.data?.total || 0} change={setPage} />
    </>
  )
}
