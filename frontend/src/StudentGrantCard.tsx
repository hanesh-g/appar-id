import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Dialog from './Dialog'
import { api } from './api'
import { displayTime } from './PortalUI'
import { fieldLabels, purposeLabels, type Grant, type IssuedGrant } from './consent'

export default function GrantCard({
  grant,
  issued,
  revoked,
}: {
  grant: Grant
  issued: (data: IssuedGrant) => void
  revoked: (id: string) => void
}) {
  const [confirm, setConfirm] = useState<'revoke' | 'reissue' | null>(null)
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
      setConfirm(null)
      void client.invalidateQueries({ queryKey: ['consent'] })
    },
  })
  const expired = new Date(grant.expires_at).getTime() <= Date.now()
  return (
    <article className="panel grant-row">
      <div className="section-title">
        <div>
          <h3>{grant.verifier_organisation}</h3>
          <p>{purposeLabels[grant.purpose]}</p>
        </div>
        <span className={`status-pill ${grant.revoked_at || expired ? 'quiet' : 'good'}`}>
          {grant.revoked_at
            ? 'Sharing stopped'
            : expired
              ? 'Link expired'
              : 'Within sharing period'}
        </span>
      </div>
      <div className="shared-field-tags">
        {grant.allowed_fields.map((f) => (
          <span key={f}>{fieldLabels[f]}</span>
        ))}
      </div>
      <p className="subtle">Expires {displayTime(grant.expires_at)}</p>
      <div className="actions">
        {!grant.revoked_at && !expired && (
          <button className="secondary stop-sharing" onClick={() => setConfirm('revoke')}>
            Stop sharing
          </button>
        )}
        {grant.can_reissue && (
          <button className="text-button" onClick={() => setConfirm('reissue')}>
            Replace lost link
          </button>
        )}
      </div>
      {confirm && (
        <Dialog
          title={confirm === 'revoke' ? 'Stop sharing this record?' : 'Replace your sharing link?'}
          close={() => {
            if (!action.isPending) setConfirm(null)
          }}
        >
          <p>
            {confirm === 'revoke'
              ? `This will stop future checks by ${grant.verifier_organisation}. Information already viewed cannot be taken back.`
              : 'The previous link will stop working. The new link shares the same fields for up to 15 minutes.'}
          </p>
          {action.error && (
            <p className="notice error" role="alert">
              {action.error.message}
            </p>
          )}
          <div className="dialog-actions">
            <button
              className="secondary"
              disabled={action.isPending}
              onClick={() => setConfirm(null)}
            >
              Keep current access
            </button>
            <button
              className="primary"
              disabled={action.isPending}
              onClick={() => action.mutate(confirm)}
            >
              {action.isPending
                ? 'Saving…'
                : confirm === 'revoke'
                  ? 'Confirm stop sharing'
                  : 'Replace link'}
            </button>
          </div>
        </Dialog>
      )}
    </article>
  )
}
