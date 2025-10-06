import { test, expect } from '@playwright/test';

const APPROVAL_DELTA = JSON.stringify({
  type: 'STATE_DELTA',
  delta: [
    {
      op: 'add',
      path: '/approvalModal',
      value: {
        envelopeId: 'env-123',
        proposal: {
          summary: 'Send renewal email',
          evidence: ['CRM ticket 42'],
        },
        requiredScopes: ['GMAIL.SMTP'],
        approvalState: 'pending',
        schema: {
          type: 'object',
          properties: {
            body: { type: 'string', title: 'Email body' },
          },
        },
        formData: { body: '' },
        actions: {
          approve: { label: 'Approve', action: 'approvals:approve' },
          reject: { label: 'Reject', action: 'approvals:reject', variant: 'destructive' },
          cancel: { label: 'Cancel', action: 'approvals:cancel', variant: 'ghost' },
        },
      },
    },
  ],
});

test('approvals modal submit & cancel flows', async ({ page }) => {
  await page.route('**/api/copilotkit/**', async (route) => {
    if (route.request().method() === 'POST') {
      return route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: `event: state\ndata: ${APPROVAL_DELTA}\n\n`,
      });
    }
    return route.fulfill({ status: 200, body: '{}' });
  });

  await page.goto('http://localhost:3000/approvals');
  await expect(page.getByRole('heading', { name: /Send renewal email/i })).toBeVisible();

  // Approve action
  await page.getByRole('button', { name: 'Approve' }).click();
  // Cancel action (modal should close after approve handler processes)
  await page.getByRole('button', { name: 'Cancel' }).click();
});
