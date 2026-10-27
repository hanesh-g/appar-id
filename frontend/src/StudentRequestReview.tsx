import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './api'
import { displayTime, FieldPicker, StatusPill } from './PortalUI'
import {
  fieldLabels,
  purposeLabels,
  type FieldName,
  type StudentRequest,
  type IssuedGrant,
} from './consent'

export default function RequestCard({
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
    <article className="panel request-review">
      <div className="section-title">
        <div>
          <div className="eyebrow">REQUESTED BY</div>
          <h3>{item.verifier_organisation}</h3>
        </div>
        <StatusPill value={item.status} />
      </div>
      <dl className="request-facts">
        <div>
          <dt>Purpose</dt>
          <dd>{purposeLabels[item.purpose]}</dd>
        </div>
        <div>
          <dt>Your record</dt>
          <dd>
            {item.record
              ? `${item.record.fields.programme} · ${item.record.fields.institution_name}`
              : 'Ask your college to review this record'}
          </dd>
        </div>
      </dl>
      {item.status === 'PENDING' ? (
        <>
          <FieldPicker
            fields={item.requested_fields}
            selected={selected}
            change={setSelected}
            values={item.record?.fields}
            disabled={action.isPending || !item.record}
          />
          <div className="approval-bottom">
            <label className="portal-field">
              Allow access for
              <select
                aria-label="Allow access for"
                value={minutes}
                onChange={(e) => setMinutes(Number(e.target.value))}
              >
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={60}>60 minutes</option>
              </select>
            </label>
            <div className="actions">
              <button
                className="secondary"
                disabled={action.isPending}
                onClick={() => action.mutate('deny')}
              >
                Decline request
              </button>
              <button
                className="primary"
                disabled={action.isPending || !selected.length || !item.record}
                onClick={() => action.mutate('approve')}
              >
                {action.isPending ? 'Saving…' : 'Approve selected fields'}
              </button>
            </div>
          </div>
          <p className="privacy-caption">
            <ShieldCheck size={14} />
            Only selected fields will be shared. You can stop sharing later.
          </p>
        </>
      ) : (
        <p className="subtle">
          Requested fields: {item.requested_fields.map((f) => fieldLabels[f]).join(', ')}
        </p>
      )}
      <p className="request-deadline">Request expires {displayTime(item.expires_at)}</p>
      {action.error && (
        <p className="notice error" role="alert">
          {action.error.message}
        </p>
      )}
    </article>
  )
}
