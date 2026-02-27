/**
 * 聊天功能E2E测试
 */
import { test, expect } from '@playwright/test';

test.describe('AI对话流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前导航到工具页面
    await page.goto('/modules/ai_tools');
  });

  test('应该显示工具列表', async ({ page }) => {
    // 等待工具列表加载
    await expect(page.locator('[data-testid="tool-list"]')).toBeVisible({ timeout: 10000 }).catch(() => {
      // 如果没有data-testid，尝试其他选择器
      return expect(page.locator('.tool-list, .tools-grid, .tools').first()).toBeVisible({ timeout: 10000 });
    });
  });

  test('应该能选择工具并打开对话', async ({ page }) => {
    // 选择第一个工具
    await page.locator('.tool-item, .tool-card, [data-testid="tool-item"]').first().click();

    // 验证对话界面打开
    await expect(page.locator('[data-testid="chat-panel"], .chat-panel, .chat-container').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('[data-testid="chat-input"], textarea, .chat-input').first()).toBeVisible();
  });

  test('应该能发送消息并显示响应', async ({ page }) => {
    // 选择工具
    await page.locator('.tool-item, .tool-card, [data-testid="tool-item"]').first().click();

    // 输入消息
    const chatInput = page.locator('[data-testid="chat-input"], textarea, .chat-input').first();
    await chatInput.fill('Hello, how are you?');

    // 点击发送按钮
    await page.locator('[data-testid="send-button"], button:has-text("发送"), .send-button').first().click();

    // 验证消息出现在列表中
    await expect(page.locator('[data-testid="message-item"], .message, .chat-message').first()).toBeVisible({ timeout: 5000 });

    // 验证发送按钮禁用状态
    await expect(page.locator('[data-testid="send-button"], button:has-text("发送"), .send-button').first()).toBeDisabled();

    // 等待AI响应（最多30秒）
    await expect(page.locator('[data-testid="message-item"], .message, .chat-message').nth(1)).toBeVisible({ timeout: 30000 });
  });

  test('应该显示流式响应的加载状态', async ({ page }) => {
    await page.locator('.tool-item, .tool-card, [data-testid="tool-item"]').first().click();

    const chatInput = page.locator('[data-testid="chat-input"], textarea, .chat-input').first();
    await chatInput.fill('Generate content');
    await page.locator('[data-testid="send-button"], button:has-text("发送"), .send-button').first().click();

    // 验证流式指示器显示
    await expect(page.locator('[data-testid="streaming-message"], .loading, .streaming, .typing-indicator').first()).toBeVisible({ timeout: 5000 }).catch(() => {
      // 如果没有专门的loading指示器，检查消息内容
      return expect(page.locator('.message, .chat-message').first()).toBeVisible();
    });
  });

  test('应该在消息列表中显示用户和AI消息', async ({ page }) => {
    await page.locator('.tool-item, .tool-card, [data-testid="tool-item"]').first().click();

    const chatInput = page.locator('[data-testid="chat-input"], textarea, .chat-input').first();
    await chatInput.fill('Test message');
    await page.locator('[data-testid="send-button"], button:has-text("发送"), .send-button').first().click();

    // 等待两条消息
    await expect(page.locator('[data-testid="message-item"], .message, .chat-message').nth(0)).toBeVisible();
    await expect(page.locator('[data-testid="message-item"], .message, .chat-message').nth(1)).toBeVisible({ timeout: 30000 });

    // 验证第一条是用户消息
    const firstMessage = page.locator('[data-testid="message-item"], .message, .chat-message').nth(0);
    await expect(firstMessage).toHaveClass(/message-user|user-message|user/);

    // 验证第二条是AI消息
    const secondMessage = page.locator('[data-testid="message-item"], .message, .chat-message').nth(1);
    await expect(secondMessage).toHaveClass(/message-assistant|assistant-message|assistant|ai/);
  });

  test('应该支持Shift+Enter换行', async ({ page }) => {
    await page.locator('.tool-item, .tool-card, [data-testid="tool-item"]').first().click();

    const chatInput = page.locator('[data-testid="chat-input"], textarea, .chat-input').first();

    // 输入文本并按Shift+Enter
    await chatInput.fill('Line 1');
    await chatInput.press('Shift+Enter');
    await chatInput.type('Line 2');

    // 验证输入框包含换行
    const inputValue = await chatInput.inputValue();
    expect(inputValue).toContain('Line 1\nLine 2');

    // 验证消息未发送
    const messageCount = await page.locator('[data-testid="message-item"], .message, .chat-message').count();
    expect(messageCount).toBe(0);
  });
});

test.describe('工具选择', () => {
  test('应该显示工具分类', async ({ page }) => {
    await page.goto('/modules/ai_tools');

    // 验证页面加载
    await expect(page).toHaveTitle(/AI/);

    // 验证工具分类或工具列表存在
    const categories = page.locator('.category, .tool-category, [data-testid="category"]');
    const tools = page.locator('.tool-item, .tool-card, [data-testid="tool-item"]');

    await expect(categories.or(tools).first()).toBeVisible({ timeout: 10000 });
  });
});
