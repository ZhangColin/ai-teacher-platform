import { describe, it, expect, vi, beforeEach } from 'vitest'
import { downloadWord } from '@/utils/documentDownloader'

describe('downloadWord', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.restoreAllMocks()
  })

  it('should download Word document successfully', async () => {
    const mockBlob = new Blob(['test'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => mockBlob
    } as Response))

    // Mock URL.createObjectURL and revokeObjectURL
    const mockUrl = 'blob:test-url'
    vi.spyOn(URL, 'createObjectURL').mockReturnValue(mockUrl)
    vi.spyOn(URL, 'revokeObjectURL')

    // Mock createElement to return a proper anchor element
    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
      style: {}
    }
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)

    // Mock body.appendChild
    vi.spyOn(document.body, 'appendChild').mockReturnValue(mockAnchor as any)

    await downloadWord('# Test\n\nThis is a test.', 'test-document.docx')

    expect(fetch).toHaveBeenCalledWith('/api/v1/convert/markdown-to-word', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ markdown: '# Test\n\nThis is a test.' })
    })
    expect(createElementSpy).toHaveBeenCalledWith('a')
    expect(mockAnchor.href).toBe(mockUrl)
    expect(mockAnchor.download).toBe('test-document.docx')
    expect(mockAnchor.click).toHaveBeenCalled()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith(mockUrl)
  })

  it('should handle API errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Internal Server Error'
    } as Response))

    await expect(downloadWord('# Test')).rejects.toThrow('转换失败: Internal Server Error')
  })

  it('should handle network errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    await expect(downloadWord('# Test')).rejects.toThrow('Network error')
  })

  it('should clean up Blob URL after download', async () => {
    const mockBlob = new Blob(['test'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => mockBlob
    } as Response))

    // Mock URL.createObjectURL and revokeObjectURL
    const mockUrl = 'blob:test-url'
    vi.spyOn(URL, 'createObjectURL').mockReturnValue(mockUrl)
    const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL')

    // Mock createElement to return a proper anchor element
    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
      style: {}
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)
    vi.spyOn(document.body, 'appendChild').mockReturnValue(mockAnchor as any)

    await downloadWord('# Test')

    expect(revokeObjectURLSpy).toHaveBeenCalledWith(mockUrl)
  })

  it('should use default filename if not provided', async () => {
    const mockBlob = new Blob(['test'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => mockBlob
    } as Response))

    const mockUrl = 'blob:test-url'
    vi.spyOn(URL, 'createObjectURL').mockReturnValue(mockUrl)
    vi.spyOn(URL, 'revokeObjectURL')

    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
      style: {}
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)
    vi.spyOn(document.body, 'appendChild').mockReturnValue(mockAnchor as any)

    await downloadWord('# Test')

    expect(mockAnchor.download).toBe('document.docx')
  })

  it('should use custom filename if provided', async () => {
    const mockBlob = new Blob(['test'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => mockBlob
    } as Response))

    const mockUrl = 'blob:test-url'
    vi.spyOn(URL, 'createObjectURL').mockReturnValue(mockUrl)
    vi.spyOn(URL, 'revokeObjectURL')

    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn(),
      style: {}
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)
    vi.spyOn(document.body, 'appendChild').mockReturnValue(mockAnchor as any)

    await downloadWord('# Test', 'custom-name.docx')

    expect(mockAnchor.download).toBe('custom-name.docx')
  })
})
