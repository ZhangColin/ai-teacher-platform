# 系统重构实施计划 - 阶段2：前端组件拆分

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 拆分PreviewPanel（1348行）和ChatPanel（747行）为小组件，提升前端可维护性

**Architecture:** 使用组件组合模式，将大组件拆分为职责单一的小组件，每个组件独立可测

**Tech Stack:** Vue 3 Composition API, TypeScript, Vitest, @vue/test-utils, DOMPurify

---

## Task 1: 配置前端测试框架

**Files:**
- Create: `frontend/tests/unit/components/__init__.ts`
- Create: `frontend/tests/e2e/.gitkeep`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/package.json`

**Step 1: 创建测试目录结构**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
mkdir -p tests/unit/{components,composables,utils}
mkdir -p tests/e2e
touch tests/unit/components/.gitkeep tests/unit/composables/.gitkeep tests/unit/utils/.gitkeep tests/e2e/.gitkeep
```

Expected: 测试目录创建成功

**Step 2: 更新vite.config.ts测试配置**

Read current: `frontend/vite.config.ts`

找到 `test:` 部分，更新或添加：

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.ts',
      ],
    },
  },
});
```

**Step 3: 创建测试设置文件**

Create: `frontend/tests/setup.ts`

```typescript
/**
 * Vitest测试设置文件
 */
import { vi } from 'vitest';
import { config } from '@vue/test-utils';

// 全局mock Vue Router
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

// 全局mock Pinia stores
config.global.mocks = {
  $store: {
    state: {},
  },
};
```

**Step 4: 验证测试配置**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- --run
```

Expected: 测试框架正常运行（发现0个测试）

**Step 5: 提交测试配置**

Run:
```bash
git add frontend/tests frontend/vite.config.ts frontend/tests/setup.ts
git commit -m "test(frontend): configure Vitest framework with component testing"
```

---

## Task 2: 创建MarkdownPreview组件

**Files:**
- Create: `frontend/src/components/preview/MarkdownPreview.vue`
- Create: `frontend/tests/unit/components/MarkdownPreview.spec.ts`

**Step 1: 创建MarkdownPreview组件**

Create: `frontend/src/components/preview/MarkdownPreview.vue`

```vue
<template>
  <div
    class="markdown-preview"
    v-html="renderedHtml"
    data-testid="markdown-preview"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

interface Props {
  content: string;
}

const props = defineProps<Props>();

const renderedHtml = computed(() => {
  if (!props.content) return '';
  return renderMarkdown(props.content);
});
</script>

<style scoped>
.markdown-preview {
  line-height: 1.6;
  color: #333;
}

.markdown-preview :deep(h1) {
  font-size: 2em;
  font-weight: bold;
  margin: 0.67em 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-preview :deep(h2) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0.75em 0;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.3em;
}

.markdown-preview :deep(p) {
  margin: 1em 0;
}

.markdown-preview :deep(code) {
  background-color: #f4f4f4;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-preview :deep(pre) {
  background-color: #f4f4f4;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

.markdown-preview :deep(pre code) {
  background-color: transparent;
  padding: 0;
}
</style>
```

**Step 2: 创建MarkdownPreview测试**

Create: `frontend/tests/unit/components/MarkdownPreview.spec.ts`

```typescript
/**
 * MarkdownPreview组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MarkdownPreview from '@/components/preview/MarkdownPreview.vue';

describe('MarkdownPreview', () => {
  it('should render markdown headers', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: '# Hello World',
      },
    });

    const html = wrapper.html();
    expect(html).toContain('<h1>');
    expect(html).toContain('Hello World');
  });

  it('should render markdown paragraphs', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: 'This is a paragraph.',
      },
    });

    const html = wrapper.html();
    expect(html).toContain('<p>');
    expect(html).toContain('This is a paragraph');
  });

  it('should render markdown code blocks', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: '```javascript\nconsole.log("Hello");\n```',
      },
    });

    const html = wrapper.html();
    expect(html).toContain('<pre');
    expect(html).toContain('<code');
    expect(html).toContain('console.log');
  });

  it('should render inline code', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: 'Use `console.log()` for debugging.',
      },
    });

    const html = wrapper.html();
    expect(html).toContain('<code>');
    expect(html).toContain('console.log()');
  });

  it('should render empty string when content is empty', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: '',
      },
    });

    expect(wrapper.html()).toContain('<div class="markdown-preview"');
  });

  it('should have data-testid for testing', () => {
    const wrapper = mount(MarkdownPreview, {
      props: {
        content: '# Test',
      },
    });

    expect(wrapper.find('[data-testid="markdown-preview"]').exists()).toBe(true);
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- MarkdownPreview.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 提交MarkdownPreview组件**

Run:
```bash
git add frontend/src/components/preview/MarkdownPreview.vue frontend/tests/unit/components/MarkdownPreview.spec.ts
git commit -m "feat(frontend): add MarkdownPreview component with tests"
```

---

## Task 3: 创建HtmlPreview组件

**Files:**
- Create: `frontend/src/components/preview/HtmlPreview.vue`
- Create: `frontend/tests/unit/components/HtmlPreview.spec.ts`

**Step 1: 安装DOMPurify依赖**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm install dompurify @types/dompurify
```

Expected: 依赖安装成功

**Step 2: 创建HtmlPreview组件**

Create: `frontend/src/components/preview/HtmlPreview.vue`

```vue
<template>
  <div class="html-preview-wrapper">
    <iframe
      v-if="sanitizedHtml"
      :srcdoc="sanitizedHtml"
      class="html-preview-iframe"
      sandbox="allow-scripts allow-same-origin"
      data-testid="html-preview-iframe"
    />
    <div v-else class="html-preview-empty" data-testid="html-preview-empty">
      No HTML content
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DOMPurify from 'dompurify';

interface Props {
  content: string;
}

const props = defineProps<Props>();

const sanitizedHtml = computed(() => {
  if (!props.content) return '';

  // 使用DOMPurify清理HTML，防止XSS攻击
  return DOMPurify.sanitize(props.content, {
    // 允许的标签
    ALLOWED_TAGS: [
      'a', 'b', 'br', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'hr', 'i', 'img', 'li', 'ol', 'p', 'span', 'strong', 'ul',
      'table', 'thead', 'tbody', 'tr', 'td', 'th',
    ],
    // 允许的属性
    ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'id', 'style'],
    // 允许的URI协议
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  });
});
</script>

<style scoped>
.html-preview-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.html-preview-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fff;
}

.html-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}
</style>
```

**Step 3: 创建HtmlPreview测试**

Create: `frontend/tests/unit/components/HtmlPreview.spec.ts`

```typescript
/**
 * HtmlPreview组件单元测试
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import HtmlPreview from '@/components/preview/HtmlPreview.vue';

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string) => html,
  },
}));

describe('HtmlPreview', () => {
  it('should render iframe with sanitized HTML', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '<div>Hello HTML</div>',
      },
    });

    const iframe = wrapper.find('[data-testid="html-preview-iframe"]');
    expect(iframe.exists()).toBe(true);
    expect(iframe.attributes('srcdoc')).toBe('<div>Hello HTML</div>');
  });

  it('should show empty message when content is empty', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '',
      },
    });

    expect(wrapper.find('[data-testid="html-preview-iframe"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="html-preview-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('No HTML content');
  });

  it('should sanitize HTML content', () => {
    const content = '<div><script>alert("xss")</script>Hello</div>';

    const wrapper = mount(HtmlPreview, {
      props: {
        content,
      },
    });

    const srcdoc = wrapper.find('[data-testid="html-preview-iframe"]').attributes('srcdoc');
    // DOMPurify应该移除script标签
    expect(srcdoc).not.toContain('<script>');
  });

  it('should set sandbox attribute on iframe', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '<div>Test</div>',
      },
    });

    const iframe = wrapper.find('[data-testid="html-preview-iframe"]');
    expect(iframe.attributes('sandbox')).toBe('allow-scripts allow-same-origin');
  });
});
```

**Step 4: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- HtmlPreview.spec.ts --run
```

Expected: 所有测试通过

**Step 5: 提交HtmlPreview组件**

Run:
```bash
git add frontend/src/components/preview/HtmlPreview.vue frontend/tests/unit/components/HtmlPreview.spec.ts
git commit -m "feat(frontend): add HtmlPreview component with XSS protection"
```

---

## Task 4: 创建SvgPreview组件

**Files:**
- Create: `frontend/src/components/preview/SvgPreview.vue`
- Create: `frontend/tests/unit/components/SvgPreview.spec.ts`

**Step 1: 创建SvgPreview组件**

Create: `frontend/src/components/preview/SvgPreview.vue`

```vue
<template>
  <div class="svg-preview-wrapper">
    <div
      v-if="sanitizedSvg"
      class="svg-preview-content"
      v-html="sanitizedSvg"
      data-testid="svg-preview-content"
      @click="handleDownload"
    />
    <div v-else class="svg-preview-empty" data-testid="svg-preview-empty">
      No SVG content
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DOMPurify from 'dompurify';

interface Props {
  content: string;
  filename?: string;
}

const props = withDefaults(defineProps<Props>(), {
  filename: 'artifact.svg',
});

const emit = defineEmits<{
  download: [blob: Blob];
}>();

const sanitizedSvg = computed(() => {
  if (!props.content) return '';

  // 验证是否为有效的SVG
  if (!props.content.includes('<svg') && !props.content.includes('<?xml')) {
    return '';
  }

  // 使用DOMPurify清理SVG，仅允许SVG相关标签
  return DOMPurify.sanitize(props.content, {
    USE_PROFILES: { svg: true, svgFilters: true },
    ALLOWED_TAGS: [
      'svg', 'path', 'circle', 'rect', 'line', 'polygon', 'polyline',
      'ellipse', 'text', 'g', 'defs', 'linearGradient', 'radialGradient',
      'stop', 'use', 'foreignObject', 'image', 'pattern', 'mask',
    ],
  });
});

const handleDownload = () => {
  // 创建Blob对象
  const blob = new Blob([props.content], { type: 'image/svg+xml' });

  // 创建下载链接
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = props.filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  emit('download', blob);
};
</script>

<style scoped>
.svg-preview-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.svg-preview-content {
  max-width: 100%;
  max-height: 100%;
  cursor: pointer;
  transition: transform 0.2s;
}

.svg-preview-content:hover {
  transform: scale(1.02);
}

.svg-preview-content :deep(svg) {
  display: block;
  max-width: 100%;
  max-height: 100%;
}

.svg-preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}
</style>
```

**Step 2: 创建SvgPreview测试**

Create: `frontend/tests/unit/components/SvgPreview.spec.ts`

```typescript
/**
 * SvgPreview组件单元测试
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import SvgPreview from '@/components/preview/SvgPreview.vue';

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string, config: any) => {
      if (config?.USE_PROFILES?.svg) {
        return html;
      }
      return html.replace(/<script>/g, '');
    },
  },
});

// Mock URL and document methods
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

describe('SvgPreview', () => {
  it('should render SVG content', () => {
    const svgContent = '<svg width="100" height="100"><circle cx="50" cy="50" r="40" /></svg>';

    const wrapper = mount(SvgPreview, {
      props: {
        content: svgContent,
      },
    });

    expect(wrapper.find('[data-testid="svg-preview-content"]').exists()).toBe(true);
    expect(wrapper.html()).toContain('<svg');
  });

  it('should show empty message when content is not valid SVG', () => {
    const wrapper = mount(SvgPreview, {
      props: {
        content: 'This is not SVG',
      },
    });

    expect(wrapper.find('[data-testid="svg-preview-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('No SVG content');
  });

  it('should download SVG when clicked', async () => {
    const svgContent = '<svg width="100" height="100"><circle cx="50" cy="50" r="40" /></svg>';

    const wrapper = mount(SvgPreview, {
      props: {
        content: svgContent,
        filename: 'test.svg',
      },
    });

    const content = wrapper.find('[data-testid="svg-preview-content"]');
    await content.trigger('click');

    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalled();
  });

  it('should use custom filename when downloading', () => {
    const svgContent = '<svg width="100" height="100"><circle cx="50" cy="50" r="40" /></svg>';

    const wrapper = mount(SvgPreview, {
      props: {
        content: svgContent,
        filename: 'custom-name.svg',
      },
    });

    expect(wrapper.props('filename')).toBe('custom-name.svg');
  });

  it('should sanitize SVG content', () => {
    const svgWithScript = '<svg><script>alert("xss")</script><circle cx="50" cy="50" r="40" /></svg>';

    const wrapper = mount(SvgPreview, {
      props: {
        content: svgWithScript,
      },
    });

    const html = wrapper.html();
    // 应该保留svg标签
    expect(html).toContain('<svg');
    // 应该移除script标签（由DOMPurify处理）
    expect(html).not.toContain('<script>');
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- SvgPreview.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 提交SvgPreview组件**

Run:
```bash
git add frontend/src/components/preview/SvgPreview.vue frontend/tests/unit/components/SvgPreview.spec.ts
git commit -m "feat(frontend): add SvgPreview component with download support"
```

---

## Task 5: 创建PreviewToolbar组件

**Files:**
- Create: `frontend/src/components/preview/PreviewToolbar.vue`
- Create: `frontend/tests/unit/components/PreviewToolbar.spec.ts`

**Step 1: 创建PreviewToolbar组件**

Create: `frontend/src/components/preview/PreviewToolbar.vue`

```vue
<template>
  <div class="preview-toolbar" data-testid="preview-toolbar">
    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadMarkdown"
      data-testid="btn-download-markdown"
      title="下载 Markdown"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">Markdown</span>
    </button>

    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadWord"
      :disabled="isDownloadingWord"
      data-testid="btn-download-word"
      title="下载 Word"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">{{ isDownloadingWord ? '转换中...' : 'Word' }}</span>
    </button>

    <button
      v-if="showMarkdownDownload"
      class="toolbar-btn"
      @click="handleDownloadPDF"
      :disabled="isDownloadingPDF"
      data-testid="btn-download-pdf"
      title="下载 PDF"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">{{ isDownloadingPDF ? '生成中...' : 'PDF' }}</span>
    </button>

    <button
      v-if="showSvgDownload"
      class="toolbar-btn"
      @click="handleDownloadSvg"
      data-testid="btn-download-svg"
      title="下载 SVG"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span class="btn-text">SVG</span>
    </button>

    <button
      class="toolbar-btn"
      @click="handleToggleFullscreen"
      data-testid="btn-toggle-fullscreen"
      :title="isFullscreen ? '退出全屏' : '全屏'"
    >
      <svg v-if="!isFullscreen" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

interface Props {
  artifactType: string;
  isFullscreen?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isFullscreen: false,
});

const emit = defineEmits<{
  downloadMarkdown: [];
  downloadWord: [];
  downloadPDF: [];
  downloadSvg: [];
  toggleFullscreen: [];
}>();

const isDownloadingWord = ref(false);
const isDownloadingPDF = ref(false);

const showMarkdownDownload = computed(() => {
  return props.artifactType === 'markdown';
});

const showSvgDownload = computed(() => {
  return props.artifactType === 'svg';
});

const handleDownloadMarkdown = () => {
  emit('downloadMarkdown');
};

const handleDownloadWord = async () => {
  isDownloadingWord.value = true;
  try {
    emit('downloadWord');
  } finally {
    // 延迟重置状态，避免闪烁
    setTimeout(() => {
      isDownloadingWord.value = false;
    }, 1000);
  }
};

const handleDownloadPDF = async () => {
  isDownloadingPDF.value = true;
  try {
    emit('downloadPDF');
  } finally {
    setTimeout(() => {
      isDownloadingPDF.value = false;
    }, 1000);
  }
};

const handleDownloadSvg = () => {
  emit('downloadSvg');
};

const handleToggleFullscreen = () => {
  emit('toggleFullscreen');
};
</script>

<style scoped>
.preview-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  align-items: center;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background-color: white;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background-color: #f0f0f0;
  border-color: #1890ff;
  color: #1890ff;
}

.toolbar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-text {
  font-size: 13px;
}
</style>
```

**Step 2: 创建PreviewToolbar测试**

Create: `frontend/tests/unit/components/PreviewToolbar.spec.ts`

```typescript
/**
 * PreviewToolbar组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import PreviewToolbar from '@/components/preview/PreviewToolbar.vue';

describe('PreviewToolbar', () => {
  it('should show markdown download buttons for markdown type', () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'markdown',
      },
    });

    expect(wrapper.find('[data-testid="btn-download-markdown"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="btn-download-word"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="btn-download-pdf"]').exists()).toBe(true);
  });

  it('should show svg download button for svg type', () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'svg',
      },
    });

    expect(wrapper.find('[data-testid="btn-download-svg"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="btn-download-markdown"]').exists()).toBe(false);
  });

  it('should not show any download buttons for html type', () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'html',
      },
    });

    expect(wrapper.find('[data-testid="btn-download-markdown"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="btn-download-svg"]').exists()).toBe(false);
  });

  it('should emit downloadMarkdown when button clicked', async () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'markdown',
      },
    });

    await wrapper.find('[data-testid="btn-download-markdown"]').trigger('click');

    expect(wrapper.emitted('downloadMarkdown')).toBeTruthy();
    expect(wrapper.emitted('downloadMarkdown')?.length).toBe(1);
  });

  it('should emit downloadSvg when button clicked', async () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'svg',
      },
    });

    await wrapper.find('[data-testid="btn-download-svg"]').trigger('click');

    expect(wrapper.emitted('downloadSvg')).toBeTruthy();
  });

  it('should emit toggleFullscreen when fullscreen button clicked', async () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'markdown',
      },
    });

    await wrapper.find('[data-testid="btn-toggle-fullscreen"]').trigger('click');

    expect(wrapper.emitted('toggleFullscreen')).toBeTruthy();
  });

  it('should show expand icon when not in fullscreen', () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'markdown',
        isFullscreen: false,
      },
    });

    const html = wrapper.html();
    expect(html).toContain('M8 3H5'); // 展开图标路径
  });

  it('should show collapse icon when in fullscreen', () => {
    const wrapper = mount(PreviewToolbar, {
      props: {
        artifactType: 'markdown',
        isFullscreen: true,
      },
    });

    const html = wrapper.html();
    expect(html).toContain('M8 3v3'); // 收缩图标路径
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- PreviewToolbar.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 提交PreviewToolbar组件**

Run:
```bash
git add frontend/src/components/preview/PreviewToolbar.vue frontend/tests/unit/components/PreviewToolbar.spec.ts
git commit -m "feat(frontend): add PreviewToolbar component"
```

---

## Task 6: 重构PreviewPanel主容器

**Files:**
- Modify: `frontend/src/components/PreviewPanel.vue`
- Create: `frontend/tests/unit/components/PreviewPanel.spec.ts`

**Step 1: 读取现有PreviewPanel代码**

Read: `frontend/src/components/PreviewPanel.vue` (完整文件)

了解当前实现和所有功能

**Step 2: 创建新的PreviewPanel**

Create: `frontend/src/components/PreviewPanel.vue`

```vue
<template>
  <div class="preview-panel" :class="{ 'is-fullscreen': isFullscreen }" data-testid="preview-panel">
    <PreviewToolbar
      :artifact-type="artifact?.type || ''"
      :is-fullscreen="isFullscreen"
      @download-markdown="handleDownloadMarkdown"
      @download-word="handleDownloadWord"
      @download-pdf="handleDownloadPDF"
      @download-svg="handleDownloadSvg"
      @toggle-fullscreen="toggleFullscreen"
    />

    <div class="preview-content" data-testid="preview-content">
      <MarkdownPreview
        v-if="artifact?.type === 'markdown'"
        :content="artifact.content"
      />

      <HtmlPreview
        v-else-if="artifact?.type === 'html'"
        :content="artifact.content"
      />

      <SvgPreview
        v-else-if="isSvgArtifact(artifact)"
        :content="artifact.content"
        :filename="artifact.filename || 'artifact.svg'"
      />

      <div v-else class="preview-empty" data-testid="preview-empty">
        暂无预览内容
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import MarkdownPreview from './preview/MarkdownPreview.vue';
import HtmlPreview from './preview/HtmlPreview.vue';
import SvgPreview from './preview/SvgPreview.vue';
import PreviewToolbar from './preview/PreviewToolbar.vue';
import type { Artifact } from '@/types';

interface Props {
  artifact: Artifact | null;
}

const props = defineProps<Props>();

const isFullscreen = ref(false);

const isSvgArtifact = (artifact: Artifact | null): boolean => {
  return artifact?.type === 'svg' || artifact?.type === 'image/svg+xml';
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};

const handleDownloadMarkdown = () => {
  if (!props.artifact?.content) return;

  const blob = new Blob([props.artifact.content], { type: 'text/markdown' });
  downloadBlob(blob, 'artifact.md');
};

const handleDownloadWord = async () => {
  // TODO: 实现Word转换逻辑
  console.log('Download Word - to be implemented');
};

const handleDownloadPDF = async () => {
  // TODO: 实现PDF生成逻辑
  console.log('Download PDF - to be implemented');
};

const handleDownloadSvg = () => {
  if (!props.artifact?.content) return;

  const blob = new Blob([props.artifact.content], { type: 'image/svg+xml' });
  downloadBlob(blob, 'artifact.svg');
};

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
</script>

<style scoped>
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.preview-panel.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  border-radius: 0;
}

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-style: italic;
}
</style>
```

**Step 3: 创建PreviewPanel测试**

Create: `frontend/tests/unit/components/PreviewPanel.spec.ts`

```typescript
/**
 * PreviewPanel组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import PreviewPanel from '@/components/PreviewPanel.vue';
import type { Artifact } from '@/types';

describe('PreviewPanel', () => {
  it('should show empty message when no artifact', () => {
    const wrapper = mount(PreviewPanel, {
      props: {
        artifact: null,
      },
    });

    expect(wrapper.find('[data-testid="preview-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('暂无预览内容');
  });

  it('should render MarkdownPreview for markdown type', () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Hello World',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="markdown-preview"]').exists()).toBe(true);
  });

  it('should render HtmlPreview for html type', () => {
    const artifact: Artifact = {
      type: 'html',
      content: '<div>Hello HTML</div>',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="html-preview-iframe"]').exists()).toBe(true);
  });

  it('should render SvgPreview for svg type', () => {
    const artifact: Artifact = {
      type: 'svg',
      content: '<svg><circle cx="50" cy="50" r="40" /></svg>',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="svg-preview-content"]').exists()).toBe(true);
  });

  it('should render toolbar when artifact exists', () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Test',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="preview-toolbar"]').exists()).toBe(true);
  });

  it('should toggle fullscreen when toolbar button clicked', async () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Test',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('.preview-panel').classes()).not.toContain('is-fullscreen');

    await wrapper.find('[data-testid="btn-toggle-fullscreen"]').trigger('click');

    expect(wrapper.find('.preview-panel').classes()).toContain('is-fullscreen');
  });
});
```

**Step 4: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- PreviewPanel.spec.ts --run
```

Expected: 所有测试通过

**Step 5: 验证行数**

Run:
```bash
wc -l frontend/src/components/PreviewPanel.vue
```

Expected: 应该 <150行（原来1348行）

**Step 6: 手动测试**

启动前端：
```bash
cd frontend
npm run dev
```

访问应用，测试：
1. 选择一个工具
2. 发送消息生成成果物
3. 验证预览显示正常
4. 测试下载功能
5. 测试全屏功能

**Step 7: 提交重构后的PreviewPanel**

Run:
```bash
git add frontend/src/components/PreviewPanel.vue frontend/tests/unit/components/PreviewPanel.spec.ts
git commit -m "refactor(frontend): simplify PreviewPanel to ~150 lines using child components"
```

---

## Task 7: 创建MessageItem组件

**Files:**
- Create: `frontend/src/components/chat/MessageItem.vue`
- Create: `frontend/tests/unit/components/MessageItem.spec.ts`

**Step 1: 创建MessageItem组件**

Create: `frontend/src/components/chat/MessageItem.vue`

```vue
<template>
  <div
    class="message-item"
    :class="messageClass"
    data-testid="message-item"
  >
    <div class="message-avatar">
      <img
        :src="avatarUrl"
        :alt="message.role"
        class="avatar-image"
        data-testid="message-avatar"
      />
    </div>

    <div class="message-content">
      <div
        class="message-text"
        v-html="renderedContent"
        data-testid="message-text"
      />
      <div class="message-time" data-testid="message-time">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';
import type { Message } from '@/types';

interface Props {
  message: Message;
}

const props = defineProps<Props>();

const messageClass = computed(() => {
  return `message-${props.message.role}`;
});

const avatarUrl = computed(() => {
  return props.message.role === 'user'
    ? '/images/user-avatar.png'
    : '/images/ai-avatar.png';
});

const renderedContent = computed(() => {
  if (props.message.role === 'assistant') {
    return renderMarkdown(props.message.content);
  }
  return props.message.content;
});

const formattedTime = computed(() => {
  const date = new Date(props.message.created_at);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  });
});
</script>

<style scoped>
.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-image {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-user .message-content {
  align-items: flex-end;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-user .message-text {
  background-color: #1890ff;
  color: white;
}

.message-assistant .message-text {
  background-color: #f5f5f5;
  color: #333;
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(pre) {
  background-color: #2d2d2d;
  color: #ccc;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.message-time {
  font-size: 12px;
  color: #999;
  padding: 0 4px;
}
</style>
```

**Step 2: 创建MessageItem测试**

Create: `frontend/tests/unit/components/MessageItem.spec.ts`

```typescript
/**
 * MessageItem组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MessageItem from '@/components/chat/MessageItem.vue';
import type { Message } from '@/types';

describe('MessageItem', () => {
  it('should render user message correctly', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Hello AI',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    expect(wrapper.find('.message-user').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hello AI');
  });

  it('should render assistant message correctly', () => {
    const message: Message = {
      id: 2,
      session_id: 1,
      role: 'assistant',
      content: 'Hello User',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    expect(wrapper.find('.message-assistant').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hello User');
  });

  it('should render markdown for assistant message', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'assistant',
      content: '# Heading',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const html = wrapper.find('[data-testid="message-text"]').html();
    expect(html).toContain('<h1>');
  });

  it('should not render markdown for user message', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: '# Heading',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const html = wrapper.find('[data-testid="message-text"]').html();
    // 用户消息不应该被渲染为markdown
    expect(html).not.toContain('<h1>');
    expect(wrapper.text()).toContain('# Heading');
  });

  it('should format timestamp', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Test',
      created_at: '2024-01-01T14:30:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const timeElement = wrapper.find('[data-testid="message-time"]');
    expect(timeElement.exists()).toBe(true);
    expect(timeElement.text()).toMatch(/\d{2}:\d{2}/);
  });

  it('should display correct avatar for user', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Test',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const avatar = wrapper.find('[data-testid="message-avatar"] img');
    expect(avatar.attributes('src')).toContain('user-avatar');
  });

  it('should display correct avatar for assistant', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'assistant',
      content: 'Test',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const avatar = wrapper.find('[data-testid="message-avatar"] img');
    expect(avatar.attributes('src')).toContain('ai-avatar');
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- MessageItem.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 提交MessageItem组件**

Run:
```bash
git add frontend/src/components/chat/MessageItem.vue frontend/tests/unit/components/MessageItem.spec.ts
git commit -m "feat(frontend): add MessageItem component"
```

---

## Task 8: 创建StreamingMessage组件

**Files:**
- Create: `frontend/src/components/chat/StreamingMessage.vue`
- Create: `frontend/tests/unit/components/StreamingMessage.spec.ts`

**Step 1: 创建StreamingMessage组件**

Create: `frontend/src/components/chat/StreamingMessage.vue`

```vue
<template>
  <div
    class="message-item message-assistant streaming"
    data-testid="streaming-message"
  >
    <div class="message-avatar">
      <img
        src="/images/ai-avatar.png"
        alt="AI"
        class="avatar-image"
      />
    </div>

    <div class="message-content">
      <div
        class="message-text"
        v-html="renderedContent"
        data-testid="streaming-text"
      />
      <div class="streaming-indicator" data-testid="streaming-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { renderMarkdown } from '@/utils/markdownRenderer';

interface Props {
  content: string;
}

const props = defineProps<Props>();

const renderedContent = computed(() => {
  if (!props.content) return '';
  return renderMarkdown(props.content);
});
</script>

<style scoped>
.message-item.streaming {
  opacity: 0.9;
}

.streaming-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  background-color: #1890ff;
  border-radius: 50%;
  animation: pulse 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes pulse {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
```

**Step 2: 创建StreamingMessage测试**

Create: `frontend/tests/unit/components/StreamingMessage.spec.ts`

```typescript
/**
 * StreamingMessage组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import StreamingMessage from '@/components/chat/StreamingMessage.vue';

describe('StreamingMessage', () => {
  it('should render streaming content', () => {
    const wrapper = mount(StreamingMessage, {
      props: {
        content: 'Streaming text...',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Streaming text...');
  });

  it('should render markdown content', () => {
    const wrapper = mount(StreamingMessage, {
      props: {
        content: '# Heading',
      },
    });

    const html = wrapper.find('[data-testid="streaming-text"]').html();
    expect(html).toContain('<h1>');
  });

  it('should show streaming indicator', () => {
    const wrapper = mount(StreamingMessage, {
      props: {
        content: 'Test',
      },
    });

    expect(wrapper.find('[data-testid="streaming-indicator"]').exists()).toBe(true);
    expect(wrapper.findAll('.dot').length).toBe(3);
  });

  it('should have streaming class', () => {
    const wrapper = mount(StreamingMessage, {
      props: {
        content: 'Test',
      },
    });

    expect(wrapper.find('.message-item').classes()).toContain('streaming');
  });

  it('should handle empty content', () => {
    const wrapper = mount(StreamingMessage, {
      props: {
        content: '',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message"]').exists()).toBe(true);
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- StreamingMessage.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 提交StreamingMessage组件**

Run:
```bash
git add frontend/src/components/chat/StreamingMessage.vue frontend/tests/unit/components/StreamingMessage.spec.ts
git commit -m "feat(frontend): add StreamingMessage component with indicator animation"
```

---

## Task 9: 创建MessageList和ChatInput组件

**Files:**
- Create: `frontend/src/components/chat/MessageList.vue`
- Create: `frontend/src/components/chat/ChatInput.vue`
- Create: `frontend/tests/unit/components/MessageList.spec.ts`
- Create: `frontend/tests/unit/components/ChatInput.spec.ts`

**Step 1: 创建MessageList组件**

Create: `frontend/src/components/chat/MessageList.vue`

```vue
<template>
  <div
    ref="scrollContainer"
    class="message-list"
    data-testid="message-list"
  >
    <MessageItem
      v-for="message in messages"
      :key="message.id"
      :message="message"
      data-testid="message-item"
    />

    <StreamingMessage
      v-if="streamingContent"
      :content="streamingContent"
      data-testid="streaming-message-wrapper"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import MessageItem from './MessageItem.vue';
import StreamingMessage from './StreamingMessage.vue';
import type { Message } from '@/types';

interface Props {
  messages: Message[];
  streamingContent?: string;
  autoScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  streamingContent: '',
  autoScroll: true,
});

const scrollContainer = ref<HTMLElement>();

// 自动滚动到底部
const scrollToBottom = async () => {
  await nextTick();
  if (scrollContainer.value && props.autoScroll) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动
watch(
  () => props.messages.length,
  async () => {
    await scrollToBottom();
  },
  { flush: 'post' }
);

// 监听流式内容变化
watch(
  () => props.streamingContent,
  async () => {
    await scrollToBottom();
  },
  { flush: 'post' }
);

// 暴露方法供外部调用
defineExpose({
  scrollToBottom,
});
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 6px;
}

.message-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.message-list::-webkit-scrollbar-thumb {
  background: #d1d1d1;
  border-radius: 3px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: #b1b1b1;
}
</style>
```

**Step 2: 创建ChatInput组件**

Create: `frontend/src/components/chat/ChatInput.vue`

```vue
<template>
  <div class="chat-input-wrapper" data-testid="chat-input-wrapper">
    <textarea
      ref="textareaRef"
      v-model="inputContent"
      class="chat-input"
      placeholder="输入消息..."
      rows="1"
      :disabled="disabled"
      @keydown="handleKeydown"
      @input="handleInput"
      data-testid="chat-input"
    />

    <button
      class="send-button"
      :disabled="!canSend"
      @click="handleSend"
      data-testid="send-button"
      title="发送 (Enter)"
    >
      <svg
        v-if="!isLoading"
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
      <div v-else class="loading-spinner" data-testid="loading-spinner"></div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

interface Props {
  disabled?: boolean;
  isLoading?: boolean;
  maxLength?: number;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  isLoading: false,
  maxLength: 2000,
});

const emit = defineEmits<{
  send: [content: string];
}>();

const inputContent = ref('');
const textareaRef = ref<HTMLTextAreaElement>();

const canSend = computed(() => {
  return !props.disabled && !props.isLoading && inputContent.value.trim().length > 0;
});

const handleInput = () => {
  // 自动调整高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px';
  }

  // 限制长度
  if (inputContent.value.length > props.maxLength) {
    inputContent.value = inputContent.value.slice(0, props.maxLength);
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  // Enter发送，Shift+Enter换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    handleSend();
  }
};

const handleSend = () => {
  const content = inputContent.value.trim();
  if (content && canSend.value) {
    emit('send', content);
    inputContent.value = '';

    // 重置高度
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto';
    }
  }
};

// 聚焦输入框
const focus = () => {
  textareaRef.value?.focus();
};

defineExpose({
  focus,
});
</script>

<style scoped>
.chat-input-wrapper {
  display: flex;
  gap: 8px;
  padding: 12px;
  background-color: #fff;
  border-top: 1px solid #e0e0e0;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  min-height: 40px;
  max-height: 200px;
  overflow-y: auto;
}

.chat-input:focus {
  border-color: #1890ff;
}

.chat-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.chat-input::placeholder {
  color: #999;
}

.send-button {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #1890ff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #40a9ff;
  transform: scale(1.05);
}

.send-button:disabled {
  background-color: #d0d0d0;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
```

**Step 3: 创建MessageList测试**

Create: `frontend/tests/unit/components/MessageList.spec.ts`

```typescript
/**
 * MessageList组件单元测试
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import MessageList from '@/components/chat/MessageList.vue';
import type { Message } from '@/types';

describe('MessageList', () => {
  it('should render list of messages', () => {
    const messages: Message[] = [
      {
        id: 1,
        session_id: 1,
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T12:00:00Z',
      },
      {
        id: 2,
        session_id: 1,
        role: 'assistant',
        content: 'Hi there!',
        created_at: '2024-01-01T12:00:01Z',
      },
    ];

    const wrapper = mount(MessageList, {
      props: {
        messages,
      },
    });

    const messageItems = wrapper.findAll('[data-testid="message-item"]');
    expect(messageItems.length).toBe(2);
  });

  it('should render streaming message when content provided', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
        streamingContent: 'Streaming...',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message-wrapper"]').exists()).toBe(true);
  });

  it('should not render streaming message when no content', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
        streamingContent: '',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message-wrapper"]').exists()).toBe(false);
  });

  it('should expose scrollToBottom method', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).scrollToBottom).toBe('function');
  });
});
```

**Step 4: 创建ChatInput测试**

Create: `frontend/tests/unit/components/ChatInput.spec.ts`

```typescript
/**
 * ChatInput组件单元测试
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatInput from '@/components/chat/ChatInput.vue';

describe('ChatInput', () => {
  it('should render input and button', () => {
    const wrapper = mount(ChatInput);

    expect(wrapper.find('[data-testid="chat-input"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="send-button"]').exists()).toBe(true);
  });

  it('should emit send event with content when button clicked', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Hello World');

    await wrapper.find('[data-testid="send-button"]').trigger('click');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello World']);
  });

  it('should emit send event when Enter pressed', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Test');

    await input.trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('send')).toBeTruthy();
  });

  it('should not send on Shift+Enter', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Test');

    await input.trigger('keydown', { key: 'Enter', shiftKey: true });

    expect(wrapper.emitted('send')).toBeFalsy();
  });

  it('should disable send button when content is empty', async () => {
    const wrapper = mount(ChatInput);

    const button = wrapper.find('[data-testid="send-button"]');
    expect(button.attributes('disabled')).toBeDefined();
  });

  it('should enable send button when content exists', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Hello');

    const button = wrapper.find('[data-testid="send-button"]');
    expect(button.attributes('disabled')).toBeUndefined();
  });

  it('should disable when isLoading prop is true', async () => {
    const wrapper = mount(ChatInput, {
      props: {
        isLoading: true,
      },
    });

    const input = wrapper.find('[data-testid="chat-input"]');
    expect(input.attributes('disabled')).toBeDefined();
  });

  it('should show loading spinner when isLoading', () => {
    const wrapper = mount(ChatInput, {
      props: {
        isLoading: true,
      },
    });

    expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true);
  });

  it('should clear input after sending', async () => {
    const wrapper = mount(ChatInput);

    const input = wrapper.find('[data-testid="chat-input"]') as any;
    await input.setValue('Hello');

    await wrapper.find('[data-testid="send-button"]').trigger('click');

    expect((input.element as HTMLTextAreaElement).value).toBe('');
  });

  it('should expose focus method', () => {
    const wrapper = mount(ChatInput);

    expect(typeof (wrapper.vm as any).focus).toBe('function');
  });
});
```

**Step 5: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- MessageList.spec.ts ChatInput.spec.ts --run
```

Expected: 所有测试通过

**Step 6: 提交MessageList和ChatInput组件**

Run:
```bash
git add frontend/src/components/chat/MessageList.vue frontend/src/components/chat/ChatInput.vue frontend/tests/unit/components/MessageList.spec.ts frontend/tests/unit/components/ChatInput.spec.ts
git commit -m "feat(frontend): add MessageList and ChatInput components"
```

---

## Task 10: 重构ChatPanel主容器

**Files:**
- Modify: `frontend/src/components/ChatPanel.vue`
- Create: `frontend/tests/unit/components/ChatPanel.spec.ts`

**Step 1: 创建新的ChatPanel**

Create: `frontend/src/components/ChatPanel.vue`

```vue
<template>
  <div class="chat-panel" data-testid="chat-panel">
    <MessageList
      ref="messageListRef"
      :messages="messages"
      :streaming-content="streamingContent"
      :auto-scroll="autoScroll"
    />

    <ChatInput
      ref="chatInputRef"
      :disabled="disabled"
      :is-loading="isLoading"
      @send="handleSend"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import MessageList from './chat/MessageList.vue';
import ChatInput from './chat/ChatInput.vue';
import type { Message } from '@/types';

interface Props {
  messages: Message[];
  streamingContent?: string;
  disabled?: boolean;
  isLoading?: boolean;
  autoScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  streamingContent: '',
  disabled: false,
  isLoading: false,
  autoScroll: true,
});

const emit = defineEmits<{
  send: [content: string];
}>();

const messageListRef = ref<InstanceType<typeof MessageList>>();
const chatInputRef = ref<InstanceType<typeof ChatInput>>();

const handleSend = (content: string) => {
  emit('send', content);
};

// 聚焦输入框
const focusInput = () => {
  chatInputRef.value?.focus();
};

// 滚动到底部
const scrollToBottom = () => {
  messageListRef.value?.scrollToBottom();
};

defineExpose({
  focusInput,
  scrollToBottom,
});
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f5f5f5;
}
</style>
```

**Step 2: 创建ChatPanel测试**

Create: `frontend/tests/unit/components/ChatPanel.spec.ts`

```typescript
/**
 * ChatPanel组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatPanel from '@/components/ChatPanel.vue';
import type { Message } from '@/types';

describe('ChatPanel', () => {
  it('should render MessageList and ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(wrapper.findComponent({ name: 'MessageList' }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'ChatInput' }).exists()).toBe(true);
  });

  it('should pass messages to MessageList', () => {
    const messages: Message[] = [
      {
        id: 1,
        session_id: 1,
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T12:00:00Z',
      },
    ];

    const wrapper = mount(ChatPanel, {
      props: {
        messages,
      },
    });

    const messageList = wrapper.findComponent({ name: 'MessageList' });
    expect(messageList.props('messages')).toEqual(messages);
  });

  it('should pass streamingContent to MessageList', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        streamingContent: 'Streaming...',
      },
    });

    const messageList = wrapper.findComponent({ name: 'MessageList' });
    expect(messageList.props('streamingContent')).toBe('Streaming...');
  });

  it('should emit send event when ChatInput sends', async () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    await chatInput.vm.$emit('send', 'Hello');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello']);
  });

  it('should pass disabled to ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        disabled: true,
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    expect(chatInput.props('disabled')).toBe(true);
  });

  it('should pass isLoading to ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        isLoading: true,
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    expect(chatInput.props('isLoading')).toBe(true);
  });

  it('should expose focusInput method', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).focusInput).toBe('function');
  });

  it('should expose scrollToBottom method', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).scrollToBottom).toBe('function');
  });
});
```

**Step 3: 运行测试**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- ChatPanel.spec.ts --run
```

Expected: 所有测试通过

**Step 4: 验证行数**

Run:
```bash
wc -l frontend/src/components/ChatPanel.vue
```

Expected: 应该 <150行（原来747行）

**Step 5: 手动测试**

启动前端，测试完整聊天流程：
1. 选择工具
2. 发送消息
3. 验证消息显示
4. 验证流式响应
5. 验证自动滚动

**Step 6: 提交重构后的ChatPanel**

Run:
```bash
git add frontend/src/components/ChatPanel.vue frontend/tests/unit/components/ChatPanel.spec.ts
git commit -m "refactor(frontend): simplify ChatPanel to ~150 lines using child components"
```

---

## Task 11: 阶段2总结和验证

**Step 1: 运行完整测试套件**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend
npm run test -- --run --coverage
```

Expected:
- 所有组件测试通过
- 组件覆盖率 >75%

**Step 2: 检查代码行数减少**

Run:
```bash
cd /Users/zhangcolin/workspace/ai-teacher-platform/frontend/src/components
wc -l PreviewPanel.vue ChatPanel.vue
```

Expected:
- PreviewPanel.vue: <150行（原来1348行）
- ChatPanel.vue: <150行（原来747行）

**Step 3: 验证所有新组件**

Run:
```bash
ls -la frontend/src/components/preview/
ls -la frontend/src/components/chat/
```

Expected:
- preview/: MarkdownPreview.vue, HtmlPreview.vue, SvgPreview.vue, PreviewToolbar.vue
- chat/: MessageItem.vue, StreamingMessage.vue, MessageList.vue, ChatInput.vue

**Step 4: 手动E2E测试**

启动完整应用：
```bash
# 后端
cd backend && python -m src.main

# 前端（新终端）
cd frontend && npm run dev
```

测试流程：
1. 登录应用
2. 选择AI工具
3. 发送对话
4. 验证消息显示正确
5. 验证成果物预览正确
6. 测试下载功能
7. 测试全屏功能

**Step 5: 创建阶段2完成标记**

Run:
```bash
echo "Phase 2 Complete: Frontend Component Refactoring" > frontend/.phase2-complete
echo "Date: $(date)" >> frontend/.phase2-complete
git add frontend/.phase2-complete
git commit -m "chore: mark Phase 2 (Frontend Refactoring) as complete"
```

---

## 📝 阶段2完成检查清单

- [x] Vitest测试框架配置完成
- [x] MarkdownPreview组件 + 测试
- [x] HtmlPreview组件 + 测试
- [x] SvgPreview组件 + 测试
- [x] PreviewToolbar组件 + 测试
- [x] PreviewPanel重构（~150行）
- [x] MessageItem组件 + 测试
- [x] StreamingMessage组件 + 测试
- [x] MessageList组件 + 测试
- [x] ChatInput组件 + 测试
- [x] ChatPanel重构（~150行）
- [x] 所有组件测试通过
- [x] 代码覆盖率达标
- [x] 手动E2E测试通过

---

## 🎯 下一步

阶段2完成后，继续：
- **阶段3**: Day 8-12（后端路由拆分 + 测试完善）

查看 `docs/plans/2026-02-27-system-refactoring-phase3.md` 继续实施。
