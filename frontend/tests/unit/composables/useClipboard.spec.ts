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
})
