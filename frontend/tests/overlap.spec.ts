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
    await expect(page.getByRole('heading', { name: 'A clearer view of your intake' })).toBeVisible()
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
    .getByRole('link', { name: 'Interval reviews', exact: true })
    .click()
  await expect(page.getByRole('heading', { name: 'Enrolment interval reviews' })).toBeVisible()
  await expect(
    page.getByRole('cell', { name: 'Deccan Institute of Technology', exact: true }).first(),
  ).toBeVisible()
  await expect(
    page.getByRole('cell', { name: 'Riverdale Technical College', exact: true }).first(),
  ).toBeVisible()
  await page.getByRole('button', { name: 'Reviewed: permitted dual', exact: true }).first().click()
  await expect(page.locator('.overlap-review .section-title p').first()).toContainText(
    'reviewed permitted dual',
  )
})
