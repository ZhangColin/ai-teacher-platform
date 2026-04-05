# 浏览器端代码执行沙箱设计

## 概述

在现有 HTML 预览功能的基础上，扩展支持 Python 和 JavaScript 代码的浏览器端执行。用户在与 AI 对话时，AI 生成的代码块（Python/JavaScript）旁会出现"运行"按钮，点击后在右侧面板的 iframe 沙箱中执行代码并展示结果。

## 背景

当前系统已支持 AI 生成 HTML 代码并在 iframe 沙箱中预览。整个流程是：

1. AI 回复中包含 ` ```html ` 代码块
2. `markdownRenderer.ts` 解析代码块，生成带"预览"按钮的 UI
3. 用户点击"预览"，`codeBlockHandlers.ts` 派发 `codeblock-preview` 自定义事件
4. `ChatArea.vue` 监听事件，打开右侧 `PreviewPanel.vue`
5. `PreviewPanel` 根据 `artifact.type === 'html'` 选择 `HtmlPreview.vue`
6. `HtmlPreview` 通过 Blob URL 在 iframe 中渲染 HTML

本设计在此基础上扩展，让 Python 和 JavaScript 代码也能通过相同的交互模式执行。

## 设计约束

- **纯浏览器端执行**：不需要后端参与代码执行，零服务器成本
- **iframe 沙箱隔离**：代码在独立 iframe 中运行，不影响主应用
- **与现有交互一致**：复用已有的事件派发和 PreviewPanel 分发机制
- **仅支持单文件代码**：AI 在对话中生成的代码为单文件，不涉及项目结构
- **用户不编辑代码**：迭代通过对话进行，代码块本身只读

## 支持语言

| 语言 | 运行时技术 | 说明 |
|------|-----------|------|
| Python | Pyodide（CPython → WebAssembly） | 支持 numpy/pandas/matplotlib 等常用库，首次加载 ~26MB，浏览器自动缓存 |
| JavaScript | 浏览器原生 | 零依赖，即时执行 |

## 整体数据流

```
AI 回复含 ```python 或 ```javascript 代码块
  → markdownRenderer 解析代码块，生成"运行"按钮
  → 用户点击"运行"
  → codeBlockHandlers 派发 codeblock-preview 事件（复用现有机制）
  → ChatArea 接收事件，打开右侧 PreviewPanel
  → PreviewPanel 根据 type=python/javascript 选择 CodeRunnerPreview（新组件）
  → CodeRunnerPreview 加载对应语言的 iframe 沙箱
  → iframe 内执行代码，通过 postMessage 返回结果
  → CodeRunnerPreview 在面板中展示输出（文本/错误/图形）
```

## 前端组件架构

### 新增组件

**`components/preview/CodeRunnerPreview.vue`**

核心新组件，职责：
- 根据语言选择对应的 iframe 沙箱页面
- 通过 `postMessage` 发送代码、接收执行结果
- 展示运行状态（加载中 / 运行中 / 完成 / 出错）
- 展示输出内容（stdout 文本、stderr 错误、图形图片）

### 新增静态资源

放在 `public/sandboxes/` 目录下，iframe 直接加载（不经过 Vite 打包）：

- **`public/sandboxes/python-sandbox.html`** — 加载 Pyodide，执行 Python 代码，捕获 stdout/stderr/图形
- **`public/sandboxes/js-sandbox.html`** — 原生 JS 执行环境，捕获 console 输出

### 现有组件改动

**`PreviewPanel.vue`**

新增 type 分支：

```
PreviewPanel.vue
  ├── MarkdownPreview.vue    (type=markdown，已有)
  ├── HtmlPreview.vue        (type=html，已有)
  ├── SvgPreview.vue         (type=svg，已有)
  └── CodeRunnerPreview.vue  (type=python/javascript，新增)
```

**`utils/markdownRenderer.ts`**

区分两类代码块的按钮：

- 渲染类（html, svg, markdown）：按钮文案"预览"，眼睛图标
- 执行类（python, javascript）：按钮文案"运行"，播放三角形 ▶ 图标

通过可执行语言集合判断：

```typescript
const RUNNABLE_LANGUAGES = new Set(['python', 'javascript'])
```

**`utils/codeBlockHandlers.ts`**

无需改动，现有事件派发机制直接复用。

## iframe 沙箱通信协议

### 主应用 → iframe

```typescript
{ type: 'execute', code: string, language: 'python' | 'javascript' }
```

### iframe → 主应用

```typescript
// 标准输出（可能多次，每次 print 一行）
{ type: 'stdout', data: string }

// 错误输出
{ type: 'stderr', data: string }

// 图形输出（matplotlib 等渲染成 base64 图片）
{ type: 'image', data: string, mimeType: 'image/png' }

// 执行状态
{ type: 'status', status: 'loading' | 'ready' | 'running' | 'done' | 'error' }
```

## Python 沙箱（python-sandbox.html）

- 页面加载时从 CDN 加载 Pyodide（`https://cdn.jsdelivr.net/pyodide/`）
- 加载完成后发送 `{ type: 'status', status: 'ready' }`
- 收到 `execute` 消息后：
  - 重定向 stdout/stderr，每次 print 实时发回 `stdout` 消息
  - 用 `pyodide.runPythonAsync()` 执行代码
  - 如果代码使用了 matplotlib，捕获图形输出转成 base64 图片发回
  - 执行完毕发送 `{ type: 'status', status: 'done' }`
  - 出错发送 `stderr` + `{ type: 'status', status: 'error' }`

### Pyodide 加载策略

- 首次加载 ~26MB（CDN 加速），加载期间显示进度提示
- 浏览器自动缓存 WASM 文件，二次打开秒加载
- iframe 在用户首次点"运行"时才创建，不预加载

## JavaScript 沙箱（js-sandbox.html）

- 无需加载运行时，页面就绪后直接发送 `{ type: 'status', status: 'ready' }`
- 收到 `execute` 消息后：
  - 覆盖 `console.log/warn/error`，拦截输出发回 `stdout`/`stderr`
  - 用 `new Function(code)()` 执行代码（比 eval 更隔离）
  - 执行完毕发送 `{ type: 'status', status: 'done' }`

## CodeRunnerPreview UI 设计

### 面板布局（从上到下）

1. **顶部工具栏**：语言标签（"Python" / "JavaScript"）+ "重新运行"按钮
2. **输出区域**：占据面板主体空间
   - 文本输出（stdout）：等宽字体，类终端样式，黑底白字
   - 错误输出（stderr）：红色文字，与 stdout 混合显示（按时序）
   - 图形输出（matplotlib 图片等）：内联显示在文本流中

### 状态展示

| 状态 | UI 表现 |
|------|---------|
| `loading` | "正在加载 Python 环境..." + 加载动画（仅 Python 首次） |
| `ready` | 自动开始执行，无需用户操作 |
| `running` | "运行中..." + 旋转指示器 |
| `done` | 输出区显示完整结果 |
| `error` | 输出区显示错误信息，红色高亮 |

### 交互细节

- 点击代码块"运行"按钮 → 右侧面板打开 → 自动执行（无需再点一次）
- 点击另一个代码块的"运行" → 面板切换到新代码的执行结果
- "重新运行"按钮 → 清空输出，重新执行（Python 复用已加载的 Pyodide）
- stdout 实时滚动到底部

## 后端改动

**无需改动。**

- `artifact_parser.py` 已能识别 ` ```python ` 和 ` ```javascript ` 代码块
- 代码执行完全在浏览器端完成
- 数据库 Artifact 模型已有 `type` 和 `language` 字段，天然支持

## 改动范围总结

| 层 | 文件 | 改动 |
|----|------|------|
| 前端新增 | `components/preview/CodeRunnerPreview.vue` | 新组件：代码执行面板 |
| 前端新增 | `public/sandboxes/python-sandbox.html` | Python 沙箱页面 |
| 前端新增 | `public/sandboxes/js-sandbox.html` | JavaScript 沙箱页面 |
| 前端改动 | `components/PreviewPanel.vue` | 新增 type 分支到 CodeRunnerPreview |
| 前端改动 | `utils/markdownRenderer.ts` | 按钮文案/图标区分"预览"vs"运行" |
| 后端 | 无 | — |

## 未来扩展方向

- **更多语言**：通过 Runno（WASI）可添加 Ruby、PHP、C/C++、SQLite 等
- **后端沙箱**：Docker 容器执行，支持更复杂的代码和更多库
- **代码编辑**：让用户在预览面板中修改代码并重新运行
