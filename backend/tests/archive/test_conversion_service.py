"""测试 ConversionService"""
import pytest
from src.services.conversion_service import ConversionService


class TestConversionService:
    """测试文档转换服务"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.service = ConversionService()
    
    def test_markdown_to_word_basic(self):
        """测试基础 Markdown 转 Word 功能"""
        markdown_content = """# 测试文档

这是一个测试文档。

## 二级标题

- 列表项 1
- 列表项 2

**粗体文本** 和 *斜体文本*。
"""
        
        word_content, filename = self.service.markdown_to_word(markdown_content)
        
        # 验证返回值
        assert isinstance(word_content, bytes)
        assert len(word_content) > 0
        assert filename.endswith(".docx")
    
    def test_markdown_to_word_with_math_dollar_syntax(self):
        """测试包含数学公式的 Markdown 转 Word 功能 - $ 语法（核心需求）"""
        markdown_content = """# 数学公式测试 - $ 语法

行内公式：$E=mc^2$

块级公式：

$$
\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}
$$

更复杂的公式：

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$
"""
        
        word_content, filename = self.service.markdown_to_word(markdown_content)
        
        # 验证返回值
        assert isinstance(word_content, bytes)
        assert len(word_content) > 0
        assert filename.endswith(".docx")
        # Word 文件应该包含 MathML 标记（pandoc 生成的数学公式）
        # 注意：这里只能验证文件生成成功，实际公式渲染需要手动测试
    
    def test_markdown_to_word_with_math_latex_syntax(self):
        """测试包含数学公式的 Markdown 转 Word 功能 - LaTeX 原生语法（核心需求）"""
        markdown_content = r"""# 数学公式测试 - LaTeX 原生语法

行内公式：\(E=mc^2\)

块级公式：

\[
\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\]

更复杂的公式：

\[
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
\]
"""
        
        word_content, filename = self.service.markdown_to_word(markdown_content)
        
        # 验证返回值
        assert isinstance(word_content, bytes)
        assert len(word_content) > 0
        assert filename.endswith(".docx")
    
    def test_markdown_to_word_with_math_mixed_syntax(self):
        """测试同时包含两种数学公式语法的 Markdown 转 Word 功能"""
        markdown_content = r"""# 混合语法测试

Markdown 语法：$E=mc^2$

LaTeX 原生语法：\(F=ma\)

块级 Markdown 语法：

$$
\alpha + \beta = \gamma
$$

块级 LaTeX 原生语法：

\[
x^2 + y^2 = z^2
\]
"""
        
        word_content, filename = self.service.markdown_to_word(markdown_content)
        
        # 验证返回值
        assert isinstance(word_content, bytes)
        assert len(word_content) > 0
        assert filename.endswith(".docx")
    
    def test_markdown_to_word_with_custom_filename(self):
        """测试自定义文件名"""
        markdown_content = "# 测试"
        custom_filename = "my_document"
        
        word_content, filename = self.service.markdown_to_word(
            markdown_content, 
            filename=custom_filename
        )
        
        assert filename == f"{custom_filename}.docx"
    
    def test_markdown_to_word_empty_content(self):
        """测试空内容应抛出异常"""
        with pytest.raises(ValueError, match="Markdown 内容不能为空"):
            self.service.markdown_to_word("")
    
    def test_markdown_to_word_whitespace_only(self):
        """测试仅包含空白字符的内容应抛出异常"""
        with pytest.raises(ValueError, match="Markdown 内容不能为空"):
            self.service.markdown_to_word("   \n\n   ")
    
    def test_markdown_to_word_special_chars_in_filename(self):
        """测试文件名包含特殊字符时应自动清理"""
        markdown_content = "# 测试"
        unsafe_filename = "test<>:\"/\\|?*file"
        
        word_content, filename = self.service.markdown_to_word(
            markdown_content,
            filename=unsafe_filename
        )
        
        # 文件名应该被清理，只保留安全字符
        assert filename.endswith(".docx")
        assert "<" not in filename
        assert ">" not in filename
    
    def test_markdown_to_word_chinese_content(self):
        """测试中文内容转换"""
        markdown_content = """# 中文标题

这是中文内容，包含**加粗**和*斜体*。

数学公式：$\\alpha + \\beta = \\gamma$
"""
        
        word_content, filename = self.service.markdown_to_word(markdown_content)
        
        assert isinstance(word_content, bytes)
        assert len(word_content) > 0
    
    def test_check_pandoc_available(self):
        """测试 pandoc 可用性检查"""
        # 如果能初始化 ConversionService，说明 pandoc 可用
        service = ConversionService()
        assert service is not None
