import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from './api'
import Dialog from './Dialog'

interface Rule {
  rule_set_id: string
  issue_code: string
  explanation: string
  steps: string[]
  owner_types: string[]
  authority_label: string
  source_url: string
  applicability: string
  effective_date: string | null
  reviewed_date: string | null
}

export default function RuleHelp({ code, ruleSetId }: { code: string; ruleSetId: string }) {
  const [open, setOpen] = useState(false)
  const query = useQuery({
    queryKey: ['rule', ruleSetId, code],
    queryFn: () =>
      api<Rule>(`/rules/${encodeURIComponent(code)}?rule_set_id=${encodeURIComponent(ruleSetId)}`),
    enabled: open,
    retry: false,
  })
  const rule = query.data
  return (
    <>
      <button className="rule-link" onClick={() => setOpen(true)} aria-label={`Explain ${code}`}>
        {code.replaceAll('_', ' ').toLowerCase()}
      </button>
      {open && (
        <Dialog title="Why this issue needs attention" close={() => setOpen(false)}>
          {query.isPending && <p role="status">Loading this rule version…</p>}
          {query.error && (
            <p role="alert">
              {query.error instanceof Error ? query.error.message : 'Rule explanation unavailable.'}
            </p>
          )}
          {rule && (
            <>
              <p>
                <strong>{rule.issue_code}</strong> · {rule.explanation}
              </p>
              <h3>Next steps</h3>
              <ol>
                {rule.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <p>
                <strong>Who can act:</strong>{' '}
                {rule.owner_types.map((v) => v.replaceAll('_', ' ').toLowerCase()).join(', ')}.
                Confirm which source record needs correction.
              </p>
              <p>{rule.applicability}</p>
              <dl className="record-grid">
                <div>
                  <dt>Authority</dt>
                  <dd>{rule.authority_label}</dd>
                </div>
                <div>
                  <dt>Version</dt>
                  <dd>{rule.rule_set_id}</dd>
                </div>
                <div>
                  <dt>Effective date</dt>
                  <dd>{rule.effective_date || 'Not established for official use'}</dd>
                </div>
                <div>
                  <dt>Human review date</dt>
                  <dd>{rule.reviewed_date || 'Not reviewed as official policy'}</dd>
                </div>
              </dl>
              {rule.source_url.startsWith('https://') && (
                <a href={rule.source_url} target="_blank" rel="noopener noreferrer">
                  Read the demo rule source
                </a>
              )}
            </>
          )}
        </Dialog>
      )}
    </>
  )
}
