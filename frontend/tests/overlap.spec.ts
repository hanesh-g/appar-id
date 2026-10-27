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

test('officer reviews an overlap while institutions receive only a generic notice', async ({
  page,
}) => {
  async function signIn(email: string) {
    await page.goto('/')
    await page.getByLabel('Email address').fill(email)
    await page.getByLabel('Password', { exact: true }).fill(password())
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(
      page.getByRole('heading', {
        name:
          email === 'officer@example.test'
            ? 'Admission oversight'
            : 'A clearer view of your intake',
      }),
    ).toBeVisible()
  }
  await signIn('collegeb@example.test')
  await page.getByRole('navigation').getByRole('link', { name: 'Upload admissions' }).click()
  await page
    .getByLabel('Student CSV')
    .setInputFiles(resolve('..', 'fixtures', 'identity-cases.csv'))
  await page.getByRole('button', { name: 'Validate and preview' }).click()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Commit batch', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('held')
  await page.getByRole('navigation').getByRole('link', { name: 'Enrolments', exact: true }).click()
  await page.getByLabel('Student reference').fill('STU-001')
  await page.getByRole('button', { name: 'Demo Student 001', exact: true }).click()
  await expect(page.getByRole('dialog')).toContainText('needs officer review')
  await expect(page.getByRole('dialog')).not.toContainText('Deccan Institute of Technology')
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click()
  await page.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn('officer@example.test')
  await page
    .getByRole('navigation')
    .getByRole('link', { name: 'Overlap reviews', exact: true })
    .click()
  await expect(page.getByRole('heading', { name: 'Review overlapping enrolments' })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Deccan Institute of Technology', exact: true }).first(),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Riverdale Technical College', exact: true }).first(),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Review this overlap' }).first().click()
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.getByLabel('Review outcome', { exact: true }).selectOption('REVIEWED_PERMITTED_DUAL')
  await page.getByRole('button', { name: 'Save review', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('Review saved: Dual study reviewed')
  await page.getByLabel('Review status', { exact: true }).selectOption('')
  await expect(page.locator('.overlap-review').first()).toContainText('Reviewed: dual study')
})
