import { test, expect } from '@playwright/test';

test('sidebar bootstraps against mocked runtime', async ({ page }) => {
  await page.route('**/api/copilotkit/**', async (route) => {
    if (route.request().method() === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'event: ready\ndata: {}\n\n',
      });
    }
    return route.fulfill({ status: 200, body: '{}' });
  });

  await page.goto('http://localhost:3000/');
  await expect(page.getByTestId('copilot-sidebar')).toBeVisible();
});
