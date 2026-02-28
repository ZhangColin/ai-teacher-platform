/**
 * Downloads a PDF document by converting an HTML element using html2pdf.js
 *
 * @param elementId - The ID of the HTML element to convert to PDF
 * @param filename - The filename for the downloaded PDF (default: 'document.pdf')
 * @throws Error if the element is not found or conversion fails
 */
export default async function downloadPdf(
  elementId: string,
  filename = 'document.pdf'
): Promise<void> {
  try {
    const element = document.getElementById(elementId)
    if (!element) {
      throw new Error(`找不到要转换的元素: ${elementId}`)
    }

    // Configure html2pdf options for high-quality output
    const opt = {
      margin: 10, // margin in mm
      filename,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2, // Higher scale for better quality
        useCORS: true, // Enable CORS for images
        logging: false // Disable logging
      },
      jsPDF: {
        unit: 'mm',
        format: 'a4',
        orientation: 'portrait'
      }
    }

    // Generate and save PDF
    await (await import('html2pdf.js')).default().set(opt).from(element).save()
  } catch (error) {
    console.error('PDF 下载失败:', error)
    throw error
  }
}
