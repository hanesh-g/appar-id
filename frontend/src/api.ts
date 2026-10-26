let token = ''
export const setToken = (value: string) => {
  token = value
}
const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(
  /\/$/,
  '',
)

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code = '',
  ) {
    super(message)
  }
}

export async function rawRequest(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData))
    headers.set('Content-Type', 'application/json')
  let response: Response
  try {
    response = await fetch(`${base}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Cannot reach the API. Check that the backend is running.', 0)
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    if (response.status === 401 && path !== '/auth/login')
      window.dispatchEvent(new Event('session-expired'))
    const detail = data.details
      ?.map((v: { field: string; message: string }) => `${v.field}: ${v.message}`)
      .join('; ')
    throw new ApiError(
      detail || data.message || 'The request failed. Please try again.',
      response.status,
      data.code,
    )
  }
  return response
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  return (await rawRequest(path, options)).json()
}

export async function download(path: string, filename: string) {
  const blob = await (await rawRequest(path)).blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export interface User {
  id: string
  email: string
  name: string
  role: string
  institution_id: string | null
}
export interface Programme {
  id: string
  name: string
  academic_year: string
  approved_intake: number
  institution_id: string
}
export interface Intake {
  id: string
  programme: string
  institution_id: string
  academic_year: string
  approved: number
  active: number
  excess: number
}
export interface RecentBatch {
  id: string
  filename: string
  status: string
  rows_total: number
  created_at: string
}
export interface Dashboard {
  active: number
  categories: {
    base_count: number
    supernumerary_count: number
    unclassified_count: number
    nri_count: number
    oci_count: number
    foreign_national_count: number
  }
  identity_counts: Record<string, number>
  excess: number
  programmes: Intake[]
  held_candidates: number
  unassignable_rows: number
  batches: RecentBatch[]
  as_of: string
}
export interface Issue {
  code: string
  field: string
  severity: string
  message: string
}
export interface BatchRow {
  id: string
  row_no: number
  student_ref: string
  identity_status: string
  identity_reason: string
  status: string
  issues: Issue[]
}
export interface Batch {
  id: string
  filename: string
  academic_year: string
  rule_set_id: string
  status: string
  result: Record<string, number> | null
  summary: {
    rows_total: number
    rows_ok: number
    rows_warning: number
    rows_error: number
    identity_counts: Record<string, number>
    issue_counts: Record<string, number>
    intake: { programme: string; before: number; after: number; approved: number; excess: number }[]
  }
}
export interface Enrolment {
  id: string
  student_ref: string
  student_name?: string
  programme: string
  academic_year: string
  identity_status: string
  identity_reason: string
  apaar_masked: string
  status: string
  start_date: string
  end_date: string | null
  version: number
  overlap_review_pending: boolean
  history?: { version: number; created_at: string; snapshot: Record<string, unknown> }[]
}
export interface Audit {
  id: string
  actor: string
  action: string
  entity_id: string
  created_at: string
  details: Record<string, unknown>
}
export interface Page<T> {
  total: number
  items: T[]
}

export interface ResolutionCase {
  id: string
  subject_kind: 'STAGED_ROW' | 'ENROLMENT'
  batch_row_id: string | null
  enrolment_id: string | null
  origin_batch_id: string | null
  student_ref: string
  issue_code: string
  rule_set_id: string
  owner_type: string
  assignee_id: string | null
  status: string
  resolution_reason: string | null
  evidence_kind: string | null
  version: number
  episode: number
  created_at: string
  updated_at: string
  resolved_at: string | null
  events?: {
    old_status: string | null
    new_status: string
    owner_type: string
    reason: string
    version: number
    created_at: string
  }[]
}
