/**
 * Debug script to investigate E2E chat area issue
 */
import { test, expect } from '@playwright/test';

const TEST_USER = {
  account: 'e2etest@example.com',
  password: 'Test123456!'
};

test.describe('Debug - Chat Area Rendering', () => {
  test('investigate why chat area is not showing', async ({ page }) => {
    // Capture console logs and errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        console.log('Browser Console Error:', text);
        consoleErrors.push(text);
      }
    });
    page.on('pageerror', err => {
      console.log('Browser Page Error:', err.message);
      consoleErrors.push(err.message);
    });

    // Capture network requests
    const apiRequests: { url: string; status?: number; method: string }[] = [];
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/')) {
        console.log('API Request:', request.method(), url);
        apiRequests.push({ url, method: request.method() });
      }
    });
    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/api/')) {
        const status = response.status();
        console.log('API Response:', status, url);
        const req = apiRequests.find(r => r.url === url);
        if (req) req.status = status;

        // Log conversations API response body
        if (url.includes('/conversations')) {
          try {
            const body = await response.json();
            console.log('Conversations API body:', JSON.stringify(body));
          } catch (e) {
            console.log('Failed to parse conversations response:', e);
          }
        }

        // Log tools API response body
        if (url.includes('/tools') && url.includes('/toolsets')) {
          try {
            const body = await response.json();
            console.log('Tools API body:', JSON.stringify(body));
          } catch (e) {
            console.log('Failed to parse tools response:', e);
          }
        }
      }
    });
    console.log('=== Step 1: Login ===');
    await page.goto('http://localhost:5174/login');
    await page.fill('input[type="email"], input[type="text"]', TEST_USER.account);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });

    console.log('=== Step 2: Check page structure ===');

    // Wait for tools to load - wait for loading to disappear
    try {
      await page.waitForSelector('.tool-card', { timeout: 15000 });
      console.log('✓ Tools loaded successfully');
    } catch (e) {
      console.log('⚠ Tools did not load in 15 seconds, will diagnose...');
    }

    // Take screenshot of current state
    await page.screenshot({ path: 'test-results/debug-01-after-login.png', fullPage: true });

    // Check for loading state
    const loadingText = page.locator('text=/加载工具列表/');
    const loadingCount = await loadingText.count();
    console.log(`Loading indicators found: ${loadingCount}`);

    // Check for error state
    const errorText = page.locator('.error-text');
    const errorCount = await errorText.count();
    console.log(`Error indicators found: ${errorCount}`);
    if (errorCount > 0) {
      const errorMessages = await errorText.allTextContents();
      console.log('Error messages:', errorMessages);
    }

    // Check for sidebar
    const sidebar = page.locator('.sidebar, .tool-selector');
    const sidebarCount = await sidebar.count();
    console.log(`Sidebar elements found: ${sidebarCount}`);

    console.log('=== Step 3: Find tools ===');
    const toolCards = await page.locator('.tool-card').count();
    console.log(`Found ${toolCards} tool cards`);

    if (toolCards > 0) {
      const firstCardText = await page.locator('.tool-card').first().textContent();
      console.log(`First tool card text: ${firstCardText}`);

      console.log('=== Step 4: Click first tool ===');
      await page.locator('.tool-card').first().click();
      await page.waitForTimeout(3000);

      // Screenshot after click
      await page.screenshot({ path: 'test-results/debug-02-after-click-tool.png', fullPage: true });

      console.log('=== Step 5: Check for chat area ===');

      // Check for ChatArea or any chat-related elements
      const chatArea = page.locator('.chat-area, .chat-panel, .conversation, .ChatArea');
      const chatCount = await chatArea.count();
      console.log(`Chat area elements found: ${chatCount}`);

      // Check for textarea
      const textarea = page.locator('textarea');
      const textareaCount = await textarea.count();
      console.log(`Textarea elements found: ${textareaCount}`);

      // List all iframes
      const iframes = await page.locator('iframe').count();
      console.log(`Iframes found: ${iframes}`);

      // Check page body classes
      const bodyClass = await page.locator('body').getAttribute('class');
      console.log(`Body classes: ${bodyClass}`);

      console.log('=== Step 6: Check Vue app state ===');

      // Try to get Vue app state
      const appHTML = await page.locator('#app').innerHTML();
      console.log('App HTML preview:', appHTML.substring(0, 1000));

    } else {
      console.log('❌ No tool cards found!');
      console.log('Checking page content for clues...');

      // Check what's actually in the main content area
      const mainContent = page.locator('.main-content, main');
      const mainHTML = await mainContent.innerHTML();
      console.log('Main content HTML preview:', mainHTML.substring(0, 500));

      // Check all divs with class containing 'tool'
      const toolDivs = await page.locator('div[class*="tool"]').count();
      console.log(`Divs with 'tool' in class: ${toolDivs}`);

      // List all visible text
      const bodyText = await page.locator('body').textContent();
      console.log('Page text preview:', bodyText?.substring(0, 500));
    }

    console.log('=== Step 7: Report console errors ===');
    if (consoleErrors.length > 0) {
      console.log('Console errors found:', consoleErrors);
    } else {
      console.log('No console errors');
    }

    // Additional debugging: check Vue app state
    console.log('=== Step 8: Check Vue app state ===');
    const vueState = await page.evaluate(() => {
      const app = document.querySelector('#app')?.__vueParentComponent;
      return {
        hasVue: !!app,
        appKeys: app ? Object.keys(app) : [],
      };
    });
    console.log('Vue state:', JSON.stringify(vueState));
  });
});
