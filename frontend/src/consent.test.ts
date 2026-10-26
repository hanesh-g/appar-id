import { describe, expect, it } from 'vitest'
import { extractGrantToken, takeInitialGrantToken } from './consent'

describe('private consent link parsing', () => {
  it('takes only the URL fragment and clears it before routing', () => {
    window.history.replaceState({}, '', '/verify#token=synthetic-unit-value')
    expect(takeInitialGrantToken()).toBe('synthetic-unit-value')
    expect(window.location.hash).toBe('')
    expect(window.location.pathname).toBe('/verify')
    expect(takeInitialGrantToken()).toBe('')
  })
  it('does not accept query-string tokens or fetch a shared URL', () => {
    expect(extractGrantToken('https://example.test/verify#token=synthetic-unit-value')).toBe(
      'synthetic-unit-value',
    )
    expect(() =>
      extractGrantToken('https://example.test/verify?token=synthetic-unit-value'),
    ).toThrow('Check the shared link')
    expect(() => extractGrantToken('x'.repeat(2001))).toThrow('Check the shared link')
  })
})
