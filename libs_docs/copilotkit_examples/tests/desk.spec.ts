import { test, expect } from '@playwright/test';

async function mockCopilotStream(route: any, events: string[]) {
  const body = events.map((event) => `event: state\ndata: ${event}\n\n`).join('');
  await route.fulfill({
    status: 200,
    contentType: 'text/event-stream',
    body,
  });
}

test('desk queue renders after a StateDeltaEvent', async ({ page }) => {
  await page.route('**/api/copilotkit/**', async (route) => {
    if (route.request().method() === 'POST') {
      const delta = JSON.stringify({
        type: 'STATE_DELTA',
        delta: [
          {
            op: 'add',
            path: '/desk',
            value: {
              queue: [{ id: 'ticket-123', title: 'Renew contract', status: 'pending', evidence: [] }],
            },
          },
        ],
      });
      return mockCopilotStream(route, [delta]);
    }
    return route.fulfill({ status: 200, body: '{}' });
  });

  await page.goto('http://localhost:3000/desk');
  await expect(page.getByText('Renew contract')).toBeVisible();
});
