import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useClipboard } from '@/composables/useClipboard'

describe('useClipboard', () => {
  beforeEach(() => {
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined)
      }
    })
  })

  it('should copy text to clipboard', async () => {
    const { copy, copiedText } = useClipboard()

    await copy('test message')

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test message')
    expect(copiedText.value).toBe('test message')
  })

  it('should show success toast', async () => {
    vi.useFakeTimers()

    const { copy, showSuccessToast } = useClipboard()

    await copy('test')

    expect(showSuccessToast.value).toBe(true)

    // Fast-forward 2 seconds
    await vi.advanceTimersByTimeAsync(2000)
    expect(showSuccessToast.value).toBe(false)

    vi.useRealTimers()
  })

  describe('error scenarios', () => {
    it('should handle clipboard API errors gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const mockError = new Error('Permission denied')
      vi.mocked(navigator.clipboard.writeText).mockRejectedValueOnce(mockError)

      const { copy, copiedText, showSuccessToast } = useClipboard()

      const result = await copy('test message')

      expect(result).toBe(false)
      expect(copiedText.value).toBe('')
      expect(showSuccessToast.value).toBe(false)
      expect(consoleErrorSpy).toHaveBeenCalledWith('复制失败:', mockError)

      consoleErrorSpy.mockRestore()
    })

    it('should return false when clipboard API is not available', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      // 模拟不支持 clipboard API 的浏览器环境
      vi.stubGlobal('navigator', {})

      const { copy, copiedText, showSuccessToast } = useClipboard()

      const result = await copy('test message')

      expect(result).toBe(false)
      expect(copiedText.value).toBe('')
      expect(showSuccessToast.value).toBe(false)
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '剪贴板 API 在当前浏览器中不可用'
      )

      consoleErrorSpy.mockRestore()

      // 恢复 navigator 以免影响其他测试
      vi.stubGlobal('navigator', {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined)
        }
      })
    })

    it('should return false when clipboard.writeText is not available', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      // 模拟 clipboard 对象存在但 writeText 方法不存在
      vi.stubGlobal('navigator', {
        clipboard: {}
      })

      const { copy, copiedText, showSuccessToast } = useClipboard()

      const result = await copy('test message')

      expect(result).toBe(false)
      expect(copiedText.value).toBe('')
      expect(showSuccessToast.value).toBe(false)
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '剪贴板 API 在当前浏览器中不可用'
      )

      consoleErrorSpy.mockRestore()

      // 恢复 navigator 以免影响其他测试
      vi.stubGlobal('navigator', {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined)
        }
      })
    })
  })

  describe('memory leak prevention', () => {
    it('should clear previous timer when copy is called again', async () => {
      vi.useFakeTimers()

      const { copy, showSuccessToast } = useClipboard()

      // 第一次复制
      await copy('first')
      expect(showSuccessToast.value).toBe(true)

      // 在定时器触发前再次复制
      await copy('second')
      expect(showSuccessToast.value).toBe(true)

      // 前进 2 秒（应该只清除第二个定时器）
      await vi.advanceTimersByTimeAsync(2000)
      expect(showSuccessToast.value).toBe(false)

      vi.useRealTimers()
    })
  })
})
