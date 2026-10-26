import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Issue, type ResolutionCase } from './api'
import Dialog from './Dialog'

interface Context {
  case_version: number
  fields: Record<string, string>
  immutable_fields: string[]
}
interface Preview {
  id: string
  case_version: number
  expires_at: string
  changes: { field: string; before: string; after: string }[]
  issues: Issue[]
  outcome: Record<string, number>
  active_delta: number
  can_apply: boolean
}
const labels: Record<string, string> = {
  student_ref: 'Student reference',
  apaar_id: 'APAAR ID',
  student_name: 'Student name',
  date_of_birth: 'Date of birth',
  programme: 'Programme',
  academic_year: 'Academic year',
  admission_date: 'Admission date',
  start_date: 'Start date',
  end_date: 'End date',
  status: 'Admission status',
  seat_type: 'Seat type',
  supernumerary: 'Supernumerary flag',
  nri: 'NRI flag',
  oci: 'OCI flag',
  foreign_national: 'Foreign-national flag',
}

function CorrectionForm({
  item,
  context,
  done,
}: {
  item: ResolutionCase
  context: Context
  done: () => void
}) {
  const [values, setValues] = useState(context.fields)
  const client = useQueryClient()
  const preview = useMutation({
    mutationFn: () =>
      api<Preview>(`/resolution-cases/${item.id}/correction-previews`, {
        method: 'POST',
        body: JSON.stringify({
          expected_version: context.case_version,
          changes: Object.fromEntries(
            Object.entries(values).filter(([key, value]) => value !== context.fields[key]),
          ),
        }),
      }),
  })
  const apply = useMutation({
    mutationFn: () =>
      api(`/correction-proposals/${preview.data!.id}/apply`, {
        method: 'POST',
        body: JSON.stringify({ expected_version: preview.data!.case_version }),
      }),
    onSuccess: async () => {
      await client.invalidateQueries()
      done()
    },
  })
  const proposal = preview.data
  function submit(event: FormEvent) {
    event.preventDefault()
    preview.mutate()
  }
  return (
    <>
      <p>
        Dates use YYYY-MM-DD. Flags use Y or N. Protected identity values are masked in the
        comparison.
      </p>
      <form onSubmit={submit}>
        <div className="correction-fields">
          {Object.entries(values).map(([key, value]) => (
            <div key={key}>
              <label htmlFor={`correction-${key}`}>{labels[key] || key}</label>
              <input
                id={`correction-${key}`}
                value={value}
                type={key === 'apaar_id' ? 'password' : 'text'}
                autoComplete="off"
                maxLength={200}
                readOnly={context.immutable_fields.includes(key)}
                disabled={preview.isPending || Boolean(proposal)}
                onChange={(event) => setValues({ ...values, [key]: event.target.value })}
              />
            </div>
          ))}
        </div>
        {(preview.error || apply.error) && (
          <p role="alert" className="notice error">
            {(preview.error || apply.error)?.message} Close and reopen the editor if the record
            changed.
          </p>
        )}
        <button className="primary" disabled={preview.isPending || Boolean(proposal)} type="submit">
          Preview correction
        </button>
      </form>
      {proposal && (
        <section className="correction-preview">
          <h3>Review the exact proposed change</h3>
          {proposal.changes.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Field</th>
                    <th>Current</th>
                    <th>Proposed</th>
                  </tr>
                </thead>
                <tbody>
                  {proposal.changes.map((change) => (
                    <tr key={change.field}>
                      <td>{labels[change.field] || change.field}</td>
                      <td>{change.before}</td>
                      <td>{change.after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No field values changed.</p>
          )}
          <p>
            {proposal.outcome.created} new admissions; {proposal.outcome.updated} records updated;{' '}
            {proposal.outcome.unchanged} unchanged. Active count change:{' '}
            {proposal.active_delta > 0 ? '+' : ''}
            {proposal.active_delta}.
          </p>
          {proposal.issues.map((issue, index) => (
            <p key={index} className="notice">
              {issue.message}
            </p>
          ))}
          <p className="fine-print">
            This review expires at {new Date(proposal.expires_at).toLocaleTimeString()}. Saving
            checks the current record again. Identity checks remain simulated.
          </p>
          <div className="actions">
            <button
              className="secondary"
              disabled={apply.isPending}
              onClick={() => {
                preview.reset()
                apply.reset()
              }}
            >
              Edit values again
            </button>
            <button
              className="primary"
              disabled={!proposal.can_apply || apply.isPending}
              onClick={() => apply.mutate()}
            >
              Apply correction
            </button>
          </div>
        </section>
      )}
    </>
  )
}

export default function CorrectionEditor({ item }: { item: ResolutionCase }) {
  const [open, setOpen] = useState(false)
  const context = useQuery({
    queryKey: ['correction-context', item.id, item.version],
    queryFn: () => api<Context>(`/resolution-cases/${item.id}/correction-context`),
    enabled: open,
    gcTime: 0,
    retry: false,
  })
  return (
    <>
      <button className="secondary" onClick={() => setOpen(true)}>
        Review a correction
      </button>
      {open && (
        <Dialog title="Correct this admission record" close={() => setOpen(false)}>
          {context.isPending && <p role="status">Loading the current institution record…</p>}
          {context.error && (
            <p role="alert" className="notice error">
              {context.error.message}
            </p>
          )}
          {context.data && (
            <CorrectionForm item={item} context={context.data} done={() => setOpen(false)} />
          )}
        </Dialog>
      )}
    </>
  )
}
