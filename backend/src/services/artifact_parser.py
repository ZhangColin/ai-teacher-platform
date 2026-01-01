"""成果物解析服务：从 Markdown 中提取代码块"""
import re
from datetime import datetime
from typing import List
from ..models import Artifact


class ArtifactParser:
    """成果物解析服务"""
    
    # Markdown 代码块正则表达式
    CODE_BLOCK_PATTERN = re.compile(
        r'```(\w+)?\n(.*?)```',
        re.DOTALL  # 允许 . 匹配换行符
    )
    
    @staticmethod
    def parse_from_markdown(content: str) -> List[Artifact]:
        """
        从 Markdown 文本中提取代码块，生成成果物列表
        
        Args:
            content: Markdown 文本内容
            
        Returns:
            成果物列表
        """
        artifacts = []
        matches = ArtifactParser.CODE_BLOCK_PATTERN.findall(content)
        
        for language, code_content in matches:
            # 语言标识默认为空字符串，如果为空则使用 "text"
            language = language.strip() if language else "text"
            
            # 代码内容去除首尾空白
            code_content = code_content.strip()
            
            # 确定成果物类型（由语言标识决定）
            artifact_type = language
            
            # 创建 Artifact 对象
            artifact = Artifact(
                type=artifact_type,
                content=code_content,
                language=language,
                timestamp=datetime.now()
            )
            artifacts.append(artifact)
        
        return artifacts

