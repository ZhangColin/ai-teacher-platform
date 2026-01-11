import { describe, it, expect } from 'vitest'
import { 
  recommendIcon, 
  recommendToolIcon, 
  recommendWorkIcon,
  recommendCategoryIcon 
} from '../src/utils/iconRecommendation'

describe('Icon Recommendation', () => {
  describe('recommendIcon', () => {
    it('should recommend document-text for document-related names', () => {
      expect(recommendIcon('Markdown编辑器', '')).toBe('document-text')
      expect(recommendIcon('文档工具', '')).toBe('document-text')
      expect(recommendIcon('Text Editor', '')).toBe('document-text')
    })

    it('should recommend chart-bar for chart-related names', () => {
      expect(recommendIcon('数据统计', '')).toBe('chart-bar')
      expect(recommendIcon('图表生成器', '')).toBe('chart-bar')
      expect(recommendIcon('Statistics Tool', '')).toBe('chart-bar')
    })

    it('should recommend code-bracket for code-related names', () => {
      expect(recommendIcon('代码编辑器', '')).toBe('code-bracket')
      expect(recommendIcon('编程工具', '')).toBe('code-bracket')
      expect(recommendIcon('Code Generator', '')).toBe('code-bracket')
    })

    it('should recommend calculator for math-related names', () => {
      expect(recommendIcon('数学计算器', '')).toBe('calculator')
      expect(recommendIcon('公式编辑器', '')).toBe('calculator')
      expect(recommendIcon('Math Tool', '')).toBe('calculator')
    })

    it('should recommend photo for image-related names', () => {
      expect(recommendIcon('图片编辑', '')).toBe('photo')
      expect(recommendIcon('相册管理', '')).toBe('photo')
      expect(recommendIcon('Image Gallery', '')).toBe('photo')
    })

    it('should recommend video-camera for video-related names', () => {
      expect(recommendIcon('视频播放器', '')).toBe('video-camera')
      expect(recommendIcon('录制工具', '')).toBe('video-camera')
      expect(recommendIcon('Video Editor', '')).toBe('video-camera')
    })

    it('should use description for matching', () => {
      expect(recommendIcon('工具', '这是一个代码编辑工具')).toBe('code-bracket')
      expect(recommendIcon('工具', '用于生成图表')).toBe('chart-bar')
    })

    it('should return default icon if no match', () => {
      expect(recommendIcon('未知工具', '', 'wrench')).toBe('wrench')
      expect(recommendIcon('Test', '', 'photo')).toBe('photo')
    })

    it('should be case insensitive', () => {
      expect(recommendIcon('MARKDOWN EDITOR', '')).toBe('document-text')
      expect(recommendIcon('Code Tool', '')).toBe('code-bracket')
    })

    it('should match Chinese and English keywords', () => {
      expect(recommendIcon('文档', '')).toBe('document-text')
      expect(recommendIcon('document', '')).toBe('document-text')
      expect(recommendIcon('代码', '')).toBe('code-bracket')
      expect(recommendIcon('code', '')).toBe('code-bracket')
    })
  })

  describe('recommendToolIcon', () => {
    it('should return wrench as default', () => {
      expect(recommendToolIcon('未知工具')).toBe('wrench')
    })

    it('should recommend appropriate icon based on tool name', () => {
      expect(recommendToolIcon('Markdown编辑器')).toBe('document-text')
      expect(recommendToolIcon('代码生成器')).toBe('code-bracket')
    })
  })

  describe('recommendWorkIcon', () => {
    it('should return photo as default', () => {
      expect(recommendWorkIcon('未知作品')).toBe('photo')
    })

    it('should recommend appropriate icon based on work name', () => {
      expect(recommendWorkIcon('视频作品')).toBe('video-camera')
      expect(recommendWorkIcon('音乐作品')).toBe('musical-note')
    })
  })

  describe('recommendCategoryIcon', () => {
    it('should return puzzle-piece as default', () => {
      expect(recommendCategoryIcon('未知分类')).toBe('puzzle-piece')
    })

    it('should recommend appropriate icon based on category name', () => {
      expect(recommendCategoryIcon('教育类')).toBe('academic-cap')
      expect(recommendCategoryIcon('工具类')).toBe('wrench')
    })
  })
})
