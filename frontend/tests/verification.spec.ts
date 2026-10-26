import { test, expect, type Page } from '@playwright/test'
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
async function signIn(page: Page, email: string) {
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password())
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
}
// Keep opaque values out of Playwright action diagnostics as well as application logs.
async function secretInput(page: Page, label: string, value: string) {
  await expect(page.getByLabel(label, { exact: true })).toBeVisible()
  await page.evaluate(
    ({ label, value }) => {
      const element = document.querySelector<HTMLInputElement>(`input[aria-label="${label}"]`)!
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(
        element,
        value,
      )
      element.dispatchEvent(new Event('input', { bubbles: true }))
    },
    { label, value },
  )
}

test('student limits QR disclosure and can revoke access immediately', async ({ browser }) => {
  test.setTimeout(60000)
  const studentContext = await browser.newContext()
  const verifierContext = await browser.newContext()
  const student = await studentContext.newPage()
  const verifier = await verifierContext.newPage()
  const requestedUrls: string[] = []
  verifier.on('request', (request) => requestedUrls.push(request.url()))
  await student.goto('/')
  await signIn(student, 'student1@example.test')
  await expect(student.getByRole('heading', { name: 'Your records and consent' })).toBeVisible()
  await expect(student.getByRole('link', { name: 'Enrolments', exact: true })).toHaveCount(0)
  await student
    .getByRole('article')
    .filter({ hasText: 'Deccan Institute of Technology' })
    .getByRole('button', { name: 'Create request code', exact: true })
    .click()
  const code = await student.getByLabel('Request code', { exact: true }).inputValue()
  await verifier.goto('/')
  await signIn(verifier, 'verifier1@example.test')
  await expect(verifier.getByRole('heading', { name: 'Request and verify' })).toBeVisible()
  await secretInput(verifier, 'Student request code', code)
  await verifier.getByRole('checkbox', { name: 'Programme', exact: true }).check()
  await verifier.getByRole('checkbox', { name: 'Institution', exact: true }).check()
  await verifier.getByRole('button', { name: 'Submit consent request', exact: true }).click()
  await expect(verifier.getByRole('status')).toContainText('Request submitted')
  await student.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn(student, 'student1@example.test')
  await expect(
    student.getByRole('heading', { name: 'Demo admissions verifier', exact: true }),
  ).toBeVisible()
  await expect(student.getByRole('button', { name: 'Approve selected fields' })).toBeDisabled()
  await student.getByRole('checkbox', { name: 'Programme', exact: true }).check()
  await student.getByRole('button', { name: 'Approve selected fields' }).click()
  const issued = student.getByRole('region', { name: 'New consent link' })
  await expect(issued.getByRole('heading', { name: 'Your consent link' })).toBeVisible()
  await expect(issued.locator('svg')).toHaveCount(1)
  const shared = await issued.getByLabel('Shared link', { exact: true }).inputValue()
  const opaque = new URL(shared).hash.slice('#token='.length)
  await verifier.evaluate((url) => window.location.assign(url), shared)
  await expect(verifier.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()
  expect(new URL(verifier.url()).hash).toBe('')
  await signIn(verifier, 'verifier1@example.test')
  await verifier.getByRole('button', { name: 'Verify approved fields' }).click()
  const result = verifier
    .getByRole('status')
    .filter({ has: verifier.getByRole('heading', { name: 'Approved fields' }) })
  await expect(result).toContainText('Computer Science')
  await expect(result.locator('dt')).toHaveText(['Programme'])
  expect(requestedUrls.every((url) => !url.includes(opaque))).toBe(true)
  await student.getByRole('button', { name: 'Revoke access', exact: true }).click()
  await expect(student.getByRole('button', { name: 'Revoke access', exact: true })).toHaveCount(0)
  await secretInput(verifier, 'Student consent link', shared)
  await verifier.getByRole('button', { name: 'Verify approved fields' }).click()
  await expect(verifier.getByRole('alert')).toContainText('Verification is unavailable')
  await expect(verifier.getByRole('heading', { name: 'Approved fields' })).toHaveCount(0)
  await student.getByRole('button', { name: 'Sign out', exact: true }).click()
  await signIn(student, 'student1@example.test')
  await expect(student.getByRole('heading', { name: 'Access history' })).toBeVisible()
  await expect(student.getByText('No verifier has accessed your records.')).toHaveCount(0)
  await studentContext.close()
  await verifierContext.close()
})
