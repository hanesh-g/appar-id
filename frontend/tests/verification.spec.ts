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
  const clientErrors: string[] = []
  student.on('pageerror', (error) => clientErrors.push(error.name))
  verifier.on('pageerror', (error) => clientErrors.push(error.name))
  verifier.on('request', (request) => requestedUrls.push(request.url()))
  await student.goto('/')
  await signIn(student, 'student1@example.test')
  await expect(student.getByRole('heading', { name: 'Your student records' })).toBeVisible()
  await expect(student.getByRole('link', { name: 'Enrolments', exact: true })).toHaveCount(0)
  await student
    .getByRole('navigation')
    .getByRole('link', { name: 'My records', exact: true })
    .click()
  const record = student.getByRole('article').filter({ hasText: 'Deccan Institute of Technology' })
  await record.getByRole('button', { name: 'View student card', exact: true }).click()
  const studentCard = student
    .getByRole('dialog')
    .getByRole('article', { name: 'Student record card' })
  await expect(studentCard).toContainText('Computer Science')
  await expect(studentCard).toContainText('Not an official APAAR ID or certificate.')
  await expect(studentCard).not.toContainText('900000000001')
  await student.setViewportSize({ width: 390, height: 844 })
  expect(
    await student.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true)
  await expect(student.getByRole('dialog')).toBeVisible()
  await student.setViewportSize({ width: 1280, height: 900 })
  await student.getByRole('button', { name: 'Close dialog', exact: true }).click()
  await student
    .getByRole('article')
    .filter({ hasText: 'Deccan Institute of Technology' })
    .getByRole('button', { name: 'Start sharing', exact: true })
    .click()
  const code = await student.getByLabel('Request code', { exact: true }).inputValue()
  await student.getByRole('button', { name: 'Close dialog', exact: true }).click()
  await verifier.goto('/')
  await signIn(verifier, 'verifier1@example.test')
  await expect(verifier.getByRole('heading', { name: 'Verify a student record' })).toBeVisible()
  await verifier
    .getByRole('navigation')
    .getByRole('link', { name: 'Request access', exact: true })
    .click()
  const picker = verifier.getByRole('group', { name: 'Choose fields to request' })
  expect(await picker.evaluate((element) => element.getBoundingClientRect().height < 330)).toBe(
    true,
  )
  expect(
    await picker
      .locator('label')
      .first()
      .evaluate((element) => getComputedStyle(element).flexDirection),
  ).toBe('row')
  await verifier.setViewportSize({ width: 390, height: 844 })
  expect(
    await verifier.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true)
  await expect(verifier.getByRole('button', { name: 'Sign out', exact: true })).toBeVisible()
  await verifier.setViewportSize({ width: 1280, height: 900 })
  await secretInput(verifier, 'Student request code', code)
  await verifier.getByRole('checkbox', { name: 'Programme', exact: true }).check()
  await verifier.getByRole('checkbox', { name: 'Institution', exact: true }).check()
  await verifier.getByRole('button', { name: 'Send approval request', exact: true }).click()
  await expect(verifier.getByRole('status')).toContainText('Request submitted')
  await verifier.getByRole('link', { name: 'Track your requests', exact: true }).click()
  await expect(
    verifier.getByRole('heading', { name: 'Your request history', exact: true }),
  ).toBeVisible()
  await expect(verifier.getByText('Computer Science', { exact: true })).toHaveCount(0)
  await student
    .getByRole('navigation')
    .getByRole('link', { name: /^Requests/ })
    .click()
  await student.getByRole('button', { name: 'Refresh', exact: true }).click()
  const pending = student
    .getByRole('article')
    .filter({ has: student.getByRole('button', { name: 'Approve selected fields' }) })
    .first()
  await expect(
    pending.getByRole('heading', { name: 'Demo admissions verifier', exact: true }),
  ).toBeVisible()
  await expect(pending.getByRole('button', { name: 'Approve selected fields' })).toBeDisabled()
  await pending.getByRole('checkbox', { name: 'Programme', exact: true }).check()
  await pending.getByRole('button', { name: 'Approve selected fields' }).click()
  const issued = student.getByRole('region', { name: 'New consent link' })
  await expect(issued.getByRole('heading', { name: 'Your consent link' })).toBeVisible()
  await expect(issued.locator('svg')).toHaveCount(1)
  const card = issued.getByRole('article', { name: 'Consent sharing card' })
  await expect(card).toContainText('Demo admissions verifier')
  await expect(card).toContainText('Admission confirmation')
  await expect(card.getByRole('listitem')).toHaveText(['Programme'])
  await expect(card).toContainText('Not an official APAAR ID or certificate.')
  await expect(card.locator('time')).toHaveAttribute('datetime', /.+/)
  await student.setViewportSize({ width: 390, height: 844 })
  expect(
    await student.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBe(true)
  const bounds = await card.boundingBox()
  expect(
    Boolean(bounds && bounds.width > 0 && bounds.x >= 0 && bounds.x + bounds.width <= 390),
  ).toBe(true)
  await student.setViewportSize({ width: 1280, height: 900 })
  const shared = await issued.getByLabel('Shared link', { exact: true }).inputValue()
  const opaque = new URL(shared).hash.slice('#token='.length)
  await verifier.evaluate((url) => window.location.assign(url), shared)
  await expect(verifier.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible()
  expect(new URL(verifier.url()).hash).toBe('')
  await signIn(verifier, 'verifier1@example.test')
  await verifier.getByRole('button', { name: 'Verify approved fields' }).click()
  const result = verifier
    .getByRole('status')
    .filter({ has: verifier.getByRole('heading', { name: 'Approved fields', exact: true }) })
  await expect(result).toContainText('Computer Science')
  await expect(result.locator('dt')).toHaveText(['Programme'])
  expect(requestedUrls.every((url) => !url.includes(opaque))).toBe(true)
  await student.getByRole('button', { name: 'Stop sharing', exact: true }).click()
  await expect(student.getByRole('dialog')).toContainText('stop future checks')
  await student.getByRole('button', { name: 'Confirm stop sharing', exact: true }).click()
  await expect(student.getByRole('button', { name: 'Stop sharing', exact: true })).toHaveCount(0)
  await expect(issued).toHaveCount(0)
  await secretInput(verifier, 'Student consent link', shared)
  await verifier.getByRole('button', { name: 'Verify approved fields' }).click()
  await expect(verifier.getByRole('alert')).toContainText('This link cannot be opened')
  await expect(verifier.getByRole('heading', { name: 'Approved fields', exact: true })).toHaveCount(
    0,
  )
  await student
    .getByRole('navigation')
    .getByRole('link', { name: 'Access history', exact: true })
    .click()
  await expect(student.getByRole('heading', { name: 'Access history' })).toBeVisible()
  await expect(
    student
      .locator('.activity-list')
      .getByRole('heading', { name: 'Demo admissions verifier', exact: true })
      .first(),
  ).toBeVisible()
  await expect(student.getByText('No record checks yet')).toHaveCount(0)
  expect(clientErrors).toEqual([])
  await studentContext.close()
  await verifierContext.close()
})
