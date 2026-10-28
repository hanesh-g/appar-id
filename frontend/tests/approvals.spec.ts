import { expect, test } from '@playwright/test'
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

test('officer reviews synthetic evidence before either college can upload admissions', async ({
  page,
}) => {
  const pageErrors: string[] = []
  page.on('pageerror', (error) => pageErrors.push(error.name))
  async function signIn(email: string) {
    await page.goto('/')
    await page.getByLabel('Email address').fill(email)
    await page.getByLabel('Password', { exact: true }).fill(password())
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible()
  }
  await signIn('collegea@example.test')
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await expect(page.locator('.approval-notice')).toContainText('Officer review needed')
  await page.getByLabel('Student CSV').setInputFiles(resolve('..', 'fixtures', 'intake-65.csv'))
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  await expect(page.getByRole('alert')).toContainText('Admission submissions are blocked')
  await page.getByRole('link', { name: 'View approval' }).click()
  await expect(page.getByText('Simulated AICTE approval review', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Review demo evidence' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn('officer@example.test')
  await page
    .getByRole('navigation')
    .getByRole('link', { name: 'Institution approval', exact: true })
    .click()
  for (const college of ['Deccan Institute of Technology', 'Riverdale Technical College']) {
    const card = page
      .locator('.approval-card')
      .filter({ has: page.getByRole('heading', { name: college, exact: true }) })
    await expect(card).toContainText('Officer review needed')
    await card.getByRole('button', { name: 'Review demo evidence' }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toContainText('Synthetic fixture')
    await expect(
      dialog.getByRole('button', { name: 'Approve demo access', exact: true }),
    ).toBeDisabled()
    await dialog
      .getByRole('checkbox', { name: 'I reviewed the synthetic evidence and matching programmes.' })
      .check()
    await dialog.getByRole('button', { name: 'Approve demo access', exact: true }).click()
    await expect(card).toContainText('Demo approval active')
    await expect(card.getByText('Enabled in demo', { exact: true })).toHaveCount(2)
  }
  const first = page.locator('.approval-card').first()
  await first.locator('summary').click()
  await expect(first).toContainText('Version 1 · Demo access approved')
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await expect(
    page.getByRole('heading', { name: 'Institution approval', exact: true }),
  ).toBeVisible()
  await page.setViewportSize({ width: 1536, height: 730 })
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn('collegea@example.test')
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await expect(page.locator('.approval-notice')).toContainText('2 of 2 programmes enabled')
  expect(pageErrors).toEqual([])
})
