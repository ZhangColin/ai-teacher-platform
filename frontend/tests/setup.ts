/** 测试环境配置 */
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/vue'
import '@testing-library/jest-dom/vitest'

// 每个测试后清理
afterEach(() => {
  cleanup()
})

