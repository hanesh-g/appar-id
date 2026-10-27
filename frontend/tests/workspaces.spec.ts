import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

test('student can recover from a records error and understands an empty result', async ({
  page,
}) => {
  const password =
    process.env.DEMO_PASSWORD ||
    readFileSync(resolve('..', '.env'), 'utf8')
      .split(/\r?\n/)
      .find((line) => line.startsWith('DEMO_PASSWORD='))
      ?.slice('DEMO_PASSWORD='.length)
      .replace(/^"|"$/g, '')
  if (!password) throw new Error('Configure the synthetic smoke account password')
  let mode: 'error' | 'empty' | 'live' = 'error'
  await page.route('**/api/v1/me/enrolments*', async (route) => {
    if (mode === 'live') return route.continue()
    await route.fulfill({
      status: mode === 'error' ? 503 : 200,
      contentType: 'application/json',
      body: JSON.stringify(
        mode === 'error'
          ? { message: 'Student records are temporarily unavailable' }
          : { items: [], total: 0 },
      ),
    })
  })
  await page.goto('/')
  await page.getByLabel('Email address').fill('student2@example.test')
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Student records are temporarily unavailable')
  mode = 'live'
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(
    page.getByRole('button', { name: 'View student card', exact: true }).first(),
  ).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
  mode = 'empty'
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Your records will appear here', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByText('Your college needs to submit and verify your record first.', { exact: false }),
  ).toBeVisible()
  mode = 'live'
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(
    page.getByRole('button', { name: 'View student card', exact: true }).first(),
  ).toBeVisible()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back', exact: true })).toBeVisible()
})
