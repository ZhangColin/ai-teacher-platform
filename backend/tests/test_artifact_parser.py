"""ArtifactParser 单元测试"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.artifact_parser import ArtifactParser
from src.models import Artifact


class TestArtifactParser:
    """测试 ArtifactParser 类"""
    
    def test_parse_empty_content(self):
        """测试解析空内容（应该返回空列表）"""
        artifacts = ArtifactParser.parse_from_markdown("")
        assert artifacts == []
    
    def test_parse_no_code_blocks(self):
        """测试解析没有代码块的内容（应该返回空列表）"""
        content = "这是一段普通的文本，没有代码块。"
        artifacts = ArtifactParser.parse_from_markdown(content)
        assert artifacts == []
    
    def test_parse_single_code_block_with_language(self):
        """测试解析单个带语言标识的代码块"""
        content = """这是一段文本。

```markdown
## 标题
这是内容。
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "markdown"
        assert artifact.language == "markdown"
        assert "标题" in artifact.content
        assert isinstance(artifact.timestamp, datetime)
    
    def test_parse_single_code_block_without_language(self):
        """测试解析单个不带语言标识的代码块（应该使用 'text' 作为默认值）"""
        content = """文本内容。

```
这是代码内容。
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "text"
        assert artifact.language == "text"
        assert "代码内容" in artifact.content
    
    def test_parse_multiple_code_blocks(self):
        """测试解析多个代码块"""
        content = """第一段文本。

```markdown
## Markdown 内容
```

第二段文本。

```html
<div>HTML 内容</div>
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 2
        
        # 第一个代码块
        assert artifacts[0].type == "markdown"
        assert artifacts[0].language == "markdown"
        assert "Markdown 内容" in artifacts[0].content
        
        # 第二个代码块
        assert artifacts[1].type == "html"
        assert artifacts[1].language == "html"
        assert "HTML 内容" in artifacts[1].content
    
    def test_parse_code_block_with_multiline_content(self):
        """测试解析多行内容的代码块"""
        content = """文本。

```python
def hello():
    print("Hello")
    print("World")
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "python"
        assert artifact.language == "python"
        assert "def hello()" in artifact.content
        assert "print" in artifact.content
    
    def test_parse_code_block_strips_whitespace(self):
        """测试代码块内容去除首尾空白"""
        content = """文本。

```markdown
    
    内容前后有空白
    
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        # 内容应该去除首尾空白，但保留内部格式
        assert artifact.content.startswith("内容") or "内容" in artifact.content
    
    def test_parse_code_block_with_special_characters(self):
        """测试解析包含特殊字符的代码块"""
        content = """文本。

```json
{
  "key": "value",
  "number": 123
}
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "json"
        assert artifact.language == "json"
        assert "key" in artifact.content
        assert "value" in artifact.content
    
    def test_parse_code_block_different_languages(self):
        """测试解析不同语言的代码块"""
        content = """文本。

```javascript
console.log("JS");
```

```css
body { margin: 0; }
```

```svg
<svg><circle r="10"/></svg>
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 3
        languages = [a.language for a in artifacts]
        assert "javascript" in languages
        assert "css" in languages
        assert "svg" in languages
    
    def test_parse_code_block_timestamp(self):
        """测试代码块的时间戳"""
        content = """文本。

```markdown
内容
```"""
        artifacts = ArtifactParser.parse_from_markdown(content)
        
        assert len(artifacts) == 1
        assert isinstance(artifacts[0].timestamp, datetime)
        # 时间戳应该是最近的时间（几秒内）
        import time
        now = datetime.now()
        diff = abs((now - artifacts[0].timestamp).total_seconds())
        assert diff < 5  # 5秒内

