# 浏览器端代码执行沙箱 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在聊天消息中，对 `python` / `javascript`（及可选 `js`）代码块显示「运行」按钮，点击后在右侧 `PreviewPanel` 中通过同源 iframe 沙箱执行代码并展示 stdout/stderr/图形输出。

**Architecture:** 与现有 HTML 预览一致：复用 `codeblock-preview` 事件与 `PreviewPanel` 分发；新增 `CodeRunnerPreview.vue` 作为宿主，内嵌 `public/sandboxes/*.html`；父页面与 iframe 通过 `postMessage` 通信，且**双方均校验 `event.origin === window.location.origin`**。

**Tech Stack:** Vue 3、Vite、`public/` 静态 HTML、Pyodide（CDN jsdelivr）、Vitest + @vue/test-utils。

**Spec 依据:** `docs/superpowers/specs/2026-04-05-code-sandbox-design.md`

**审查说明:** 计划审查不派子代理；实施前自检清单见文末。

---

## 文件结构（创建 / 修改）

| 路径 | 职责 |
|------|------|
| `frontend/public/sandboxes/python-sandbox.html` | 加载 Pyodide，执行 Python，回传 stdout/stderr/状态/可选图片 |
| `frontend/public/sandboxes/js-sandbox.html` | 执行 JS（`new Function`），劫持 console，回传输出 |
| `frontend/src/components/preview/CodeRunnerPreview.vue` | iframe 宿主、消息桥、输出 UI、重新运行 |
| `frontend/src/components/PreviewPanel.vue` | `python` / `javascript` 分支挂载 `CodeRunnerPreview` |
| `frontend/src/utils/markdownRenderer.ts` | 可运行语言集合、按钮文案「运行」+ 播放图标 |
| `frontend/src/utils/codeBlockHandlers.ts` | 仅当需区分 data 属性时可微调（默认可不改） |
| `frontend/src/utils/__tests__/markdownRenderer.codeRunner.spec.ts`（新建） | 断言「运行」按钮与 artifact type |
| `frontend/src/components/preview/__tests__/CodeRunnerPreview.spec.ts`（新建，可选） | 冒烟：挂载 + mock postMessage |

---

### Task 1: 静态页面 `js-sandbox.html`

**Files:**
- Create: `frontend/public/sandboxes/js-sandbox.html`

- [ ] **Step 1: 实现最小沙箱页**

内联脚本（无外部依赖）完成：

1. 定义 `EXPECTED_ORIGIN = window.location.origin`。
2. `window.addEventListener('message', ...)`：若 `event.origin !== EXPECTED_ORIGIN` 或 `event.data?.type !== 'execute'` 则忽略。
3. `execute` 时：向父窗口发 `{ type: 'status', status: 'running' }`；用 `try/catch` 包裹执行逻辑。
4. 执行前保存 `console.log/warn/error`，替换为把内容 `postMessage` 到父窗口（`stdout` / `stderr`）；执行后恢复。
5. 使用 `new Function(code)()` 执行用户代码（不要用裸 `eval` 字符串形式）。
6. 结束发 `{ type: 'status', status: 'done' }`；异常发 `stderr` + `{ type: 'status', status: 'error' }`。
7. 页面 `load` 后发 `{ type: 'status', status: 'ready' }`（父组件收到后再发 `execute`）。

- [ ] **Step 2: 手动验证**

`npm run dev` 后浏览器打开 `http://localhost:5173/sandboxes/js-sandbox.html`，在控制台模拟：

```js
window.postMessage({ type: 'execute', code: 'console.log(1+1)' }, window.location.origin)
```

预期：父窗口若监听应收到 `stdout` 含 `2`。可在临时 HTML 中测。

- [ ] **Step 3: Commit**

```bash
git add frontend/public/sandboxes/js-sandbox.html
git commit -m "feat(frontend): 添加 JS 浏览器沙箱页面"
```

---

### Task 2: 静态页面 `python-sandbox.html`

**Files:**
- Create: `frontend/public/sandboxes/python-sandbox.html`

- [ ] **Step 1: 引入 Pyodide**

使用官方 CDN，例如：

```html
<script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>
```

（版本号可在实施时改为当前稳定版；计划里固定一个版本便于复现。）

- [ ] **Step 2: 初始化与 `execute`**

1. 同样校验 `event.origin`。
2. `loadPyodide()` 完成后发 `status: 'ready'`。
3. 收到 `execute`：发 `status: 'running'`，用 `pyodide.runPythonAsync(code)`。
4. 使用 Pyodide 的 stdout/stderr 重定向 API（如 `pyodide.setStdout` / `setStderr` 或文档推荐方式）将输出流式或分批 `postMessage` 为 `stdout`/`stderr`。
5. 成功：`status: 'done'`；失败：`stderr` + `status: 'error'`。

- [ ] **Step 3: Matplotlib（与设计一致）**

在首次需要时 `await pyodide.loadPackage('matplotlib')`，并配置非交互 backend（按 Pyodide 文档设置 `matplotlib` 的 wasm 后端），使 `plt.savefig` 或 `buffer_rgba` 能产出 PNG base64，通过 `{ type: 'image', data, mimeType: 'image/png' }` 发给父窗口。若单步过大，可先合并 Task 2 Step 2 再追加 Step 3 提交。

- [ ] **Step 4: Commit**

```bash
git add frontend/public/sandboxes/python-sandbox.html
git commit -m "feat(frontend): 添加 Python Pyodide 沙箱页面"
```

---

### Task 3: `CodeRunnerPreview.vue`

**Files:**
- Create: `frontend/src/components/preview/CodeRunnerPreview.vue`

- [ ] **Step 1: Props 与 iframe**

```ts
interface Props {
  content: string
  language: 'python' | 'javascript'  // 由父组件规范化后传入
}
```

- 根据 `language` 设置 `iframe.src`：`/sandboxes/python-sandbox.html` 或 `/sandboxes/js-sandbox.html`。
- `iframe` 使用 `sandbox="allow-scripts allow-same-origin"`（与 `HtmlPreview` 对齐需求；不需要表单可不加 `allow-forms`）。
- `iframe` 设 `class` 填满父容器（参考 `HtmlPreview` 样式）。

- [ ] **Step 2: 消息桥**

- `onMounted`：`window.addEventListener('message', handler)`，`handler` 内若 `event.origin !== window.location.origin` 则 return。
- 仅处理来自**当前子 iframe 的 `contentWindow`** 的消息（比较 `event.source === iframeRef.value?.contentWindow`）。
- 收到 `status: ready` 后，对当前 `props.content` 调用 `postMessage({ type: 'execute', code: props.content, language }, origin)`。
- `watch`：`content` 或 `language` 变化时重置输出状态；若 iframe 已 `ready` 可立即再发 `execute`（或 `key` 强制重建 iframe，简单但重复加载 Pyodide —— **优先复用 iframe**，仅在语言切换时重建）。

- [ ] **Step 3: UI**

- 顶部：语言标签 +「重新运行」按钮（清空输出缓冲区，再发 `execute`）。
- 主体：终端风格输出区；`stderr` 红色；`image` 用 `<img :src="'data:' + mime + ';base64,' + data" />`。
- `loading`：Python 在首次 `ready` 前显示「正在加载 Python 环境…」；`running` 显示简短提示。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/preview/CodeRunnerPreview.vue
git commit -m "feat(frontend): 代码运行预览组件 CodeRunnerPreview"
```

---

### Task 4: `PreviewPanel.vue` 接入

**Files:**
- Modify: `frontend/src/components/PreviewPanel.vue`

- [ ] **Step 1: 增加分支**

在 `SvgPreview` 之后、`preview-empty` 之前：

```vue
<CodeRunnerPreview
  v-else-if="artifact && isRunnableCodeArtifact(artifact)"
  :content="artifact.content"
  :language="normalizeRunnableLanguage(artifact)"
/>
```

- 在同文件 `<script>` 中实现：

```ts
function isRunnableCodeArtifact(a: Artifact): boolean {
  const t = (a.type || '').toLowerCase()
  return t === 'python' || t === 'javascript' || t === 'js'
}

function normalizeRunnableLanguage(a: Artifact): 'python' | 'javascript' {
  const t = (a.type || '').toLowerCase()
  if (t === 'python') return 'python'
  return 'javascript' // js、javascript、ts 等首版统一走 JS 沙箱（TS 不编译，文档可说明）
}
```

- 按需 `import CodeRunnerPreview from './preview/CodeRunnerPreview.vue'`（路径与项目一致）。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PreviewPanel.vue
git commit -m "feat(frontend): PreviewPanel 支持 Python/JS 代码运行"
```

---

### Task 5: `markdownRenderer.ts` —「运行」按钮

**Files:**
- Modify: `frontend/src/utils/markdownRenderer.ts`

- [ ] **Step 1: 定义集合与规范化**

```ts
const RUNNABLE_LANGUAGES = new Set(['python', 'javascript', 'js'])

function normalizeArtifactTypeForRunner(lang: string): string {
  if (lang === 'js') return 'javascript'
  return lang
}
```

在构造 `artifact` 时：若 `RUNNABLE_LANGUAGES.has(lang)`，则 `artifact.type = normalizeArtifactTypeForRunner(lang)`（保证 `PreviewPanel` 收到 `javascript` 而非 `js`）。

- [ ] **Step 2: 条件渲染按钮**

- 若可运行：`title="运行代码"`，按钮文案可用 `aria-label` + 内联 SVG 播放图标（与现有眼睛图标二选一）。
- 若不可运行：保持现有「预览」与眼睛图标。
- `class` 仍可沿用 `preview-button` 以免破坏 `codeBlockHandlers.ts`（其按 class 选择器点击）。

- [ ] **Step 3: 单元测试**

新建 `frontend/src/utils/__tests__/markdownRenderer.codeRunner.spec.ts`：

```ts
import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '../markdownRenderer'

it('python 代码块含运行按钮语义', () => {
  const html = renderMarkdown('```python\nprint(1)\n```')
  expect(html).toMatch(/运行|run/i)
  expect(html).toContain('data-artifact-content')
})

it('html 代码块仍为预览', () => {
  const html = renderMarkdown('```html\n<div></div>\n```')
  expect(html).toMatch(/预览/)
})
```

按实际生成的 `title` 调整断言。

运行：

```bash
cd frontend && npm run test -- --run src/utils/__tests__/markdownRenderer.codeRunner.spec.ts
```

预期：全部 PASS。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/markdownRenderer.ts frontend/src/utils/__tests__/markdownRenderer.codeRunner.spec.ts
git commit -m "feat(frontend): 可运行语言代码块显示运行按钮并规范化类型"
```

---

### Task 6: E2E（可选但推荐）

**Files:**
- Modify: `frontend/tests/e2e/...`（若已有 chat 相关 spec，扩展一条）

- [ ] **Step 1:** 在 E2E 中注入含 ` ```python\nprint('ok')\n``` ` 的助手消息（或通过 mock API），点击「运行」，断言预览区出现 `ok`。

若 E2E 成本过高，可仅保留 Task 5 单元测试，并在 PR 说明中写明「手动回归步骤」。

---

### Task 7: 全量测试与收尾

- [ ] **Step 1**

```bash
cd frontend && npm run test -- --run
cd frontend && npm run build
```

预期：测试通过，构建无类型错误。

- [ ] **Step 2: Commit（若有仅文档小改）**

---

## 实施前自检（替代子代理审查）

- [ ] `postMessage` 双向校验 `origin`。
- [ ] `typescript` / `js` 与 `javascript` 的映射在 `markdownRenderer` 与 `PreviewPanel` 一致。
- [ ] Pyodide CDN 版本锁定；内网/离线环境是否在 README 中说明限制。
- [ ] `PreviewToolbar` 对 `python`/`javascript` 仅显示全屏与关闭（当前逻辑已满足，无需改）。

---

## 执行方式（完成后由人类选择）

计划保存路径：`docs/superpowers/plans/2026-04-05-code-sandbox-implementation.md`

1. **Subagent-Driven（推荐）** — 每任务独立子代理 + 任务间 review。  
2. **Inline Execution** — 本会话按任务顺序实现，检查点合并提交。

请选择 1 或 2 后开始写代码阶段。
