import { test, expect } from '@playwright/test';

test.describe('Agent Router Demo App - Main UI', () => {
  test.beforeEach(async ({ page }) => {
    // Mock all API endpoints since we don't have backend running in tests
    await page.route('/api/config', async route => {
      await route.fulfill({
        json: {
          features: {
            fabric_agent_enabled: true
          }
        }
      });
    });

    await page.route('/api/analyze', async route => {
      await route.fulfill({
        json: {
          success: true,
          catalog_results: {
            assets_found: 3,
            results: [
              { connected_agent: 'web', name: 'web-search' },
              { connected_agent: 'rag', name: 'document-search' },
              { connected_agent: 'fabric', name: 'data-analytics' }
            ]
          },
          purview: 'Found 3 relevant data assets with multiple agent options available'
        }
      });
    });

    await page.route('/api/process', async route => {
      const request = await route.request();
      const body = await request.postDataJSON();
      
      await route.fulfill({
        json: {
          success: true,
          response: `Processed query: "${body.query}" - This is a mocked response for testing.`,
          metadata: {
            thread_id: 'test-thread-123',
            connected_agents_called: ['web-agent'],
            tools_called: []
          }
        }
      });
    });

    await page.route('/api/process-direct', async route => {
      const request = await route.request();
      const body = await request.postDataJSON();
      
      await route.fulfill({
        json: {
          success: true,
          response: `Direct ${body.agent} agent response: "${body.query}" - This is a mocked direct response.`,
          metadata: {
            thread_id: 'test-thread-456',
            tools_called: []
          }
        }
      });
    });

    await page.goto('/');
  });

  test('should display the main UI elements', async ({ page }) => {
    // Check title
    await expect(page).toHaveTitle(/spark-template/);
    
    // Check main heading
    await expect(page.getByText('Agent Router Demo App')).toBeVisible();
    await expect(page.getByText('Purview-powered intent routing')).toBeVisible();

    // Check welcome section
    await expect(page.getByText('Purview Router')).toBeVisible();
    await expect(page.getByText('Route your queries through Microsoft Purview')).toBeVisible();

    // Check sample query buttons
    await expect(page.getByText('What is the cost of Microsoft Encarta?')).toBeVisible();
    await expect(page.getByText('What is the weather like tomorrow in Madrid?')).toBeVisible();

    // Check input and send button
    await expect(page.getByPlaceholder(/Ask about customer data/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Send' })).toBeVisible();
  });

  test('should show agent selection dropdown', async ({ page }) => {
    // Click on agent selection dropdown
    await page.getByRole('button', { name: /Auto Route \(using Purview\)/ }).click();

    // Check dropdown options
    await expect(page.getByText('Agent Selection')).toBeVisible();
    await expect(page.getByText('Auto Route (using Purview)')).toBeVisible();
    await expect(page.getByText('Fabric Data Agent')).toBeVisible();
    await expect(page.getByText('Databricks Genie')).toBeVisible();
    await expect(page.getByText('RAG Agent')).toBeVisible();
    await expect(page.getByText('Web Search')).toBeVisible();
  });

  test('should handle sample query click', async ({ page }) => {
    // Click on a sample query
    await page.getByText('What is the weather like tomorrow in Madrid?').click();

    // Check that the input is filled
    await expect(page.getByPlaceholder(/Ask about customer data/)).toHaveValue('What is the weather like tomorrow in Madrid?');
  });

  test('should process a query with auto routing', async ({ page }) => {
    // Type a query
    const query = 'What is the weather today?';
    await page.getByPlaceholder(/Ask about customer data/).fill(query);

    // Click send
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for processing to start
    await expect(page.getByText('Processing...')).toBeVisible();

    // Check that user message appears
    await expect(page.getByText(query)).toBeVisible();
    await expect(page.getByText('You')).toBeVisible();

    // Wait for analysis message
    await expect(page.getByText('Purview Analysis')).toBeVisible();
    await expect(page.getByText(/Found 3 relevant data assets/)).toBeVisible({ timeout: 10000 });

    // Wait for agent response
    await expect(page.getByText(/Processed query/)).toBeVisible({ timeout: 15000 });
    
    // Check that conversation shows active state
    await expect(page.getByText('Active conversation')).toBeVisible();
  });

  test('should process a direct query with specific agent', async ({ page }) => {
    // Select direct agent mode
    await page.getByRole('button', { name: /Auto Route \(using Purview\)/ }).click();
    await page.getByText('Web Search').click();

    // Check manual mode indicator
    await expect(page.getByText('Manual mode')).toBeVisible();

    // Type a query
    const query = 'Current weather in Tokyo';
    await page.getByPlaceholder(/Ask about current events/).fill(query);

    // Click send
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for processing
    await expect(page.getByText('Processing...')).toBeVisible();

    // Wait for direct response
    await expect(page.getByText(/Direct web agent response/)).toBeVisible({ timeout: 10000 });
  });

  test('should open and close history sidebar', async ({ page }) => {
    // Click history button
    await page.getByRole('button', { name: 'History' }).click();

    // Check sidebar is visible
    await expect(page.getByText('Recent History')).toBeVisible();

    // Check empty state
    await expect(page.getByText('No conversations yet')).toBeVisible();
    await expect(page.getByText('Start by asking a question below')).toBeVisible();

    // Close sidebar by clicking outside
    await page.locator('.history-overlay-backdrop').click();

    // Check sidebar is closed
    await expect(page.getByText('Recent History')).not.toBeVisible();
  });

  test('should start new conversation', async ({ page }) => {
    // First send a query to create a conversation
    await page.getByPlaceholder(/Ask about customer data/).fill('Test query');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for conversation to be established
    await expect(page.getByText('Active conversation')).toBeVisible();

    // Click New Chat button
    await page.getByRole('button', { name: 'New Chat' }).click();

    // Check that we're back to initial state
    await expect(page.getByText('Purview Router')).toBeVisible();
    await expect(page.getByText('Active conversation')).not.toBeVisible();
  });

  test('should handle form validation', async ({ page }) => {
    // Try to send empty query
    const sendButton = page.getByRole('button', { name: 'Send' });
    await expect(sendButton).toBeDisabled();

    // Type something
    await page.getByPlaceholder(/Ask about customer data/).fill('test');
    await expect(sendButton).toBeEnabled();

    // Clear input
    await page.getByPlaceholder(/Ask about customer data/).clear();
    await expect(sendButton).toBeDisabled();
  });

  test('should display proper agent colors and badges', async ({ page }) => {
    // Send a query to see agent messages
    await page.getByPlaceholder(/Ask about customer data/).fill('Test query for colors');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for messages to appear and check badges
    await expect(page.getByText('You')).toBeVisible();
    await expect(page.getByText('Purview Analysis')).toBeVisible({ timeout: 10000 });
    
    // Note: We can't easily test CSS colors in Playwright, but we can check that the right badges appear
    // which indicates the styling logic is working
  });

  test('should handle keyboard shortcuts', async ({ page }) => {
    const input = page.getByPlaceholder(/Ask about customer data/);
    
    // Type in input
    await input.fill('Test keyboard shortcuts');
    
    // Press Enter to submit
    await input.press('Enter');
    
    // Should start processing
    await expect(page.getByText('Processing...')).toBeVisible();
  });
});