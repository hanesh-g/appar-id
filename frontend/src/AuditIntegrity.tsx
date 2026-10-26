import { useMutation } from '@tanstack/react-query'
import { api } from './api'

interface Verification {
  verified: boolean
  checked_events: number
  through_sequence: number
  last_event_hash: string
  legacy_events: number
  first_broken_sequence: number | null
  reason: string
  scope: string
}

export default function AuditIntegrity() {
  const check = useMutation({ mutationFn: () => api<Verification>('/audit-events/verify') })
  const result = check.data
  return (
    <section className="panel">
      <div className="section-title">
        <div>
          <h2>Audit integrity</h2>
          <p>Check the retained chain at a consistent database snapshot.</p>
        </div>
        <button className="secondary" disabled={check.isPending} onClick={() => check.mutate()}>
          Verify audit chain
        </button>
      </div>
      {check.error && (
        <p role="alert" className="notice error">
          {check.error.message}
        </p>
      )}
      {result && (
        <div role="status" className={`notice ${result.verified ? 'success' : 'error'}`}>
          {result.reason === 'NO_CHAINED_EVENTS'
            ? 'No chained events yet.'
            : result.verified
              ? `Integrity check passed for ${result.checked_events} events through sequence ${result.through_sequence}.`
              : `Integrity check failed: ${result.reason.replaceAll('_', ' ').toLowerCase()}.`}
          {result.first_broken_sequence !== null && (
            <p>
              First detected failure:{' '}
              {result.first_broken_sequence === 0
                ? 'legacy snapshot'
                : `sequence ${result.first_broken_sequence}`}
              .
            </p>
          )}
          <p>
            Latest digest: {result.last_event_hash.slice(0, 16)}… · Legacy snapshot:{' '}
            {result.legacy_events} events.
          </p>
          <p>{result.scope}</p>
        </div>
      )}
    </section>
  )
}
