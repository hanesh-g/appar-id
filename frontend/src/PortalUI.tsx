import { useId, useState, type ReactNode } from 'react'
import { Clipboard, Check, Inbox, LoaderCircle, RefreshCw } from 'lucide-react'
import { fieldLabels, type FieldName } from './consent'

export const fieldHelp: Record<FieldName, string> = {
  programme: 'Course name',
  institution_name: 'College name',
  academic_year: 'Year of admission',
  admission_status: 'Current admission state',
  start_date: 'Recorded course start date',
  masked_apaar: 'Last four digits only',
}
export function displayDate(value: string) {
  return new Date(value.length === 10 ? `${value}T00:00:00` : value).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
export function displayTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })
}
export function displayFieldValue(field: FieldName, value: string | undefined) {
  if (!value) return '—'
  if (field === 'start_date') return displayDate(value)
  if (field === 'admission_status')
    return stateNames[value] || value.replaceAll('_', ' ').toLowerCase()
  return value
}
const stateNames: Record<string, string> = {
  PENDING: 'Waiting for approval',
  APPROVED: 'Approved',
  DENIED: 'Declined',
  EXPIRED: 'Expired',
  ENROLLED: 'Enrolled',
  WITHDRAWN: 'Withdrawn',
  TRANSFERRED_OUT: 'Transferred',
  CANCELLED: 'Cancelled',
  OPEN: 'Needs review',
  ESCALATED: 'More evidence needed',
  REVIEWED_PERMITTED_DUAL: 'Reviewed: dual study',
  REVIEWED_TRANSFER_LAG: 'Reviewed: transfer delay',
  NO_LONGER_OVERLAPPING: 'Overlap ended',
}
export function StatusPill({ value }: { value: string }) {
  const tone = [
    'APPROVED',
    'ENROLLED',
    'REVIEWED_PERMITTED_DUAL',
    'REVIEWED_TRANSFER_LAG',
  ].includes(value)
    ? 'good'
    : ['PENDING', 'OPEN', 'ESCALATED'].includes(value)
      ? 'attention'
      : 'quiet'
  return (
    <span className={`status-pill ${tone}`}>
      <i aria-hidden="true" />
      {stateNames[value] || value.replaceAll('_', ' ').toLowerCase()}
    </span>
  )
}
export function PageIntro({
  eyebrow,
  title,
  children,
  action,
}: {
  eyebrow: string
  title: string
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <header className="portal-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{children}</p>
      </div>
      {action}
    </header>
  )
}
export function EmptyState({
  title,
  children,
  action,
}: {
  title: string
  children: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="portal-empty">
      <span className="empty-icon">
        <Inbox size={24} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  )
}
export function QueryState({
  pending,
  error,
  retry,
}: {
  pending: boolean
  error: Error | null
  retry: () => void
}) {
  if (error)
    return (
      <div className="notice error portal-query" role="alert">
        <span>{error.message}</span>
        <button className="secondary" onClick={retry}>
          <RefreshCw size={14} />
          Try again
        </button>
      </div>
    )
  if (pending)
    return (
      <div className="portal-loading" role="status">
        <LoaderCircle size={19} className="spin" />
        Loading your workspace…
      </div>
    )
  return null
}
export function FieldPicker({
  fields,
  selected,
  change,
  values,
  disabled = false,
}: {
  fields: FieldName[]
  selected: FieldName[]
  change: (value: FieldName[]) => void
  values?: Partial<Record<FieldName, string>>
  disabled?: boolean
}) {
  const id = useId()
  return (
    <fieldset className="field-picker" disabled={disabled}>
      <legend>{values ? 'Choose what to share' : 'Choose fields to request'}</legend>
      <div className="field-picker-grid">
        {fields.map((field) => (
          <label
            className={`field-choice ${selected.includes(field) ? 'chosen' : ''}`}
            key={field}
            htmlFor={`${id}-${field}`}
          >
            <input
              id={`${id}-${field}`}
              aria-label={fieldLabels[field]}
              aria-describedby={`${id}-${field}-help`}
              type="checkbox"
              checked={selected.includes(field)}
              onChange={(e) =>
                change(
                  e.target.checked ? [...selected, field] : selected.filter((f) => f !== field),
                )
              }
            />
            <span>
              <strong>{fieldLabels[field]}</strong>
              <small id={`${id}-${field}-help`}>
                {values?.[field] ? displayFieldValue(field, values[field]) : fieldHelp[field]}
              </small>
            </span>
          </label>
        ))}
      </div>
      <p className="field-selection-note">
        {selected.length
          ? `${selected.length} ${selected.length === 1 ? 'field' : 'fields'} selected`
          : 'Select at least one field to continue.'}
      </p>
    </fieldset>
  )
}
export function CopyButton({ value, label = 'Copy code' }: { value: string; label?: string }) {
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle')
  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      setState('copied')
    } catch {
      setState('failed')
    }
  }
  return (
    <>
      <button className="secondary" type="button" onClick={() => void copy()}>
        {state === 'copied' ? <Check size={16} /> : <Clipboard size={16} />}{' '}
        {state === 'copied' ? 'Copied' : label}
      </button>
      <span role="status" className="copy-feedback">
        {state === 'failed'
          ? 'Select the code and press Ctrl+C to copy it.'
          : state === 'copied'
            ? 'Copied. Share it directly with your verifier.'
            : ''}
      </span>
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
    <div className="portal-pagination">
      <button className="secondary" disabled={page === 1} onClick={() => change(page - 1)}>
        Previous
      </button>
      <span>
        Page {page} of {Math.ceil(total / 50)}
      </span>
      <button className="secondary" disabled={page * 50 >= total} onClick={() => change(page + 1)}>
        Next
      </button>
    </div>
  ) : null
}
