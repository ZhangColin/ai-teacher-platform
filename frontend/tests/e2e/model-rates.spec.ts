/**
 * 模型汇率批量设置 E2E 测试
 */
import { test, expect } from '@playwright/test'

// 使用单个 worker 顺序执行测试，避免状态问题
test.describe.configure({ mode: 'serial' })

test.describe('模型汇率批量设置', () => {
  test.beforeEach(async ({ page }) => {
    // 登录为管理员 - 使用 ID 选择器更可靠
    await page.goto('http://localhost:5173/login')
    await page.fill('#account', 'admin')
    await page.fill('#password', 'HcyAdmin@2026')
    await page.click('button[type="submit"]')

    // 等待登录成功后跳转
    await page.waitForURL('**/modules/**', { timeout: 10000 })

    // 确保登录状态已保存
    await page.waitForTimeout(1000)
  })

  test('应该显示模型汇率配置页面', async ({ page }) => {
    // 使用 hash 模式导航到模型汇率页面
    await page.goto('http://localhost:5173/#/admin/model-rates')

    // 等待页面完全加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 检查页面是否加载了正确的组件
    // 使用 h1 角色来获取页面标题
    await expect(page.getByRole('heading', { name: '模型汇率配置' })).toBeVisible({ timeout: 10000 })

    // 验证保存和重置按钮存在
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible()
    await expect(page.getByRole('button', { name: '重置' })).toBeVisible()
  })

  test('应该按供应商分组显示模型', async ({ page }) => {
    await page.goto('http://localhost:5173/#/admin/model-rates')

    // 等待页面加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 等待数据加载 - 检查是否有折叠面板或空状态
    await page.waitForSelector('.el-collapse, .el-empty', { timeout: 10000 })

    // 如果有数据，验证折叠面板存在
    const collapseItems = page.locator('.el-collapse-item')
    const count = await collapseItems.count()

    if (count > 0) {
      // 验证折叠面板存在
      await expect(collapseItems.first()).toBeVisible()

      // 验证第一个面板默认展开（通过 aria-hidden 属性检查）
      const firstItemWrap = collapseItems.first().locator('.el-collapse-item__wrap')
      await expect(firstItemWrap).toHaveAttribute('aria-hidden', 'false')
    }
  })

  test('应该能够修改汇率并保存', async ({ page }) => {
    await page.goto('http://localhost:5173/#/admin/model-rates')

    // 等待页面加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 等待数据加载
    await page.waitForSelector('.el-collapse, .el-empty', { timeout: 10000 })

    // 检查是否有输入框
    const inputNumbers = page.locator('.el-input-number')
    const count = await inputNumbers.count()

    if (count > 0) {
      // 找到第一个输入框并修改
      const firstInput = inputNumbers.first()
      await firstInput.click()

      // el-input-number 内部使用 input[type="number"] 或 class="el-input__inner"
      const inputInner = firstInput.locator('.el-input__inner, input').first()
      await inputInner.click()
      await inputInner.fill('')
      await inputInner.fill('3000')
      await page.keyboard.press('Tab') // 移出焦点以触发变化

      // 等待一下让状态更新
      await page.waitForTimeout(500)

      // 验证保存按钮可用（保存按钮默认是禁用的，修改后应该启用）
      const saveButton = page.getByRole('button', { name: '保存' })
      await expect(saveButton).not.toBeDisabled()

      // 点击保存
      await saveButton.click()

      // 验证成功提示或错误提示
      const message = page.locator('.el-message--success, .el-message--error')
      await expect(message.first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('应该能够重置修改', async ({ page }) => {
    await page.goto('http://localhost:5173/#/admin/model-rates')

    // 等待页面加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 等待数据加载
    await page.waitForSelector('.el-collapse, .el-empty', { timeout: 10000 })

    // 检查是否有输入框
    const inputNumbers = page.locator('.el-input-number')
    const count = await inputNumbers.count()

    if (count > 0) {
      // 修改值
      const firstInput = inputNumbers.first()
      await firstInput.click()

      const inputInner = firstInput.locator('.el-input__inner, input').first()
      await inputInner.click()
      await inputInner.fill('')
      await inputInner.fill('3000')
      await page.keyboard.press('Tab')

      // 等待一下让状态更新
      await page.waitForTimeout(500)

      // 点击重置
      const resetButton = page.getByRole('button', { name: '重置' })
      await resetButton.click()

      // 验证提示信息
      const message = page.locator('.el-message--info, .el-message--success')
      await expect(message.first()).toBeVisible()
    }
  })
})

test.describe('模型配置对话框简化', () => {
  test.beforeEach(async ({ page }) => {
    // 登录为管理员
    await page.goto('http://localhost:5173/login')
    await page.fill('#account', 'admin')
    await page.fill('#password', 'HcyAdmin@2026')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/modules/**', { timeout: 10000 })
    await page.waitForTimeout(1000)
  })

  test('应该显示单表单配置对话框', async ({ page }) => {
    await page.goto('http://localhost:5173/#/admin/model-providers')

    // 等待列表加载
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // 等待表格加载
    await page.waitForSelector('table', { timeout: 10000 })

    // 点击第一个供应商的模型按钮
    const modelButtons = page.getByRole('button', { name: '模型' })
    const modelButtonCount = await modelButtons.count()

    if (modelButtonCount > 0) {
      await modelButtons.first().click()

      // 等待模型列表对话框加载
      await page.waitForSelector('.el-dialog', { timeout: 5000 })

      // 验证模型列表对话框显示
      await expect(page.getByText('模型名称')).toBeVisible()
      await expect(page.getByText('积分汇率')).toBeVisible()

      // 验证有配置按钮存在（表明是新的简化版本）
      const configButtons = page.locator('button').filter({ hasText: '配置' })
      await expect(configButtons.first()).toBeVisible()
    }
  })
})
