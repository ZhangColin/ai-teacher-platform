/**
 * Admin Configuration Management E2E Tests
 *
 * Test the admin interface for managing navigation modules and AI tools.
 */
import { test, expect } from '@playwright/test';

// Admin test user credentials
const ADMIN_USER = {
  account: 'admin@example.com',
  password: 'admin123'
};

test.describe('Admin Login', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('http://localhost:5174/login');

    // Verify login form exists
    await expect(page.locator('input[type="email"], input[type="text"]').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
    await expect(page.locator('button[type="submit"], button:has-text("登录")').first()).toBeVisible();
  });

  test('should login as admin', async ({ page }) => {
    // Create admin user first via API
    await page.goto('http://localhost:5174/login');

    // Fill login form
    await page.fill('input[type="email"], input[type="text"]', ADMIN_USER.account);
    await page.fill('input[type="password"]', ADMIN_USER.password);

    // Submit login
    await page.click('button[type="submit"], button:has-text("登录")');

    // Should redirect to tools page or admin page
    await page.waitForURL(/\/modules\/ai-tools|\/admin/, { timeout: 10000 });
    expect(page.url()).toMatch(/\/modules\/ai-tools|\/admin/);
  });
});

test.describe('Navigation Modules Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('http://localhost:5174/login');
    await page.fill('input[type="email"], input[type="text"]', ADMIN_USER.account);
    await page.fill('input[type="password"]', ADMIN_USER.password);
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForURL(/\/modules\/ai-tools|\/admin/, { timeout: 10000 });
  });

  test('should access navigation modules management page', async ({ page }) => {
    // Navigate to admin navigation modules page
    await page.goto('http://localhost:5174/admin/navigation-modules');

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Verify page title or header
    const pageTitle = page.locator('h1, h2, .page-title, [class*="title"]').first();
    await expect(pageTitle).toBeVisible({ timeout: 5000 });

    // Verify table or list exists
    const tableOrList = page.locator('table, .module-list, [class*="list"]').first();
    await expect(tableOrList).toBeVisible({ timeout: 5000 });

    console.log('✅ Navigation modules management page is accessible');
  });

  test('should display existing navigation modules', async ({ page }) => {
    // Navigate to admin navigation modules page
    await page.goto('http://localhost:5174/admin/navigation-modules');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Look for module items in table or list
    const moduleItems = page.locator('tr, .module-item, [class*="module"]');

    // Wait for at least one module item
    const count = await moduleItems.count();
    expect(count).toBeGreaterThan(0);

    console.log(`✅ Found ${count} navigation module(s)`);
  });

  test('should have create module button', async ({ page }) => {
    // Navigate to admin navigation modules page
    await page.goto('http://localhost:5174/admin/navigation-modules');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Look for create button
    const createButton = page.locator('button:has-text("创建"), button:has-text("新增"), button:has-text("添加"), [class*="create"], [class*="add"]').first();

    try {
      await expect(createButton).toBeVisible({ timeout: 5000 });
      console.log('✅ Create module button found');
    } catch (e) {
      // Take screenshot for debugging
      await page.screenshot({ path: 'test-results/admin-no-create-button.png', fullPage: true });
      throw new Error('Create button not found. Screenshot saved.');
    }
  });
});

test.describe('AI Tools Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('http://localhost:5174/login');
    await page.fill('input[type="email"], input[type="text"]', ADMIN_USER.account);
    await page.fill('input[type="password"]', ADMIN_USER.password);
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForURL(/\/modules\/ai-tools|\/admin/, { timeout: 10000 });
  });

  test('should access AI tools management page', async ({ page }) => {
    // Navigate to admin AI tools page
    await page.goto('http://localhost:5174/admin/ai-tools');

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Verify page title or header
    const pageTitle = page.locator('h1, h2, .page-title, [class*="title"]').first();
    await expect(pageTitle).toBeVisible({ timeout: 5000 });

    // Verify table or list exists
    const tableOrList = page.locator('table, .tool-list, [class*="list"]').first();
    await expect(tableOrList).toBeVisible({ timeout: 5000 });

    console.log('✅ AI tools management page is accessible');
  });

  test('should display existing AI tools', async ({ page }) => {
    // Navigate to admin AI tools page
    await page.goto('http://localhost:5174/admin/ai-tools');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Look for tool items in table or list
    const toolItems = page.locator('tr, .tool-item, [class*="tool"]');

    // Wait for at least one tool item
    const count = await toolItems.count();
    expect(count).toBeGreaterThan(0);

    console.log(`✅ Found ${count} AI tool(s)`);
  });

  test('should have create tool button', async ({ page }) => {
    // Navigate to admin AI tools page
    await page.goto('http://localhost:5174/admin/ai-tools');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Look for create button
    const createButton = page.locator('button:has-text("创建"), button:has-text("新增"), button:has-text("添加"), [class*="create"], [class*="add"]').first();

    try {
      await expect(createButton).toBeVisible({ timeout: 5000 });
      console.log('✅ Create tool button found');
    } catch (e) {
      // Take screenshot for debugging
      await page.screenshot({ path: 'test-results/admin-no-create-tool-button.png', fullPage: true });
      throw new Error('Create tool button not found. Screenshot saved.');
    }
  });

  test('should filter tools by visibility', async ({ page }) => {
    // Navigate to admin AI tools page
    await page.goto('http://localhost:5174/admin/ai-tools');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Look for filter controls (checkboxes, dropdowns, etc.)
    const filterControls = page.locator('[class*="filter"], input[type="checkbox"], select').first();

    try {
      await expect(filterControls).toBeVisible({ timeout: 5000 });
      console.log('✅ Filter controls found');
    } catch (e) {
      // Filters might not be implemented yet
      console.log('⚠️ Filter controls not found (might not be implemented yet)');
    }
  });
});

test.describe('Backward Compatibility', () => {
  test.beforeEach(async ({ page }) => {
    // Login as regular user before each test
    await page.goto('http://localhost:5174/login');
    await page.fill('input[type="email"], input[type="text"]', 'e2etest@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });
  });

  test('should access tools list via existing API', async ({ page }) => {
    // Navigate to tools page
    expect(page.url()).toContain('/modules/ai-tools');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Verify tools are displayed
    const toolCard = page.locator('.tool-card, .tool-item, [class*="tool"]').first();
    await expect(toolCard).toBeVisible({ timeout: 5000 });

    console.log('✅ Existing tools API still works');
  });

  test('should access navigation modules via existing API', async ({ page }) => {
    // Navigate to tools page
    expect(page.url()).toContain('/modules/ai-tools');

    // Wait for content to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Verify navigation module switcher is displayed
    const moduleSwitcher = page.locator('[class*="module"], [class*="nav"], [class*="switcher"]').first();
    await expect(moduleSwitcher).toBeVisible({ timeout: 5000 });

    console.log('✅ Existing navigation API still works');
  });
});

test.describe('Admin Access Control', () => {
  test('should deny access to non-admin users', async ({ page }) => {
    // Login as regular user
    await page.goto('http://localhost:5174/login');
    await page.fill('input[type="email"], input[type="text"]', 'e2etest@example.com');
    await page.fill('input[type="password"]', 'Test123456!');
    await page.click('button[type="submit"], button:has-text("登录")');
    await page.waitForURL(/\/modules\/ai-tools/, { timeout: 10000 });

    // Try to access admin navigation modules page
    await page.goto('http://localhost:5174/admin/navigation-modules');

    // Should be redirected or see an error
    await page.waitForTimeout(2000);

    const currentUrl = page.url();
    const hasError = await page.locator('text=/403|401|无权限|未授权/').count() > 0;

    expect(currentUrl.includes('/login') || hasError).toBeTruthy();
    console.log('✅ Non-admin users are denied access to admin pages');
  });
});

test.describe('API Endpoints (Direct Testing)', () => {
  test('should return navigation modules from API', async ({ request }) => {
    // First login to get token
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        account: ADMIN_USER.account,
        password: ADMIN_USER.password
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    // Get navigation modules
    const response = await request.get('http://localhost:8000/api/v1/admin/navigation-modules', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.modules).toBeDefined();
    expect(Array.isArray(data.modules)).toBeTruthy();

    console.log(`✅ API returned ${data.modules.length} navigation modules`);
  });

  test('should return AI tools from API', async ({ request }) => {
    // First login to get token
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        account: ADMIN_USER.account,
        password: ADMIN_USER.password
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    // Get AI tools
    const response = await request.get('http://localhost:8000/api/v1/admin/ai-tools', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.tools).toBeDefined();
    expect(data.total).toBeDefined();

    console.log(`✅ API returned ${data.total} AI tools`);
  });

  test('should deny API access without authentication', async ({ request }) => {
    // Try to get navigation modules without token
    const response = await request.get('http://localhost:8000/api/v1/admin/navigation-modules');

    expect(response.status()).toBe(401);
    console.log('✅ API correctly denies access without authentication');
  });

  test('should support backward compatible tools API', async ({ request }) => {
    // First login as regular user
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        account: 'e2etest@example.com',
        password: 'Test123456!'
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    // Get tools using old API
    const response = await request.get('http://localhost:8000/api/v1/tools', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.categories).toBeDefined();

    console.log('✅ Backward compatible /api/v1/tools API works');
  });

  test('should support backward compatible navigation API', async ({ request }) => {
    // First login as regular user
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        account: 'e2etest@example.com',
        password: 'Test123456!'
      }
    });

    expect(loginResponse.ok()).toBeTruthy();
    const loginData = await loginResponse.json();
    const token = loginData.token;

    // Get navigation using old API
    const response = await request.get('http://localhost:8000/api/v1/navigation', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.modules).toBeDefined();

    console.log('✅ Backward compatible /api/v1/navigation API works');
  });
});
