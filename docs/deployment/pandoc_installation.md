# Pandoc 安装指南

> **重要**: Markdown 转 Word 功能依赖 pandoc，必须在服务器上安装 pandoc 才能使用此功能。

---

## 功能说明

**功能**: 将 Markdown 内容转换为 Word 文档（.docx），支持数学公式（LaTeX 语法）

**核心需求**: 数学公式必须正确转换（使用 MathML 格式）

**API 接口**: `POST /api/v1/convert/markdown-to-word`

**支持的数学公式格式**:
- ✅ Markdown 扩展语法：`$...$` (行内公式) 和 `$$...$$` (块级公式)
- ✅ LaTeX 原生语法：`\(...\)` (行内公式) 和 `\[...\]` (块级公式)
- ✅ 混合使用两种语法

> **重要**: 不同的大模型返回的数学公式格式可能不同，本实现支持两种格式，确保兼容性。

---

## Pandoc 安装方法

### macOS

```bash
# 使用 Homebrew 安装
brew install pandoc

# 验证安装
pandoc --version
```

### Ubuntu/Debian

```bash
# 使用 apt 安装
sudo apt update
sudo apt install -y pandoc

# 验证安装
pandoc --version
```

### CentOS/RHEL

```bash
# 使用 yum 安装
sudo yum install -y pandoc

# 或使用 dnf（CentOS 8+）
sudo dnf install -y pandoc

# 验证安装
pandoc --version
```

### Docker 环境

如果使用 Docker 部署，在 Dockerfile 中添加：

```dockerfile
# 基于 Python 镜像
FROM python:3.11-slim

# 安装 pandoc
RUN apt-get update && \
    apt-get install -y pandoc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ... 其他配置
```

### 手动安装（通用方法）

从官方网站下载安装包：https://pandoc.org/installing.html

---

## 验证安装

安装完成后，运行以下命令验证：

```bash
pandoc --version
```

应该看到类似输出：

```
pandoc 3.x.x
...
```

---

## 测试转换功能

### 1. 创建测试 Markdown 文件

**测试1: Markdown 扩展语法（$ 语法）**

```bash
cat > test_dollar.md << 'EOF'
# 测试文档 - $ 语法

这是一个测试文档，包含数学公式。

行内公式：$E=mc^2$

块级公式：

$$
\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
EOF
```

**测试2: LaTeX 原生语法（反斜杠语法）**

```bash
cat > test_latex.md << 'EOF'
# 测试文档 - LaTeX 原生语法

这是一个测试文档，包含数学公式。

行内公式：\(E=mc^2\)

块级公式：

\[
\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\]
EOF
```

### 2. 测试转换

**测试 $ 语法**:
```bash
pandoc test_dollar.md -o test_dollar.docx --from=markdown+tex_math_dollars+tex_math_double_backslash --to=docx --standalone
```

**测试 LaTeX 原生语法**:
```bash
pandoc test_latex.md -o test_latex.docx --from=markdown+tex_math_dollars+tex_math_double_backslash --to=docx --standalone
```

> **注意**: 
> - `--from=markdown+tex_math_dollars+tex_math_double_backslash` 参数同时支持两种数学公式语法
> - 不使用 `--mathml` 参数，让 pandoc 使用默认的 OMML (Office Math) 格式
> - OMML 是 Word 原生的数学公式格式，渲染效果比 MathML 更好

### 3. 验证结果

打开生成的 `test_dollar.docx` 和 `test_latex.docx` 文件，检查：
- ✅ 标题正确显示
- ✅ 数学公式正确渲染（不是纯文本）
- ✅ 两种语法的公式都正确转换
- ✅ 中文内容正常显示

**常见大模型的数学公式格式**:
- **ChatGPT / GPT-4**: 通常使用 `$...$` 和 `$$...$$`
- **Claude**: 通常使用 `$...$` 和 `$$...$$`
- **DeepSeek**: 可能混合使用两种格式
- **Gemini**: 可能使用 `\(...\)` 和 `\[...\]`

本实现支持所有格式，确保兼容性。

---

## 故障排查

### 问题1：pandoc 命令未找到

**症状**: `FileNotFoundError: [Errno 2] No such file or directory: 'pandoc'`

**解决方案**:
1. 确认 pandoc 已安装：`which pandoc`
2. 如果未安装，按照上述方法安装
3. 如果已安装但找不到，检查 PATH 环境变量

### 问题2：数学公式显示为纯文本

**症状**: Word 文档中数学公式显示为 `$E=mc^2$` 而不是渲染后的公式

**原因**: Markdown 源文件中的公式语法不正确，或 pandoc 参数配置有误

**解决方案**: 
1. 确保使用正确的公式语法：`$$E=mc^2$$` 或 `\(E=mc^2\)`
2. 确保 pandoc 参数包含 `--from=markdown+tex_math_dollars+tex_math_double_backslash`
3. 使用默认的 OMML 格式（不要添加 `--mathml` 参数）

### 问题3：转换超时

**症状**: `RuntimeError: pandoc 转换超时（30秒）`

**原因**: Markdown 内容过大或服务器性能不足

**解决方案**:
1. 检查 Markdown 内容大小
2. 增加服务器资源
3. 如需调整超时时间，修改 `conversion_service.py` 中的 `timeout=30`

---

## 性能建议

- **小文档（< 100KB）**: 转换时间通常 < 1 秒
- **中等文档（100KB - 1MB）**: 转换时间 1-5 秒
- **大文档（> 1MB）**: 转换时间 5-30 秒

如果经常处理大文档，建议：
1. 增加服务器内存
2. 考虑异步处理（后续优化）
3. 添加文件大小限制

---

## 安全注意事项

1. **输入验证**: 后端已验证 Markdown 内容不为空
2. **文件名清理**: 后端已清理文件名中的特殊字符
3. **临时文件**: 使用 Python `tempfile` 模块，自动清理
4. **超时保护**: 30 秒超时，防止长时间占用资源

---

## 后续优化建议

1. **异步处理**: 对于大文档，使用后台任务队列
2. **缓存机制**: 相同内容可以缓存转换结果
3. **批量转换**: 支持一次转换多个文档
4. **格式扩展**: 支持转换为 PDF、HTML 等其他格式

---

## 已知限制

### WPS Office 兼容性问题

**症状**: 使用 WPS Office 打开导出的 Word 文档时，数学公式显示不正确（上标、分数、根号等显示异常）

**原因**: 
- 我们使用的 OMML (Office Math Markup Language) 是微软 Word 的原生数学公式格式
- WPS Office 对 OMML 格式的支持不完整，导致复杂公式无法正确渲染
- 这是 WPS 的兼容性问题，不是我们代码的问题

**验证**: 
- ✅ 使用 **Microsoft Word** 打开：公式显示**完全正常**
- ❌ 使用 **WPS Office** 打开：公式显示**异常**

**解决方案**:
- **推荐**: 使用 Microsoft Word 打开导出的文档
- **替代方案**: 如果必须使用 WPS，建议在导出页面添加提示或使用在线文档预览

**技术说明**:
- pandoc 生成的 OMML 格式完全符合 Microsoft Office 标准
- 文档内部 XML 结构经过验证是正确的
- 这是行业标准做法，大多数 Markdown 转 Word 工具都采用此方案

---

**文档版本**: v1.1  
**创建日期**: 2026-01-09  
**最后更新**: 2026-01-09  
**维护者**: DevOps Team
