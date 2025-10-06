import { test, expect } from '@playwright/test';

const GUARDRAIL_DELTA = JSON.stringify({
  type: 'STATE_DELTA',
  delta: [
    {
      op: 'add',
      path: '/guardrails',
      value: {
        trust: {
          allowed: false,
          score: 0.12,
          threshold: 0.8,
          message: 'Trust score 0.12 below threshold 0.80',
        },
      },
    },
  ],
});

test('guardrail banner surfaces trust block', async ({ page }) => {
  await page.route('**/api/copilotkit/**', async (route) => {
    if (route.request().method() === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: `event: state\ndata: ${GUARDRAIL_DELTA}\n\n`,
      });
    }
    return route.fulfill({ status: 200, body: '{}' });
  });

  await page.goto('http://localhost:3000/desk');
  await expect(page.getByText(/Trust score 0\.12/i)).toBeVisible();
});
