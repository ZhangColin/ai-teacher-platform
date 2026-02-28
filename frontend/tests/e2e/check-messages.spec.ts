/**
 * Debug test to check message structure
 */
import { test } from '@playwright/test';

test('check message element structure', async ({ page }) => {
  // Login
  await page.goto('http://localhost:5174/login');
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

  console.log('Waiting for AI response (15 seconds)...');

  // Wait longer for AI response and message rendering
  await page.waitForTimeout(15000);

  // Check Vue app state and messages
  const appState = await page.evaluate(() => {
    const app = document.querySelector('#app');
    return {
      hasVue: !!app,
      messageListCount: document.querySelectorAll('[data-testid="message-list"]').length,
      messageItemClassCount: document.querySelectorAll('.message-item').length,
      allElements: Array.from(document.querySelectorAll('*')).filter(el =>
        el.getAttribute && el.getAttribute('data-testid')?.includes('message')
      ).map(el => ({
        tag: el.tagName,
        testid: el.getAttribute('data-testid'),
        class: el.getAttribute('class'),
        text: el.textContent?.substring(0, 50)
      })),
      // Check localStorage AND sessionStorage for auth token
      hasAuthToken_local: !!localStorage.getItem('auth_token'),
      hasAuthToken_session: !!sessionStorage.getItem('auth_token')
    };
  });

  console.log('\n=== Vue App State ===');
  console.log(JSON.stringify(appState, null, 2));

  // Check console logs for errors
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('error') || text.includes('Error') || text.includes('failed')) {
      console.log(`[ERROR LOG] ${text}`);
    }
  });

  // Check all message elements
  const messages = await page.locator('.message-item, [class*="message"], [class*="chat"]').all();
  console.log(`\n=== Found ${messages.length} message elements ===`);

  // Also check for data-testid="message-item"
  const messageItems = await page.locator('[data-testid="message-item"]').all();
  console.log(`\n=== Found ${messageItems.length} elements with data-testid="message-item" ===`);

  for (let i = 0; i < messageItems.length; i++) {
    const msg = messageItems[i];
    const text = await msg.textContent();
    const classes = await msg.getAttribute('class');
    const role = classes?.includes('user') ? 'USER' : classes?.includes('assistant') ? 'AI' : 'UNKNOWN';
    console.log(`Message ${i} [${role}]:`);
    console.log(`  Classes: ${classes}`);
    console.log(`  Text: ${text?.substring(0, 100)}`);
    console.log(`  Length: ${text?.length || 0}`);
  }

  await page.screenshot({ path: 'test-results/message-structure.png', fullPage: true });
});
