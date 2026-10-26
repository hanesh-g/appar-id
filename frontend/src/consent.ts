export const fieldLabels = {
  programme: 'Programme',
  institution_name: 'Institution',
  academic_year: 'Academic year',
  admission_status: 'Admission status',
  start_date: 'Start date',
  masked_apaar: 'Masked APAAR',
}
export type FieldName = keyof typeof fieldLabels
export const purposeLabels = {
  ADMISSION_CONFIRMATION: 'Admission confirmation',
  EMPLOYMENT_CHECK: 'Employment check',
  SCHOLARSHIP_CHECK: 'Scholarship check',
}
export type Purpose = keyof typeof purposeLabels
export interface OwnRecord {
  id: string
  version: number
  fields: Record<FieldName, string>
}
export interface SubmittedRequest {
  id: string
  version: number
  status: string
  purpose: Purpose
  requested_fields: FieldName[]
  created_at: string
  expires_at: string
}
export interface StudentRequest extends SubmittedRequest {
  verifier_organisation: string
  record: OwnRecord | null
}
export interface Grant {
  id: string
  request_id: string
  version: number
  purpose: Purpose
  allowed_fields: FieldName[]
  record_version: number
  expires_at: string
  revoked_at: string | null
  verifier_organisation: string
  can_reissue: boolean
}
export interface IssuedGrant {
  grant: Grant
  token?: string
  newly_issued: boolean
}
export function extractGrantToken(value: string) {
  if (value.length > 2000) throw new Error('Check the shared link')
  const trimmed = value.trim()
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    const parsed = new URL(trimmed)
    const token = new URLSearchParams(parsed.hash.slice(1)).get('token')
    if (!token || token.length > 400) throw new Error('Check the shared link')
    return token
  }
  if (!trimmed || trimmed.length > 400) throw new Error('Check the shared link')
  return trimmed
}

// Run once before BrowserRouter starts; StrictMode may invoke state initialisers twice.
export function takeInitialGrantToken() {
  const params = new URLSearchParams(window.location.hash.slice(1))
  const value = params.get('token')
  if (value !== null) {
    window.history.replaceState(
      window.history.state,
      '',
      window.location.pathname + window.location.search,
    )
  }
  return value && value.length <= 400 ? value : ''
}
