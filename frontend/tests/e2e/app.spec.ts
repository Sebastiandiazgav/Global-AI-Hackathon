import { test, expect } from '@playwright/test'

test.describe('MyAgent Enterprise Copilot - E2E', () => {
  test('page loads with correct layout', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('MyAgent')
    await expect(page.locator('text=Enterprise AI Copilot')).toBeVisible()
  })

  test('shows all agent status badges', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Energy')).toBeVisible()
    await expect(page.locator('text=Logistics')).toBeVisible()
    await expect(page.locator('text=Support')).toBeVisible()
    await expect(page.locator('text=Analytics')).toBeVisible()
    await expect(page.locator('text=Society')).toBeVisible()
  })

  test('shows welcome message in chat', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=MyAgent, your AI Copilot')).toBeVisible()
  })

  test('has quick action buttons', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Energy')).toBeVisible()
    await expect(page.locator('text=Strategy')).toBeVisible()
  })

  test('has language selector', async ({ page }) => {
    await page.goto('/')
    // Globe icon with language label should be visible
    await expect(page.locator('text=🇪🇸 ES')).toBeVisible()
  })

  test('has image upload button', async ({ page }) => {
    await page.goto('/')
    const imageButton = page.locator('[title="Upload image for analysis"]')
    await expect(imageButton).toBeVisible()
  })

  test('workflow panel shows available agents', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Visual — Image analysis')).toBeVisible()
    await expect(page.locator('text=Society — Strategic debate')).toBeVisible()
  })

  test('footer shows infrastructure info', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Qwen Cloud')).toBeVisible()
    await expect(page.locator('text=hackaton-enterprise')).toBeVisible()
  })
})
