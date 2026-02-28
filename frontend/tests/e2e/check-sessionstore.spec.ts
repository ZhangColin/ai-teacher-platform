/**
 * Check sessionStore state during chat
 */
import { test, expect } from '@playwright/test';

test('check sessionStore messages', async ({ page }) => {
  // Capture console logs
  page.on('console', msg => {
    console.log(`[BROWSER] ${msg.type()}: ${msg.text()}`);
  });

  // Capture network requests
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/v1/tools/') && url.includes('/chat/stream')) {
      console.log(`[REQUEST] POST ${url}`);
    }
  });

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/v1/tools/') && url.includes('/chat/stream')) {
      console.log(`[RESPONSE] ${response.status()} ${url}`);
      const body = await response.text();
      console.log(`[BODY] ${body.substring(0, 500)}...`);
    }
  });

  // Login
  await page.goto('http://localhost:5173/login');
  await page.fill('input[type="email"], input[type="text"]', 'e2etest@example.com');
  await page.fill('input[type="password"]', 'Test123456!');
  await page.click('button[type="submit"], button:has-text("登录")');
  await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });

  // Select tool
  await page.waitForSelector('.tool-card', { timeout: 10000 });
  await page.locator('.tool-card').first().click();
  await page.waitForTimeout(2000);

  // Send message
  const chatInput = page.locator('textarea').first();
  await chatInput.fill('Hello');
  await page.locator('[data-testid="send-button"]').first().click();

  console.log('Waiting for response...');
  await page.waitForTimeout(10000);

  // Check sessionStore state via console
  const storeState = await page.evaluate(() => {
    // Try to access Vue devtools
    const app = document.querySelector('#app');

    // Check messages in DOM
    const messages = Array.from(document.querySelectorAll('[data-testid="message-item"]')).map(el => ({
        text: el.textContent?.substring(0, 50),
        class: el.getAttribute('class')
      }));

    return {
      messageCount: messages.length,
      messages: messages,
      messageListText: document.querySelector('[data-testid="message-list"]')?.textContent
    };
  });

  console.log('\n=== Store State ===');
  console.log(JSON.stringify(storeState, null, 2));

  await page.screenshot({ path: 'test-results/sessionstore-state.png', fullPage: true });
});
