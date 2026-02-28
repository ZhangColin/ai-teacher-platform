/**
 * Debug Shift+Enter behavior
 */
import { test, expect } from '@playwright/test';

test('debug Shift+Enter', async ({ page }) => {
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

  // Find input
  const chatInput = page.locator('textarea').first();
  await expect(chatInput).toBeVisible({ timeout: 5000 });

  console.log('Testing Shift+Enter behavior...\n');

  // Test 1: Just Enter should send
  console.log('Test 1: Press Enter (should send message)');
  await chatInput.fill('Test message 1');
  await page.waitForTimeout(500);

  const messageCountBefore = await page.locator('[data-testid="message-item"]').count();
  console.log(`  Messages before Enter: ${messageCountBefore}`);

  await chatInput.press('Enter');
  await page.waitForTimeout(2000);

  const messageCountAfter = await page.locator('[data-testid="message-item"]').count();
  console.log(`  Messages after Enter: ${messageCountAfter}`);
  console.log(`  Result: ${messageCountAfter > messageCountBefore ? '✅ Message sent' : '❌ No message sent'}\n`);

  // Test 2: Shift+Enter should NOT send
  console.log('Test 2: Press Shift+Enter (should NOT send message)');
  await chatInput.fill('Line 1');
  await page.waitForTimeout(500);

  const messageCountBefore2 = await page.locator('[data-testid="message-item"]').count();
  console.log(`  Messages before Shift+Enter: ${messageCountBefore2}`);

  await chatInput.press('Shift+Enter');
  await page.waitForTimeout(500);
  await chatInput.type('Line 2');
  await page.waitForTimeout(500);

  const inputValue = await chatInput.inputValue();
  console.log(`  Input value: ${JSON.stringify(inputValue)}`);

  const messageCountAfter2 = await page.locator('[data-testid="message-item"]').count();
  console.log(`  Messages after Shift+Enter: ${messageCountAfter2}`);
  console.log(`  Result: ${messageCountAfter2 === messageCountBefore2 ? '✅ No message sent' : '❌ Message was sent'}`);
  console.log(`  Expected value: ${JSON.stringify('Line 1\nLine 2')}`);
  console.log(`  Actual value: ${JSON.stringify(inputValue)}`);
});
