const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    console.log(`[${msg.type()}]`, msg.text());
  });
  page.on('pageerror', err => {
    console.error('[PAGE ERROR]', err.message);
    console.error('Stack:', err.stack);
  });
  
  try {
    console.log('Navigating to login page...');
    await page.goto('http://localhost:5174/login');
    
    console.log('Filling login form...');
    await page.fill('input[type="email"], input[type="text"]', 'e2etest@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    
    console.log('Submitting login...');
    await page.click('button[type="submit"], button:has-text("登录")');
    
    console.log('Waiting for navigation...');
    await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });
    
    console.log('Login successful! Waiting for tools to load...');
    await page.waitForTimeout(10000);
    
    console.log('Taking screenshot...');
    await page.screenshot({ path: 'test-results/manual-test.png', fullPage: true });
    
    console.log('Test complete. Press Ctrl+C to exit.');
    await page.waitForTimeout(60000); // Keep browser open for 60 seconds
  } catch (err) {
    console.error('Test failed:', err);
  } finally {
    await browser.close();
  }
})();
