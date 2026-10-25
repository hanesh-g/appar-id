import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import App from './App'
import { setToken } from './api'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  setToken('')
})

it('shows a failed login without granting access to the workspace', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockImplementation((url: string) =>
        Promise.resolve(
          new Response(
            JSON.stringify(
              url.endsWith('/health')
                ? { database: 'ok' }
                : { message: 'Email or password is incorrect' },
            ),
            { status: url.endsWith('/health') ? 200 : 401 },
          ),
        ),
      ),
  )
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
  await waitFor(() =>
    expect(screen.getByRole('alert').textContent).toContain('Email or password is incorrect'),
  )
  expect(screen.queryByRole('navigation', { name: 'Main navigation' })).toBeNull()
  client.clear()
})
