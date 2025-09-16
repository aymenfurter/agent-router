import { expect, test } from '@playwright/test'

test.describe('Agent Router Demo App', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/config', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ features: { fabric_agent_enabled: true } }),
      }),
    )
  })

  test('selecting a sample prompt prefills the query and allows switching mode', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('heading', { name: 'Agent Router Demo App' })).toBeVisible()

    const samplePrompt = page.getByRole('button', { name: 'What is the cost of Microsoft Encarta?' })
    await samplePrompt.click()

    await expect(page.getByRole('textbox')).toHaveValue('What is the cost of Microsoft Encarta?')

    const modeTrigger = page.getByRole('button', { name: /Auto Route/i })
    await modeTrigger.click()

    const fabricOption = page.getByRole('menuitem', { name: 'Fabric Data Agent' })
    await expect(fabricOption).toBeVisible()
    await fabricOption.click()

    await expect(page.getByRole('button', { name: /Fabric Agent/i })).toBeVisible()
    await expect(page.getByText('Manual mode')).toBeVisible()
  })
})
