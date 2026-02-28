/**
 * 直接检查Vue组件状态
 */
import { test, expect } from '@playwright/test';

test('check Vue component state directly', async ({ page }) => {
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

  // Check if ChatPanel component is rendered and has messages prop
  const chatPanelExists = await page.locator('.chat-panel, [class*="chat-panel"]').count();
  console.log(`ChatPanel elements: ${chatPanelExists}`);

  // Check message-list
  const messageListExists = await page.locator('[data-testid="message-list"]').count();
  console.log(`MessageList elements: ${messageListExists}`);

  // Send message
  const chatInput = page.locator('textarea').first();
  await chatInput.fill('Test');
  await page.locator('[data-testid="send-button"]').first().click();

  // Wait and check if messages appear
  await page.waitForTimeout(10000);

  const messageItems = await page.locator('[data-testid="message-item"]').count();
  console.log(`Message items after sending: ${messageItems}`);

  // Get all elements with class "message" to see what's actually rendered
  const allMessageElements = await page.locator('*').all();
  const elementsWithMessage = [];
  for (const el of allMessageElements) {
    const classes = await el.getAttribute('class');
    if (classes && classes.includes('message')) {
      const text = await el.textContent();
      elementsWithMessage.push({
        tag: await el.evaluate(e => e.tagName),
        class: classes,
        text: text?.substring(0, 50)
      });
    }
  }

  console.log(`\nFound ${elementsWithMessage.length} elements with 'message' in class:`);
  elementsWithMessage.slice(0, 10).forEach(el => {
    console.log(`  ${el.tag} class="${el.class}" text="${el.text}"`);
  });
});
