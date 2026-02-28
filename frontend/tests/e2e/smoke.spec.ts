/**
 * 冒烟测试 - 验证基本功能
 */
import { test, expect } from '@playwright/test';

test.describe('冒烟测试', () => {
  test('应该能访问前端页面', async ({ page }) => {
    // 直接访问运行中的前端服务器
    await page.goto('http://localhost:5174/');

    // 验证页面标题
    await expect(page).toHaveTitle(/海创元AI教育智研云平台/);

    // 验证页面包含应用容器
    await expect(page.locator('#app')).toBeVisible();
  });

  test('应该能访问API文档', async ({ request }) => {
    // 测试后端API可访问性
    const response = await request.get('http://localhost:8000/docs');

    expect(response.status()).toBe(200);
  });

  test('应该能获取OpenAPI规范', async ({ request }) => {
    const response = await request.get('http://localhost:8000/openapi.json');

    expect(response.status()).toBe(200);

    const api = await response.json();
    expect(api.info.title).toBe('AI Teacher Platform Backend');
    expect(api.paths).toBeDefined();
    expect(Object.keys(api.paths).length).toBeGreaterThan(0);
  });
});
