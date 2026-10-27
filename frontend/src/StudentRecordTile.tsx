import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Building2, CheckCircle2, Clock3, FileCheck2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import Dialog from './Dialog'
import StudentRecordCard from './StudentRecordCard'
import { api } from './api'
import { CopyButton, displayTime, QueryState, StatusPill } from './PortalUI'
import type { OwnRecord } from './consent'

export default function RecordCard({
  record,
  studentName,
}: {
  record: OwnRecord
  studentName: string
}) {
  const [open, setOpen] = useState(false)
  const [viewCard, setViewCard] = useState(false)
  const create = useMutation({
    mutationFn: () =>
      api<{ handle: string; expires_at: string }>(`/me/enrolments/${record.id}/request-handles`, {
        method: 'POST',
        body: JSON.stringify({ expected_version: record.version }),
      }),
  })
  function start() {
    setOpen(true)
    create.mutate()
  }
  return (
    <article className="record-tile">
      <div className="record-tile-top">
        <span className="record-icon">
          <FileCheck2 size={22} />
        </span>
        <StatusPill value={record.fields.admission_status} />
      </div>
      <h3>{record.fields.programme}</h3>
      <p className="record-college">
        <Building2 size={14} />
        {record.fields.institution_name}
      </p>
      <div className="record-meta">
        <span>{record.fields.academic_year}</span>
        <span>
          <CheckCircle2 size={13} />
          Demo identity matched
        </span>
      </div>
      <div className="record-actions">
        <button className="primary" onClick={start}>
          Start sharing <ArrowRight size={15} />
        </button>
        <button className="text-button" onClick={() => setViewCard(true)}>
          View student card
        </button>
      </div>
      {viewCard && (
        <Dialog title="Your student card" close={() => setViewCard(false)}>
          <StudentRecordCard record={record} studentName={studentName} />
          <div className="dialog-actions">
            <button
              className="primary"
              onClick={() => {
                setViewCard(false)
                start()
              }}
            >
              Start sharing <ArrowRight size={15} />
            </button>
          </div>
        </Dialog>
      )}
      {open && (
        <Dialog title="Share your student record" close={() => setOpen(false)}>
          <div className="share-record-context">
            <strong>{record.fields.programme}</strong>
            <p>{record.fields.institution_name}</p>
          </div>
          <QueryState
            pending={create.isPending}
            error={create.error}
            retry={() => create.mutate()}
          />
          {create.data && (
            <>
              <div className="dialog-step">
                <span>1</span>
                <div>
                  <h3>Give this code to your verifier</h3>
                  <p>It lets them request your permission. It does not share any record fields.</p>
                </div>
              </div>
              <label className="portal-field">
                Request code
                <input
                  aria-label="Request code"
                  className="request-code"
                  readOnly
                  value={create.data.handle}
                  autoComplete="off"
                />
              </label>
              <div className="code-copy-row">
                <CopyButton value={create.data.handle} label="Copy request code" />
              </div>
              <p className="code-expiry">
                <Clock3 size={14} />
                One use · Expires {displayTime(create.data.expires_at)}
              </p>
              <div className="dialog-step">
                <span>2</span>
                <div>
                  <h3>Review their request</h3>
                  <p>
                    Check the organisation and purpose, then choose the fields and how long to share
                    them.
                  </p>
                  <Link className="text-button" to="/requests" onClick={() => setOpen(false)}>
                    Go to requests <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </>
          )}
        </Dialog>
      )}
    </article>
  )
}
