import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function demoPassword() {
  if (process.env.DEMO_PASSWORD) return process.env.DEMO_PASSWORD
  const text = readFileSync(resolve('..', '.env'), 'utf8')
  const value = text
    .split(/\r?\n/)
    .find((line) => line.startsWith('DEMO_PASSWORD='))
    ?.slice('DEMO_PASSWORD='.length)
  if (!value) throw new Error('Configure DEMO_PASSWORD for the synthetic smoke account')
  return value.replace(/^"|"$/g, '')
}

test('institution uploads, reviews, commits, corrects, and reads history', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Email address').fill('collegea@example.test')
  await page.getByLabel('Password', { exact: true }).fill(demoPassword())
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'A clearer view of your intake' })).toBeVisible()
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await page.getByLabel('Student CSV').setInputFiles(resolve('..', 'fixtures', 'intake-65.csv'))
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  await expect(page.getByRole('heading', { name: 'intake-65.csv' })).toBeVisible()
  await expect(
    page
      .getByRole('cell', {
        name: 'No APAAR ID supplied. Add it later; this admission remains counted.',
        exact: false,
      })
      .first(),
  ).toBeVisible()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Commit batch', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('held')
  await page.getByRole('link', { name: 'Back to overview' }).click()
  await expect(
    page.locator('.stat').filter({ hasText: 'Active admissions' }).locator('strong'),
  ).toHaveText('65')
  await expect(
    page.locator('.stat').filter({ hasText: 'Identity gaps' }).locator('strong'),
  ).toHaveText('5')
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await page.getByLabel('Student CSV').setInputFiles(resolve('..', 'fixtures', 'corrections.csv'))
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  await expect(page.getByRole('heading', { name: 'corrections.csv' })).toBeVisible()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Commit batch', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('0 created')
  await page.getByRole('navigation').getByRole('link', { name: 'Enrolments' }).click()
  await page.getByLabel('Student reference').fill('STU-001')
  await page.getByRole('button', { name: 'Demo Student 001', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Record history' })).toBeVisible()
  await page.getByRole('button', { name: 'Close dialog' }).click()
  await page.getByRole('navigation').getByRole('link', { name: 'Activity history' }).click()
  await expect(
    page.getByRole('cell', { name: 'batch committed', exact: false }).first(),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
})
