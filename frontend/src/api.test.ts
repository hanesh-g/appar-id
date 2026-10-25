import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, rawRequest, setToken } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
  setToken('')
})

describe('API boundary', () => {
  it('sends credentials in headers, without serializing them into the body', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ total: 0 })))
    vi.stubGlobal('fetch', fetcher)
    setToken('test-only-token')
    await api('/enrolments')
    const options = fetcher.mock.calls[0][1]
    expect(options.headers.get('Authorization')).toBe('Bearer test-only-token')
    expect(options.body).toBeUndefined()
  })
  it('leaves multipart content type to the browser', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response('{}'))
    vi.stubGlobal('fetch', fetcher)
    await rawRequest('/batches', { method: 'POST', body: new FormData() })
    expect(fetcher.mock.calls[0][1].headers.has('Content-Type')).toBe(false)
  })
  it('expires the local session on API authentication failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ message: 'Sign in again' }), { status: 401 }),
        ),
    )
    const listener = vi.fn()
    window.addEventListener('session-expired', listener)
    try {
      await expect(api('/enrolments')).rejects.toThrow('Sign in again')
      expect(listener).toHaveBeenCalledOnce()
    } finally {
      window.removeEventListener('session-expired', listener)
    }
  })
  it('returns a useful failure on a disconnected backend', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network unavailable')))
    await expect(api('/dashboard')).rejects.toBeInstanceOf(ApiError)
    await expect(api('/dashboard')).rejects.toThrow('Cannot reach the API')
  })
  it('does not expose an HTML upstream error as application content', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<html>upstream diagnostic</html>', { status: 502 })),
    )
    await expect(api('/dashboard')).rejects.toThrow('The request failed')
  })
})
