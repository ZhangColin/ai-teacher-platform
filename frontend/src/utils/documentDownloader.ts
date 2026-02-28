/**
 * Downloads a Word document by converting Markdown content via the backend API
 *
 * @param markdown - The Markdown content to convert
 * @param filename - The filename for the downloaded document (default: 'document.docx')
 * @throws Error if the conversion or download fails
 */
export async function downloadWord(
  markdown: string,
  filename: string = 'document.docx'
): Promise<void> {
  try {
    const response = await fetch('/api/v1/convert/markdown-to-word', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ markdown })
    })

    if (!response.ok) {
      throw new Error(`转换失败: ${response.statusText}`)
    }

    const blob = await response.blob()

    // Create download link
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()

    // Clean up to prevent memory leaks
    window.URL.revokeObjectURL(url)

    // Remove the anchor element from DOM
    // Use try-catch in case the element was already removed
    try {
      document.body.removeChild(a)
    } catch (e) {
      // Element already removed or not in DOM, ignore
    }
  } catch (error) {
    console.error('Word 下载失败:', error)
    throw error
  }
}
