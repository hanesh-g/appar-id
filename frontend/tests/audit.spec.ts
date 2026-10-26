import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function password() {
  const value =
    process.env.DEMO_PASSWORD ||
    readFileSync(resolve('..', '.env'), 'utf8')
      .split(/\r?\n/)
      .find((line) => line.startsWith('DEMO_PASSWORD='))
      ?.slice('DEMO_PASSWORD='.length)
      .replace(/^"|"$/g, '')
  if (!value) throw new Error('Configure the synthetic smoke account password')
  return value
}

test('officer verifies the audit chain after a real staged upload', async ({ page }) => {
  async function signIn(email: string) {
    await page.goto('/')
    await page.getByLabel('Email address').fill(email)
    await page.getByLabel('Password', { exact: true }).fill(password())
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'A clearer view of your intake' })).toBeVisible()
  }
  await signIn('collegea@example.test')
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await page
    .getByLabel('Student CSV')
    .setInputFiles(resolve('..', 'fixtures', 'identity-cases.csv'))
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  await expect(page.getByRole('heading', { name: 'identity-cases.csv', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn('officer@example.test')
  await page
    .getByRole('navigation')
    .getByRole('link', { name: 'Activity history', exact: true })
    .click()
  await page.getByRole('button', { name: 'Verify audit chain', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('Integrity check passed')
  await expect(page.getByRole('status')).toContainText('not original legacy authenticity')
})
