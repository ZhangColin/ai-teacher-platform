/**
 * Debug network requests
 */
import { test, expect } from '@playwright/test';

const TEST_USER = {
  account: 'e2etest@example.com',
  password: 'Test123456!'
};

test('debug network requests', async ({ page }) => {
  // Log all network requests
  page.on('request', async request => {
    const url = request.url();
    if (url.includes('/api/')) {
      console.log(`[REQUEST] ${request.method()} ${url}`);
      if (request.method() === 'POST') {
        const data = await request.postData();
        console.log(`[POST DATA] ${data?.substring(0, 200)}`);
      }
    }
  });

  // Log console messages
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('ChatArea') || text.includes('sessionStore') || text.includes('sendMessage')) {
      console.log(`[BROWSER LOG] ${text}`);
    }
  });

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/')) {
      const status = response.status();
      console.log(`[RESPONSE] ${status} ${url}`);
      if (url.includes('/chat')) {
        try {
          const body = await response.json();
          console.log(`[CHAT RESPONSE] ${JSON.stringify(body).substring(0, 500)}`);
        } catch (e) {
          const text = await response.text();
          console.log(`[CHAT TEXT] ${text.substring(0, 500)}`);
        }
      }
    }
  });

  // Login
  console.log('=== Login ===');
  await page.goto('http://localhost:5174/login');
  await page.fill('input[type="email"], input[type="text"]', TEST_USER.account);
  await page.fill('input[type="password"]', TEST_USER.password);
  await page.click('button[type="submit"], button:has-text("登录")');
  await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });

  // Wait for tools
  await page.waitForSelector('.tool-card', { timeout: 10000 });
  console.log('✓ Tools loaded');

  // Click first tool
  await page.locator('.tool-card').first().click();
  await page.waitForTimeout(3000);

  // Screenshot after tool selection
  await page.screenshot({ path: 'test-results/debug-after-tool-select.png', fullPage: true });
  console.log('✓ Tool selected');

  // Check what buttons exist
  const buttons = await page.locator('button').all();
  console.log(`Found ${buttons.length} buttons`);
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const text = await buttons[i].textContent();
    console.log(`  Button ${i}: "${text?.trim()}"`);
  }

  // Check for textarea
  const textarea = await page.locator('textarea').count();
  console.log(`Found ${textarea} textareas`);

  // Type and send message
  const chatInput = page.locator('textarea').first();
  await chatInput.fill('Hello AI');
  console.log('✓ Message typed');

  await page.screenshot({ path: 'test-results/debug-after-type.png', fullPage: true });

  // Wait a bit for UI to update
  await page.waitForTimeout(1000);

  // Try different button selectors
  const sendButton = page.locator('[data-testid="send-button"]');
  const sendCount = await sendButton.count();
  console.log(`Found ${sendCount} send buttons`);

  if (sendCount > 0) {
    const buttonText = await sendButton.textContent();
    console.log(`Clicking button: "${buttonText}"`);
    await sendButton.click();
    console.log('✓ Send button clicked');

    // Check Vue app state
    const vueState = await page.evaluate(() => {
      const app = document.querySelector('#app')?.__vueParentComponent;
      return {
        hasVue: !!app,
      };
    });
    console.log('Vue state:', JSON.stringify(vueState));

    // Wait for chat request
    console.log('Waiting for chat API request...');
    await page.waitForTimeout(5000);
  } else {
    console.log('❌ No send button found!');
    await page.screenshot({ path: 'test-results/debug-no-send-button.png', fullPage: true });
  }
  console.log('=== End of test ===');
});
