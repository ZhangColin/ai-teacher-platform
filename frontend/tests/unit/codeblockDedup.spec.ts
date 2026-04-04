import { describe, it, expect } from 'vitest'

// 辅助函数（从 sessionStore.ts 复制）
function calculateSimilarity(str1: string, str2: string): number {
  const len = Math.min(str1.length, str2.length)
  if (len === 0) return 0

  let sameChars = 0
  for (let i = 0; i < len; i++) {
    if (str1[i] === str2[i]) sameChars++
  }

  return sameChars / len
}

function findSplitPosition(current: string, newContent: string): number {
  const maxCheck = Math.min(200, current.length, newContent.length)

  for (let i = maxCheck; i >= 10; i--) {
    const currentEnd = current.slice(-i).toLowerCase()
    const newStart = newContent.slice(0, i).toLowerCase()

    if (currentEnd === newStart) {
      return i
    }
  }

  return 0
}

describe('代码块去重逻辑', () => {
  describe('calculateSimilarity', () => {
    it('应该计算完全相同字符串的相似度为1', () => {
      const result = calculateSimilarity('hello', 'hello')
      expect(result).toBe(1.0)
    })

    it('应该计算完全不同字符串的相似度为0', () => {
      const result = calculateSimilarity('abc', 'xyz')
      expect(result).toBe(0)
    })

    it('应该计算部分相似字符串的相似度', () => {
      const result = calculateSimilarity('hello world', 'hello there')
      expect(result).toBeGreaterThan(0.5)
    })

    it('应该处理空字符串', () => {
      const result = calculateSimilarity('', 'hello')
      expect(result).toBe(0)
    })

    it('应该处理长度不同的字符串', () => {
      const result = calculateSimilarity('hi', 'hello')
      expect(result).toBe(0.5) // "hi" 是2个字符，"hello"的前2个字符都匹配，所以是 2/2 = 1.0，但算法取最小长度
    })
  })

  describe('findSplitPosition', () => {
    it('应该找到重复内容的分割点', () => {
      const current = '这是前面的内容<div class="container">'
      const newContent = '<div class="container">这是新的内容'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBeGreaterThan(0)
      expect(splitPos).toBe(23) // 找到了23个字符的重复（'div class="container">'）
    })

    it('应该在没有重复时返回0', () => {
      const current = '这是前面的内容'
      const newContent = '这是完全新的内容'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(0)
    })

    it('应该处理短字符串', () => {
      const current = 'abc'
      const newContent = 'abcxyz'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(0) // 小于最小阈值10，所以返回0
    })

    it('应该不区分大小写', () => {
      const current = 'DIV CLASS="container"'
      const newContent = 'div class="container">新的内容'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBeGreaterThan(0)
    })

    it('应该处理超过最大检查长度的情况', () => {
      const current = 'a'.repeat(300)
      const newContent = 'a'.repeat(200) + 'b'.repeat(100)

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(200) // 最大检查长度是200
    })

    it('应该在重复部分小于10字符时返回0', () => {
      const current = 'abc'
      const newContent = 'abcde'

      const splitPos = findSplitPosition(current, newContent)
      expect(splitPos).toBe(0) // 小于最小阈值10
    })
  })
})
