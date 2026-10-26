import { useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { fieldLabels, purposeLabels, type IssuedGrant } from './consent'

export default function ConsentShareCard({
  value,
  clear,
}: {
  value: IssuedGrant
  clear: () => void
}) {
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')
  if (!value.token) return null
  const { grant } = value
  const link = `${window.location.origin}/verify#token=${encodeURIComponent(value.token)}`
  const expiry = new Date(grant.expires_at).toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })
  async function copy() {
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
      setError('')
    } catch {
      setError('Select the shared link below and copy it.')
    }
  }
  return (
    <section className="panel consent-card consent-share" aria-label="New consent link">
      <div className="consent-share-instructions">
        <div className="eyebrow">YOU CONTROL WHAT YOU SHARE</div>
        <h2>Your consent link</h2>
        <p>
          Share this card's QR or link with <strong>{grant.verifier_organisation}</strong>. They
          must sign in to see the fields you approved.
        </p>
        <p className="consent-share-reveal">
          The link is shown once. Copy it before leaving this page. You can revoke access from your
          consent grants.
        </p>
        <label>
          Shared link
          <input
            aria-label="Shared link"
            type="password"
            readOnly
            value={link}
            autoComplete="off"
          />
        </label>
        <div className="actions">
          <button className="primary" onClick={() => void copy()}>
            {copied ? 'Link copied' : 'Copy consent link'}
          </button>
          <button className="secondary" onClick={clear}>
            Hide link
          </button>
        </div>
        {error && <p role="status">{error}</p>}
      </div>
      <article className="consent-ticket" aria-label="Consent sharing card">
        <header className="consent-ticket-brand">
          <span>APAAR WORKSPACE</span>
          <span className="consent-ticket-demo">SYNTHETIC DEMO</span>
        </header>
        <div className="consent-ticket-recipient">
          <span className="consent-ticket-label">FOR THIS VERIFIER</span>
          <h3>{grant.verifier_organisation}</h3>
          <p>{purposeLabels[grant.purpose]}</p>
        </div>
        <div className="consent-ticket-fields">
          <span className="consent-ticket-label">APPROVED FIELDS ONLY</span>
          <ul>
            {grant.allowed_fields.map((field) => (
              <li key={field}>{fieldLabels[field]}</li>
            ))}
          </ul>
        </div>
        <div className="consent-ticket-expiry">
          <span className="consent-ticket-label">EXPIRES</span>
          <time dateTime={grant.expires_at}>{expiry}</time>
        </div>
        <div className="consent-ticket-qr">
          <QRCodeSVG
            value={link}
            size={196}
            level="M"
            marginSize={4}
            title="Consent verification link"
          />
          <p>Verifier sign-in required</p>
        </div>
        <footer className="consent-ticket-footer">
          Permission to verify selected fields.
          <br />
          Not an official APAAR ID or certificate.
        </footer>
      </article>
    </section>
  )
}
