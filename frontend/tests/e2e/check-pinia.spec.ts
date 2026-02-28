/**
 * 直接访问并检查sessionStore状态
 */
import { test, expect } from '@playwright/test';

test('access sessionStore state directly', async ({ page }) => {
  // Enable Vue devtools exposure
  await page.addInitScript(() => {
    window.__VUE_DEVTOOLS_GLOBAL_HOOK__ = {
      apps: []
    };
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

  // Before sending: check messages count
  const beforeCount = await page.evaluate(() => {
    const app = document.querySelector('#app');
    // Try to find Pinia stores
    if ((window as any).__PINIA__) {
      const stores = (window as any).__PINIA__;
      return {
        hasPinia: true,
        storeNames: Object.keys(stores)
      };
    }
    return { hasPinia: false };
  });

  console.log('\n=== Before sending ===');
  console.log(JSON.stringify(beforeCount, null, 2));

  // Send message
  const chatInput = page.locator('textarea').first();
  await chatInput.fill('Hello Store');
  await page.locator('[data-testid="send-button"]').first().click();

  console.log('Message sent, waiting...');

  // After sending: wait and check
  await page.waitForTimeout(8000);

  // Try to access the Vue app's internal state
  const afterState = await page.evaluate(() => {
    // Check if there are any message-item elements now
    const messageItems = document.querySelectorAll('[data-testid="message-item"]');
    const messages = Array.from(messageItems).map(el => ({
      text: el.textContent?.substring(0, 50),
      classes: el.getAttribute('class')
    }));

    return {
      messageItemCount: messageItems.length,
      messages: messages
    };
  });

  console.log('\n=== After sending ===');
  console.log(JSON.stringify(afterState, null, 2));
});
