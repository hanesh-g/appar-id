import { GraduationCap, ShieldCheck } from 'lucide-react'
import type { OwnRecord } from './consent'
import { displayDate, StatusPill } from './PortalUI'

export default function StudentRecordCard({
  record,
  studentName,
}: {
  record: OwnRecord
  studentName: string
}) {
  return (
    <article className="student-record-card" aria-label="Student record card">
      <header>
        <span>
          <GraduationCap size={21} />
          APAAR WORKSPACE
        </span>
        <b>DEMO RECORD</b>
      </header>
      <div className="student-record-identity">
        <span className="student-record-avatar">{studentName.slice(0, 1)}</span>
        <div>
          <span className="eyebrow">STUDENT WORKSPACE ACCOUNT</span>
          <h3>{studentName}</h3>
          <p>{record.fields.institution_name}</p>
        </div>
      </div>
      <div className="student-record-course">
        <span className="eyebrow">PROGRAMME</span>
        <h3>{record.fields.programme}</h3>
        <StatusPill value={record.fields.admission_status} />
      </div>
      <dl>
        <div>
          <dt>Academic year</dt>
          <dd>{record.fields.academic_year}</dd>
        </div>
        <div>
          <dt>Starts</dt>
          <dd>{displayDate(record.fields.start_date)}</dd>
        </div>
        <div>
          <dt>Masked APAAR</dt>
          <dd>{record.fields.masked_apaar}</dd>
        </div>
        <div>
          <dt>Identity check</dt>
          <dd>
            <ShieldCheck size={14} />
            Simulated match
          </dd>
        </div>
      </dl>
      <footer>
        Your personal record summary.
        <br />
        Not an official APAAR ID or certificate.
      </footer>
    </article>
  )
}
