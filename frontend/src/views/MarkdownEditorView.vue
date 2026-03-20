<template>
  <div class="markdown-editor-view">
    <!-- 顶部工具条 -->
    <div class="toolbar">
      <div class="toolbar-title">
        <DocumentTextIcon class="w-5 h-5 text-blue-600" />
        <span>Markdown 编辑器</span>
      </div>
      <div class="toolbar-actions">
        <button class="toolbar-btn" @click="handleClear" title="清空内容">
          <TrashIcon class="w-4 h-4" />
          <span>清空</span>
        </button>
        <button class="toolbar-btn back-btn" @click="handleBack">
          <ArrowLeftIcon class="w-5 h-5" />
          <span>返回</span>
        </button>
      </div>
    </div>

    <!-- Markdown 编辑器组件 -->
    <MarkdownEditor v-model="editorContent" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeftIcon, DocumentTextIcon, TrashIcon } from '@heroicons/vue/24/outline'
import MarkdownEditor from '../components/editor/MarkdownEditor.vue'

const router = useRouter()

// 编辑器内容
const editorContent = ref(`# 欢迎使用 Markdown 编辑器

这是一个功能强大的在线 Markdown 编辑器，支持实时预览。

## 功能特性

- ✅ 实时预览
- ✅ 语法高亮
- ✅ 支持数学公式（KaTeX）
- ✅ 导出为 Markdown、Word、PDF

## 数学公式示例

行内公式：$E = mc^2$

块级公式：

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

## 代码示例

\`\`\`javascript
function hello() {
}
\`\`\`

## 表格示例

| 功能 | 状态 |
|------|------|
| 编辑 | ✅ |
| 预览 | ✅ |
| 导出 | ✅ |

---

开始编辑你的内容吧！
`)

/**
 * 返回工具列表
 */
const handleBack = () => {
  router.push('/common-tools')
}

/**
 * 清空编辑器内容
 */
const handleClear = () => {
  if (confirm('确定要清空所有内容吗？此操作不可撤销。')) {
    editorContent.value = ''
  }
}
</script>

<style scoped>
.markdown-editor-view {
  @apply h-full w-full overflow-hidden flex flex-col;
  background-color: theme('colors.gray.50');
}

/* 顶部工具条 */
.toolbar {
  @apply flex items-center gap-4 px-6 py-3 bg-white border-b border-gray-200;
  flex-shrink: 0;
}

.toolbar-btn {
  @apply flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all;
}

.toolbar-btn:hover {
  @apply shadow-sm;
}

.back-btn {
  @apply text-gray-600 hover:text-gray-900;
}

.toolbar-title {
  @apply flex items-center gap-2 text-lg font-semibold text-gray-900 flex-1;
}

.toolbar-actions {
  @apply flex items-center gap-2;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .toolbar-title {
    @apply text-base;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .toolbar {
    @apply px-4 py-2 gap-2;
  }

  .toolbar-title {
    @apply text-sm;
  }

  .toolbar-btn span {
    @apply hidden;
  }
}
</style>
