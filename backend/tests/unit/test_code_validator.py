import pytest
from src.services.code_validator import CodeValidator, ValidationResult

class TestCodeValidator:
    """测试代码验证器"""

    @pytest.fixture
    def validator(self):
        return CodeValidator()

    def test_complete_fence_block(self, validator):
        """测试完整的代码块应该通过验证"""
        content = '```html\n<div>内容</div>\n```'
        result = validator.validate_content(content)

        assert result.valid == True
        assert result.needs_continue == False
        assert len(result.issues) == 0

    def test_incomplete_fence_block(self, validator):
        """测试不完整的代码块应该验证失败"""
        content = '```html\n<div>内容'
        result = validator.validate_content(content)

        assert result.valid == False
        assert result.needs_continue == True
        assert any("代码块未闭合" in issue for issue in result.issues)

    def test_complete_html(self, validator):
        """测试完整的HTML应该通过验证"""
        content = '<div><p>内容</p></div>'
        result = validator.validate_content(content)

        assert result.valid == True
        assert len(result.issues) == 0

    def test_incomplete_html(self, validator):
        """测试不完整的HTML应该验证失败"""
        content = '<div><p>内容</p>'
        result = validator.validate_content(content)

        assert result.valid == False
        assert any("未闭合的HTML标签" in issue for issue in result.issues)

    def test_balanced_brackets(self, validator):
        """测试括号配对正确"""
        content = 'function test() { return [1, 2, 3]; }'
        result = validator.validate_content(content)

        assert result.valid == True

    def test_unbalanced_brackets(self, validator):
        """测试括号不配对"""
        content = 'function test() { return [1, 2, 3;'
        result = validator.validate_content(content)

        assert result.valid == False
        assert any("未闭合的括号" in issue for issue in result.issues)

    def test_self_closing_html_tags(self, validator):
        """测试自闭合HTML标签不应该报错"""
        content = '<div><img src="test.jpg" /><br /></div>'
        result = validator.validate_content(content)

        assert result.valid == True

    def test_complex_html_structure(self, validator):
        """测试复杂的HTML结构"""
        content = '''<html>
<body>
<div class="container">
  <p>段落1</p>
  <p>段落2</p>
</div>
</body>
</html>'''
        result = validator.validate_content(content)

        assert result.valid == True

    def test_nested_brackets(self, validator):
        """测试嵌套括号"""
        content = 'function outer() { return { inner: [1, 2, 3] }; }'
        result = validator.validate_content(content)

        assert result.valid == True

    def test_multiple_code_blocks(self, validator):
        """测试多个代码块"""
        content = '```python\nprint("hello")\n```\n\n```javascript\nconsole.log("world");\n```'
        result = validator.validate_content(content)

        assert result.valid == True
        assert content.count('```') == 4  # 2对

    def test_validation_result_to_dict(self, validator):
        """测试ValidationResult的to_dict方法"""
        content = '```html\n<div>内容'
        result = validator.validate_content(content)

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'valid' in result_dict
        assert 'issues' in result_dict
        assert 'needs_continue' in result_dict
        assert result_dict['valid'] == False
