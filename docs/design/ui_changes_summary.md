# UI框架变更总结

> **文档定位**: 记录UI框架实现过程中的重要变更  
> **创建日期**: 2026-01-02  
> **更新日期**: 2026-01-02

---

## 📋 变更列表

### 1. 术语变更：菜单 → 工具选择器

**变更内容**：
- 组件名称：`SidebarMenu` → `AIToolSelector`
- 概念描述：从"菜单"改为"工具选择器"
- 设计理念：从"导航菜单"改为"工具选择区域"

**影响文档**：
- `docs/requirements/ui_framework_spec.md`
- `docs/design/frontend_architecture.md`

**变更原因**：
- 更准确地反映该区域的本质功能（选择AI工具，而非导航菜单）
- 用户反馈"菜单显得弱了点"，需要更突出的设计

---

### 2. 工具组织结构变更

**变更前**：
- 一级菜单/二级菜单的层级结构
- 文生文、文生图、文生视频作为独立的一级菜单

**变更后**：
- 分类+工具卡片的结构
- 所有工具按分类组织：
  - **内容生成**分类：文生文、文生图、文生视频
  - **智能体**分类：提示词向导、Lyar等

**设计变更**：
- 从菜单式设计改为分类+卡片式设计
- 每个工具以卡片形式展示（带图标）
- 分类标题：图标 + 名称（仅展示，不可点击）
- 工具卡片：图标 + 名称（可点击切换）

**影响文档**：
- `docs/requirements/ui_framework_spec.md` - 4.2 左侧工具选择器
- `docs/design/frontend_architecture.md` - 3.2.2 AI工具模块组件

---

### 3. Logo和平台名称

**变更内容**：
- Logo：从文本Logo改为真实Logo图片文件（`logo.png`）
- 平台名称：从"AI Platform"改为"海创元AI教育平台"
- Logo显示：Logo图片 + 平台名称并排显示

**文件位置**：
- Logo文件：`frontend/src/assets/logo/logo.png`
- Logo组件：`frontend/src/components/Logo.vue`

**影响文档**：
- `docs/requirements/ui_framework_spec.md` - 3.1 布局结构

---

### 4. 侧边栏宽度

**变更内容**：
- 桌面端宽度：260px（保持不变）
- 之前曾尝试增加到300px，后恢复为260px

**原因**：
- 用户反馈260px宽度更合适
- 卡片式设计在260px宽度下也能正常显示

---

## 📝 需要同步更新的文档

### 已更新
- ✅ `docs/requirements/ui_framework_spec.md`
  - 4.2 左侧工具选择器（术语和结构描述）
  - 3.1 布局结构（Logo和平台名称）
  - 验收标准（术语更新）

- ✅ `docs/design/frontend_architecture.md`
  - 3.2.2 AI工具模块组件（组件名称和职责）
  - 4.2 UI框架Store设计（数据结构变更）
  - 8.1 模块配置数据契约（接口定义）

### 待检查
- ⚠️ 其他可能引用"菜单"或"SidebarMenu"的文档
- ⚠️ 代码注释中的术语（如需要）

---

## 🎯 设计理念变化

### 变更前
- **概念**：左侧功能导航菜单
- **设计**：菜单项列表，层级结构
- **交互**：菜单项点击切换

### 变更后
- **概念**：AI工具选择器
- **设计**：分类+卡片式，更突出工具选择
- **交互**：工具卡片点击切换，视觉反馈更明显

---

---

### 5. 工具选择器标题移除

**变更内容**：
- 移除了工具选择器顶部的"AI工具"标题和"选择你想要使用的工具"副标题
- 工具列表直接显示，更简洁

**变更原因**：
- 顶部导航栏已显示"AI工具"模块，避免信息重复
- 用户反馈标题区域占用空间，去掉后更简洁
- 分类名称（"内容生成"、"智能体"）已能说明内容

**影响范围**：
- `frontend/src/components/AIToolSelector.vue` - 移除标题区域
- 布局更紧凑，工具列表更靠上

---

### 6. 收起按钮位置优化

**变更内容**：
- 收起/展开按钮从 `AIToolSelector` 组件移到 `AIToolsLayout` 布局组件
- 按钮始终显示，不受 sidebar 的 `overflow` 限制

**技术实现**：
- 按钮使用 `absolute` 定位，相对于 `AIToolsLayout` 容器
- 展开时：按钮在 sidebar 右侧边缘（`left: 244px`）
- 收起时：按钮在左侧边缘（`left: 8px`）
- 状态通过 props 从父组件传递到子组件

**变更原因**：
- 修复收起后按钮被隐藏的问题
- 确保按钮始终可见，提升用户体验

**影响文件**：
- `frontend/src/components/AIToolSelector.vue` - 移除按钮代码
- `frontend/src/layouts/AIToolsLayout.vue` - 添加按钮代码

---

### 7. 布局高度优化

**变更内容**：
- 修复布局高度问题，确保占满整个视口高度
- 建立完整的高度链：`html` → `body` → `#app` → `.app-container` → `MainLayout`

**技术实现**：
- `html, body, #app` → `height: 100%`
- `.app-container` → `height: 100%` + `display: flex` + `flex-direction: column` + `overflow: hidden`
- `.main-layout` → `height: 100%`
- `.main-content` → `height: calc(100vh - 72px)`（减去 Header 高度）

**变更原因**：
- 修复界面下方留空的问题
- 确保布局适应整个屏幕高度

**影响文件**：
- `frontend/src/App.vue` - 更新全局样式
- `frontend/src/layouts/MainLayout.vue` - 更新布局高度

---

### 8. Favicon和页面标题

**变更内容**：
- Favicon：从默认的 `vite.svg` 改为海创元 logo（`favicon.png`）
- 页面标题：从"frontend"改为"海创元AI教育平台"
- 添加 `apple-touch-icon` 支持（iOS 设备）

**文件位置**：
- Favicon文件：`frontend/public/favicon.png`（从 `src/assets/logo/logo.png` 复制）

**影响文件**：
- `frontend/index.html` - 更新 favicon 引用和页面标题

---

## 📝 需要同步更新的文档

### 已更新
- ✅ `docs/requirements/ui_framework_spec.md`
  - 4.2 左侧工具选择器（术语和结构描述）
  - 3.1 布局结构（Logo和平台名称）
  - 验收标准（术语更新）

- ✅ `docs/design/frontend_architecture.md`
  - 3.2.2 AI工具模块组件（组件名称和职责）
  - 4.2 UI框架Store设计（数据结构变更）
  - 8.1 模块配置数据契约（接口定义）

### 待检查
- ⚠️ 其他可能引用"菜单"或"SidebarMenu"的文档
- ⚠️ 代码注释中的术语（如需要）

---

**文档维护者**: Development Team  
**最后更新**: 2026-01-02

