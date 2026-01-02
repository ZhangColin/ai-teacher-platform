# 品牌色和Logo提取指南

> **文档定位**: 指导如何从官网提取品牌色和Logo，并应用到设计系统中  
> **创建日期**: 2026-01-02  
> **参考网站**: https://www.aieducenter.com/

---

## 📋 待完成事项

### 1. 提取品牌主色

**目标**：从官网提取主色调，替换当前临时主色（`#3b82f6`）

**提取方法**：
1. **使用浏览器开发者工具**：
   - 访问 https://www.aieducenter.com/
   - 打开浏览器开发者工具（F12）
   - 使用颜色选择器工具，点击网站上的主要品牌色元素
   - 记录主色的十六进制值（如 `#1a73e8`）

2. **使用在线工具**：
   - [ColorExtractor](https://similarlabs.com/zh/p/color-extractor)
   - [ImageColorPicker](https://imagecolorpicker.com/)
   - 上传官网截图，自动提取主要颜色

3. **手动提取**：
   - 查看网站CSS文件中的颜色定义
   - 查看网站favicon或Logo的主要颜色

**提取后需要的信息**：
- 主色（Primary-500）：`#xxxxxx`
- 主色深色（Primary-600）：用于hover状态
- 主色浅色（Primary-50）：用于背景色

**应用步骤**：
1. 更新 `frontend/tailwind.config.js` 中的 `primary` 颜色配置
2. 更新 `docs/design/design_system.md` 中的品牌色定义
3. 验证所有使用主色的组件是否正确应用

---

### 2. 提取Logo文件

**目标**：从官网获取Logo文件（SVG或PNG），替换当前文本Logo

**提取方法**：
1. **直接下载**：
   - 访问 https://www.aieducenter.com/
   - 右键点击Logo，选择"另存为"
   - 优先选择SVG格式（矢量图，可缩放）

2. **从网站资源中提取**：
   - 打开浏览器开发者工具（F12）
   - 切换到"Network"标签
   - 刷新页面，筛选图片资源
   - 查找包含"logo"的文件，下载

3. **联系设计团队**：
   - 如果有设计团队，直接获取Logo源文件
   - 确保获取多种格式（SVG、PNG透明背景）

**Logo要求**：
- **格式**：优先SVG，其次PNG（透明背景）
- **尺寸**：SVG可缩放，PNG建议提供多种尺寸（@1x, @2x, @3x）
- **颜色**：提供深色和浅色版本（用于不同背景）

**应用步骤**：
1. 将Logo文件保存到 `frontend/src/assets/logo/` 目录
2. 更新 `frontend/src/components/Logo.vue` 组件
3. 添加响应式Logo显示（桌面端/移动端不同尺寸）
4. 更新 `docs/design/design_system.md` 中的Logo使用规范

---

## 📝 提取后的更新清单

### Tailwind配置更新
- [ ] 更新 `frontend/tailwind.config.js` 中的 `primary` 颜色
- [ ] 生成完整的颜色色阶（50-900）
- [ ] 更新阴影系统中的主色相关阴影

### 设计系统文档更新
- [ ] 更新 `docs/design/design_system.md` 中的品牌色定义
- [ ] 添加Logo使用规范
- [ ] 更新颜色使用示例

### 组件更新
- [ ] 更新 `frontend/src/components/Logo.vue` 使用真实Logo
- [ ] 验证所有使用主色的组件（按钮、链接、激活状态等）
- [ ] 测试不同背景下的Logo显示效果

### 测试验证
- [ ] 在不同设备上测试品牌色显示
- [ ] 验证Logo在不同尺寸下的显示效果
- [ ] 检查颜色对比度是否符合可访问性标准（WCAG AA）

---

## 🎨 颜色生成工具

如果需要基于主色生成完整的颜色色阶，可以使用以下工具：

1. **Tailwind Color Generator**：
   - https://uicolors.app/create
   - 输入主色，自动生成50-900色阶

2. **Coolors**：
   - https://coolors.co/
   - 创建调色板，生成和谐的色彩方案

3. **Adobe Color**：
   - https://color.adobe.com/
   - 创建专业的色彩方案

---

## 📌 注意事项

1. **颜色对比度**：
   - 确保文本颜色与背景颜色的对比度符合WCAG AA标准（至少4.5:1）
   - 使用 [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) 验证

2. **Logo适配**：
   - 确保Logo在不同背景（白色、浅灰、深色）下都清晰可见
   - 考虑提供深色和浅色版本的Logo

3. **品牌一致性**：
   - 提取的颜色应该与官网保持一致
   - 如果有品牌指南，优先参考品牌指南

---

**文档维护者**: Design Team  
**下一步**: 提取品牌色和Logo后，按照上述清单更新设计系统和代码

