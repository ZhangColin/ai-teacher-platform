/**
 * UI 交互测试 - 不依赖真实 API 响应
 */
import { test, expect } from '@playwright/test';

test.describe('前端 UI 交互', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5174/');
  });

  test('应该显示登录页面或主页面', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');

    // 检查是否有登录表单或主页面元素
    const loginForm = page.locator('input[type="email"], input[type="text"]').first();
    const mainContent = page.locator('#app').first();

    // 应该至少有一个存在
    await expect(loginForm.or(mainContent).first()).toBeVisible();
  });

  test('应该能够导航到工具页面', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // 尝试导航到工具页面
    await page.goto('http://localhost:5174/modules/ai_tools');

    // 等待页面加载
    await page.waitForLoadState('domcontentloaded');

    // 验证URL
    expect(page.url()).toContain('/modules/ai_tools');
  });

  test('应该显示Vue应用容器', async ({ page }) => {
    const app = page.locator('#app');

    // 应该存在 #app 元素
    await expect(app).toBeVisible();

    // 应该有内容
    const appContent = await app.innerHTML();
    expect(appContent.trim().length).toBeGreaterThan(0);
  });

  test('应该加载必要的JavaScript资源', async ({ page }) => {
    // 检查是否有脚本标签
    const scripts = await page.locator('script').count();
    expect(scripts).toBeGreaterThan(0);

    // 检查是否有主要的Vue应用脚本
    const mainScript = page.locator('script[src*="main"]').or(
      page.locator('script[type="module"]')
    ).first();

    await expect(mainScript).toBeAttached();
  });
});

test.describe('API 可访问性', () => {
  test('后端健康检查', async ({ request }) => {
    const response = await request.get('http://localhost:8000/openapi.json');

    expect(response.status()).toBe(200);

    const api = await response.json();
    expect(api.info).toBeDefined();
    expect(api.paths).toBeDefined();
  });

  test('工具列表API端点存在', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/tools');

    // 应该返回401（未认证）或200（如果不需要认证）
    expect([200, 401]).toContain(response.status());
  });

  test('工具集API端点存在', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/toolsets/ai_tools/tools');

    // 应该返回401（未认证）或200（如果不需要认证）
    expect([200, 401]).toContain(response.status());
  });
});
