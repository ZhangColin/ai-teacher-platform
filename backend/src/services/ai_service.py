"""AI 服务：调用 LLM API"""
import os
import logging
import asyncio
from typing import Optional, Tuple, List, Dict, AsyncGenerator
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务客户端"""
    
    def __init__(self):
        """初始化 AI 服务"""
        self.client, self.model_name = self._get_ai_client()
    
    def _get_ai_client(self) -> Tuple[Optional[OpenAI], str]:
        """
        根据配置文件获取 OpenAI 兼容的客户端实例和模型名称。
        支持 DeepSeek, Kimi 等兼容 OpenAI 协议的模型。
        """
        provider = os.getenv("CURRENT_PROVIDER", "kimi").lower()
        
        api_key = ""
        base_url = ""
        model_name = ""
        
        # 根据服务商读取对应的环境变量
        if provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            base_url = os.getenv("DEEPSEEK_BASE_URL")
            model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif provider == "kimi":
            api_key = os.getenv("KIMI_API_KEY")
            base_url = os.getenv("KIMI_BASE_URL")
            model_name = os.getenv("KIMI_MODEL", "moonshot-v1-8k")
        
        # 校验 API Key 是否有效
        if not api_key or not api_key.startswith("sk-"):
            logger.warning(f"未找到服务商 [{provider}] 的有效 Key，将使用 Mock 模式。")
            return None, "mock-model"
        
        # 从环境变量读取超时配置（秒），默认120秒
        timeout_seconds = float(os.getenv("AI_REQUEST_TIMEOUT", "120"))
        
        # 创建客户端，配置超时时间
        # timeout参数可以是单个数字（所有操作的超时时间）或httpx.Timeout对象（分别配置连接、读取等超时）
        client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            timeout=timeout_seconds,  # 设置超时时间
            max_retries=2  # 失败后最多重试2次
        )
        
        logger.info(f"AI 客户端初始化成功 - 服务商: {provider}, 模型: {model_name}, 超时: {timeout_seconds}秒")
        return client, model_name
    
    async def generate_welcome_message(self, system_prompt: str) -> str:
        """
        生成欢迎消息
        
        Args:
            system_prompt: Agent 的系统提示词
            
        Returns:
            AI 生成的欢迎消息
        """
        # 无客户端时的模拟返回（用于本地无网调试）
        if not self.client:
            return "你好！我是你的 AI 助手。请告诉我你需要什么帮助。"
        
        try:
            # 记录系统提示词（用于调试）
            logger.info(f"生成欢迎消息 - 系统提示词长度: {len(system_prompt)} 字符")
            logger.debug(f"系统提示词内容: {system_prompt[:200]}...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请用一句话介绍你自己，并询问用户需要什么帮助。"}
                ],
                temperature=0.7
            )
            result = response.choices[0].message.content
            logger.info(f"AI 返回的欢迎消息: {result[:100]}...")
            return result
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（生成欢迎消息）- 错误类型: {error_type}: {e}", exc_info=True)
            
            # 根据错误类型返回友好提示
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return "⚠️ AI服务响应超时，请检查网络连接后重试。"
            else:
                return "欢迎使用 AI 助手！抱歉，当前服务暂时不可用，请稍后重试。"
    
    def _find_html_end_position(self, content: str) -> int:
        """
        找到 HTML 文档的结束位置（</html> 标签的位置）
        
        Returns:
            如果找到 </html>，返回其结束位置（包含 </html> 标签）
            如果没找到，返回 -1
        """
        import re
        # 查找最后一个 </html> 标签（不区分大小写）
        pattern = re.compile(r'</html>', re.IGNORECASE)
        matches = list(pattern.finditer(content))
        if matches:
            # 返回最后一个 </html> 标签的结束位置
            last_match = matches[-1]
            return last_match.end()
        return -1
    
    def _detect_content_duplication(self, original: str, continuation: str, threshold: float = 0.7) -> tuple[bool, int]:
        """
        检测继续内容是否与原始内容重复
        
        Args:
            original: 原始内容
            continuation: 继续生成的内容
            threshold: 相似度阈值（0-1）
        
        Returns:
            (is_duplicate, overlap_length)
            is_duplicate: 是否重复
            overlap_length: 重复的长度（如果重复）
        """
        if not continuation or len(continuation) < 50:
            return False, 0
        
        # 方法1：检查继续内容是否在原始内容中出现过（完全匹配）
        # 如果继续内容的前100个字符在原始内容中出现，可能是重复
        continuation_start = continuation[:200].strip()
        if continuation_start in original:
            overlap_pos = original.find(continuation_start)
            if overlap_pos >= 0:
                # 计算重复的长度
                overlap_length = min(len(continuation_start), len(original) - overlap_pos)
                logger.warning(f"检测到继续内容在原始内容中完全匹配，位置: {overlap_pos}, 重复长度: {overlap_length}")
                return True, overlap_length
        
        # 方法2：检查继续内容是否与原始内容的结尾高度相似
        # 比较原始内容的最后 N 个字符与继续内容的前 N 个字符
        compare_length = min(300, len(original), len(continuation))
        if compare_length < 50:
            return False, 0
        
        original_end = original[-compare_length:].lower().strip()
        continuation_start = continuation[:compare_length].lower().strip()
        
        # 计算相似度
        same_chars = sum(1 for a, b in zip(original_end, continuation_start) if a == b)
        similarity = same_chars / compare_length if compare_length > 0 else 0
        
        if similarity >= threshold:
            # 找到最佳分割点
            split_pos = 0
            for i in range(min(len(original_end), len(continuation_start)) - 1, -1, -1):
                if original_end[i] != continuation_start[i]:
                    split_pos = i + 1
                    break
            if split_pos > 0:
                logger.warning(f"检测到高相似度重复（{similarity:.2%}），建议去除前 {split_pos} 字符")
                return True, split_pos
        
        return False, 0
    
    def _clean_after_html_end(self, content: str) -> str:
        """
        清理 </html> 标签之后的内容
        
        如果检测到 </html> 标签，只保留到 </html> 标签结束的内容
        """
        html_end_pos = self._find_html_end_position(content)
        if html_end_pos > 0:
            # 检查 </html> 之后是否有内容
            after_html = content[html_end_pos:].strip()
            if after_html:
                logger.warning(f"检测到 </html> 标签之后还有内容（{len(after_html)} 字符），将清理掉")
                logger.debug(f"</html> 之后的内容预览（前200字符）:\n{after_html[:200]}")
                # 只保留到 </html> 标签结束
                return content[:html_end_pos].rstrip()
        return content
    
    def _check_code_completeness(self, content: str) -> dict:
        """
        检测代码完整性（HTML/JavaScript）
        
        Returns:
            {
                'is_complete': bool,
                'missing_tags': list,  # 缺失的闭合标签
                'issues': list  # 其他问题
            }
        """
        import re
        issues = []
        missing_tags = []
        
        content_lower = content.lower()
        is_html = '<html' in content_lower or '<!doctype' in content_lower
        
        if is_html:
            # 检查 HTML 标签匹配
            html_open = content_lower.count('<html')
            html_close = content_lower.count('</html>')
            if html_open > html_close:
                missing_tags.append('</html>')
                issues.append(f'HTML标签不匹配: <html>={html_open}, </html>={html_close}')
            
            body_open = content_lower.count('<body')
            body_close = content_lower.count('</body>')
            if body_open > body_close:
                missing_tags.append('</body>')
                issues.append(f'Body标签不匹配: <body>={body_open}, </body>={body_close}')
            
            head_open = content_lower.count('<head')
            head_close = content_lower.count('</head>')
            if head_open > head_close:
                missing_tags.append('</head>')
                issues.append(f'Head标签不匹配: <head>={head_open}, </head>={head_close}')
            
            # 检查未闭合的标签（简单检测）
            # 查找所有开始标签，检查是否有对应的结束标签
            tag_pattern = re.compile(r'<(\w+)[^>]*>', re.IGNORECASE)
            open_tags = tag_pattern.findall(content)
            close_tag_pattern = re.compile(r'</(\w+)>', re.IGNORECASE)
            close_tags = close_tag_pattern.findall(content)
            
            # 统计标签（忽略自闭合标签）
            self_closing_tags = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
            tag_counts = {}
            for tag in open_tags:
                if tag.lower() not in self_closing_tags:
                    tag_counts[tag.lower()] = tag_counts.get(tag.lower(), 0) + 1
            for tag in close_tags:
                if tag.lower() in tag_counts:
                    tag_counts[tag.lower()] -= 1
            
            # 找出未闭合的标签
            for tag, count in tag_counts.items():
                if count > 0:
                    issues.append(f'未闭合的标签: <{tag}> (缺少 {count} 个闭合标签)')
        
        # 检查 JavaScript 括号匹配（简单检测）
        if '<script' in content_lower:
            open_braces = content.count('{')
            close_braces = content.count('}')
            if open_braces > close_braces:
                issues.append(f'JavaScript大括号不匹配: {{={open_braces}, }}={close_braces}')
            
            open_parens = content.count('(')
            close_parens = content.count(')')
            if open_parens > close_parens:
                issues.append(f'JavaScript圆括号不匹配: (={open_parens}, )={close_parens}')
        
        # 检查 HTML 是否已经完整闭合（有 </html> 标签）
        html_end_pos = self._find_html_end_position(content)
        if is_html and html_end_pos > 0:
            # 检查 </html> 之后是否有有效内容
            after_html = content[html_end_pos:].strip()
            # 如果 </html> 之后只有空白或很少的内容，认为 HTML 已经完整
            if len(after_html) < 50 or not any(c.isalnum() for c in after_html):
                # HTML 已经完整闭合
                is_complete = True
                logger.info("HTML 已经完整闭合（检测到 </html> 标签且之后无有效内容）")
            else:
                # </html> 之后还有内容，可能是重复或错误
                issues.append(f'</html> 标签之后还有内容（{len(after_html)} 字符），可能是重复内容')
                is_complete = False
        else:
            is_complete = len(issues) == 0
        
        return {
            'is_complete': is_complete,
            'missing_tags': missing_tags,
            'issues': issues,
            'html_end_pos': html_end_pos if is_html else -1
        }
    
    def _clean_continue_result(self, continue_result: str, is_html: bool = False) -> str:
        """
        清理自动继续返回的内容，提取纯代码内容
        
        处理情况：
        1. 如果包含Markdown代码块标记（```html、```等），提取代码块内的内容
        2. 清理对话文本、注释等非代码内容
        3. 处理可能的重复标记
        
        Args:
            continue_result: AI继续返回的原始内容
            is_html: 是否是HTML内容
            
        Returns:
            清理后的纯代码内容
        """
        import re
        
        result = continue_result.strip()
        
        # 1. 尝试提取Markdown代码块内的内容
        # 匹配 ```语言标记\n内容\n``` 格式
        code_block_pattern = re.compile(r'```(?:\w+)?\s*\n(.*?)```', re.DOTALL)
        matches = code_block_pattern.findall(result)
        if matches:
            # 如果找到代码块，使用最后一个代码块的内容（AI可能输出多个代码块）
            extracted_content = matches[-1].strip()
            logger.info(f"从Markdown代码块中提取内容，原始长度: {len(result)}, 提取后长度: {len(extracted_content)}")
            result = extracted_content
        
        # 2. 清理常见的对话文本和注释
        # 移除类似 "当然,这里是完成的HTML代码:" 这样的对话文本
        # 移除类似 "// ... 省略已生成部分 ..." 这样的注释
        lines = result.split('\n')
        cleaned_lines = []
        skip_patterns = [
            r'^当然[,，].*',
            r'^这里是.*',
            r'^以下是.*',
            r'^//\s*\.\.\.\s*.*',
            r'^//\s*省略.*',
            r'^#\s*\.\.\.\s*.*',
            r'^#\s*省略.*',
        ]
        
        for line in lines:
            # 跳过匹配对话文本模式的行
            should_skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    should_skip = True
                    logger.debug(f"跳过对话文本行: {line[:100]}")
                    break
            if not should_skip:
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # 3. 如果是HTML，确保没有残留的Markdown标记
        if is_html:
            # 移除可能的残留标记
            result = re.sub(r'^```\s*\w*\s*\n', '', result, flags=re.MULTILINE)
            result = re.sub(r'\n```\s*$', '', result, flags=re.MULTILINE)
            result = result.strip()
        
        logger.info(f"清理完成，最终内容长度: {len(result)} 字符")
        if len(result) != len(continue_result):
            logger.info(f"清理前后对比预览（清理后前200字符）:\n{result[:200]}")
        
        return result
    
    async def chat(self, system_prompt: str, history: List[Dict[str, str]], user_message: str, max_continue: int = 3) -> str:
        """
        进行对话（非流式）
        
        Args:
            system_prompt: Agent 的系统提示词
            history: 历史消息列表（格式：[{"role": "user/assistant", "content": "..."}, ...]）
            user_message: 用户当前消息
            max_continue: 最大继续生成次数（防止无限递归）
            
        Returns:
            AI 生成的回复
        """
        # 无客户端时的模拟返回
        if not self.client:
            return f"Mock 回复：收到你的消息「{user_message}」"
        
        try:
            # 构建消息链：System Prompt + History + Current Input
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史消息
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 记录系统提示词（用于调试）
            logger.info(f"对话请求 - 系统提示词长度: {len(system_prompt)} 字符, 历史消息数: {len(history)}, 用户消息: {user_message[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            logger.info(f"AI 返回的回复长度: {len(result)} 字符, finish_reason: {finish_reason}")
            
            # 如果内容包含HTML，记录详细信息用于排查
            if '<html' in result.lower() or '<!doctype' in result.lower():
                logger.info("=" * 80)
                logger.info("检测到HTML内容，记录详细信息用于排查:")
                logger.info(f"HTML内容长度: {len(result)} 字符")
                logger.info(f"包含 <html> 标签: {'<html' in result.lower()}")
                logger.info(f"包含 </html> 标签: {'</html>' in result.lower()}")
                logger.info(f"包含 <!doctype> 标签: {'<!doctype' in result.lower()}")
                logger.info(f"HTML内容预览（前1000字符）:\n{result[:1000]}")
                logger.info(f"HTML内容预览（后1000字符）:\n{result[-1000:]}")
                # 检查HTML标签是否完整
                html_open_count = result.lower().count('<html')
                html_close_count = result.lower().count('</html>')
                body_open_count = result.lower().count('<body')
                body_close_count = result.lower().count('</body>')
                logger.info(f"HTML标签统计: <html>={html_open_count}, </html>={html_close_count}, <body>={body_open_count}, </body>={body_close_count}")
                if html_open_count != html_close_count:
                    logger.warning(f"⚠️ HTML标签不匹配！<html>标签数: {html_open_count}, </html>标签数: {html_close_count}")
                logger.info("=" * 80)
            
            # 如果因为达到最大token限制而截断，自动继续生成直到完整
            if finish_reason == 'length' and max_continue > 0:
                logger.info(f"检测到内容因token限制被截断，开始自动继续生成（剩余次数: {max_continue}，内容长度: {len(result)}）...")
                
                # 循环继续生成，直到代码完整或达到最大次数
                accumulated_result = result
                continue_count = 0
                is_html = '<html' in result.lower() or '<!doctype' in result.lower()
                
                while max_continue > 0:
                    continue_count += 1
                    logger.info(f"第 {continue_count} 次继续生成（剩余次数: {max_continue}）...")
                    logger.info(f"当前内容长度: {len(accumulated_result)} 字符")
                    logger.info(f"截断位置预览（最后500字符）:\n{accumulated_result[-500:]}")
                    
                    # 清理 </html> 之后的内容（如果存在）
                    if is_html:
                        accumulated_result = self._clean_after_html_end(accumulated_result)
                    
                    # 检查代码完整性
                    completeness_check = self._check_code_completeness(accumulated_result)
                    if completeness_check['is_complete']:
                        logger.info("✅ 代码完整性检查通过，停止继续生成")
                        break
                    else:
                        logger.warning(f"⚠️ 代码不完整，问题: {completeness_check['issues']}")
                        if completeness_check['missing_tags']:
                            logger.warning(f"缺失的标签: {completeness_check['missing_tags']}")
                        
                        # 如果 HTML 已经有 </html> 标签，但检测到不完整，可能是检测逻辑问题
                        # 这种情况下，如果 </html> 之后没有内容，应该认为完整
                        if is_html and completeness_check['html_end_pos'] > 0:
                            after_html = accumulated_result[completeness_check['html_end_pos']:].strip()
                            if len(after_html) < 50:
                                logger.info("HTML 已完整闭合，停止继续生成")
                                break
                    
                    # 生成继续提示词（更严格的提示）
                    if is_html:
                        # 检查是否已经有 </html> 标签
                        if completeness_check['html_end_pos'] > 0:
                            # 已经有 </html>，不应该继续生成
                            logger.warning("检测到 HTML 已有 </html> 标签，但完整性检查未通过，可能是检测逻辑问题")
                            # 检查 </html> 之后的内容
                            after_html = accumulated_result[completeness_check['html_end_pos']:].strip()
                            if len(after_html) < 50:
                                # </html> 之后没有有效内容，认为完整
                                break
                            else:
                                # </html> 之后有内容，可能是重复，清理掉后停止
                                accumulated_result = accumulated_result[:completeness_check['html_end_pos']].rstrip()
                                break
                        
                        if completeness_check['missing_tags']:
                            missing_tags_str = '、'.join(completeness_check['missing_tags'])
                            continue_message = f"上面的HTML代码被截断了，请继续完成剩余的HTML代码。需要确保包含以下缺失的标签: {missing_tags_str}。重要：只输出HTML代码内容，不要包含Markdown代码块标记（```html或```），不要包含任何解释文字或注释，不要重复已生成的部分，直接继续输出HTML代码。"
                        else:
                            continue_message = "上面的HTML代码被截断了，请继续完成剩余的内容。重要：只输出HTML代码内容，不要包含Markdown代码块标记（```html或```），不要包含任何解释文字或注释，不要重复已生成的部分，直接继续输出HTML代码。如果HTML已经完整（已有</html>标签），请停止输出。"
                    else:
                        continue_message = "请继续完成上面的内容，不要重复已生成的部分。如果内容是代码，请只输出代码内容，不要包含Markdown代码块标记或解释文字。"
                    
                    # 将已生成的内容添加到历史消息中
                    new_history = history + [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": accumulated_result}
                    ]
                    
                    # 继续生成
                    continue_result = await self.chat(system_prompt, new_history, continue_message, max_continue - 1)
                    
                    # 清理继续返回的内容
                    cleaned_continue_result = self._clean_continue_result(continue_result, is_html)
                    
                    if not cleaned_continue_result or len(cleaned_continue_result.strip()) == 0:
                        logger.warning("继续生成的内容为空，停止继续")
                        break
                    
                    # 检测内容重复（更严格的检测）
                    is_duplicate, overlap_length = self._detect_content_duplication(
                        accumulated_result, 
                        cleaned_continue_result,
                        threshold=0.6  # 降低阈值，更严格检测重复
                    )
                    
                    if is_duplicate:
                        if overlap_length > 0:
                            # 去除重复部分
                            cleaned_continue_result = cleaned_continue_result[overlap_length:]
                            logger.warning(f"检测到内容重复，去除前 {overlap_length} 字符")
                        
                        # 如果去除重复后内容很少或为空，可能是完全重复
                        if len(cleaned_continue_result.strip()) < 100:
                            logger.warning("继续生成的内容与原始内容高度重复，停止继续生成")
                            break
                    
                    # 如果 HTML 已经有 </html> 标签，检查继续内容是否应该被忽略
                    if is_html and completeness_check['html_end_pos'] > 0:
                        # HTML 已经完整，继续生成的内容可能是重复的
                        # 检查继续内容是否包含 </html> 或重复的代码结构
                        if '</html>' in cleaned_continue_result.lower():
                            logger.warning("继续生成的内容包含 </html> 标签，但原始内容已有 </html>，可能是重复，忽略继续内容")
                            break
                        
                        # 检查继续内容是否与原始内容的某部分重复
                        # 如果继续内容的前200字符在原始内容中出现过，可能是重复
                        continue_preview = cleaned_continue_result[:200].strip()
                        if continue_preview in accumulated_result:
                            logger.warning("继续生成的内容与原始内容重复，忽略继续内容")
                            break
                    
                    # 拼接结果
                    accumulated_result = accumulated_result + cleaned_continue_result
                    
                    # 再次清理 </html> 之后的内容（防止拼接后出现问题）
                    if is_html:
                        accumulated_result = self._clean_after_html_end(accumulated_result)
                    
                    max_continue -= 1
                    
                    logger.info(f"第 {continue_count} 次继续完成，当前总长度: {len(accumulated_result)} 字符（本次新增: {len(cleaned_continue_result)} 字符）")
                
                # 最终清理和验证
                if is_html:
                    accumulated_result = self._clean_after_html_end(accumulated_result)
                
                # 最终完整性检查
                final_check = self._check_code_completeness(accumulated_result)
                if not final_check['is_complete']:
                    logger.warning(f"⚠️ 经过 {continue_count} 次继续生成后，代码仍然不完整:")
                    for issue in final_check['issues']:
                        logger.warning(f"  - {issue}")
                else:
                    logger.info(f"✅ 经过 {continue_count} 次继续生成，代码已完整")
                
                # 记录最终结果
                if is_html:
                    logger.info("=" * 80)
                    logger.info("最终HTML内容检查:")
                    logger.info(f"最终内容长度: {len(accumulated_result)} 字符")
                    logger.info(f"包含 <html> 标签: {'<html' in accumulated_result.lower()}")
                    logger.info(f"包含 </html> 标签: {'</html>' in accumulated_result.lower()}")
                    logger.info("=" * 80)
                
                return accumulated_result
            
            return result
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（对话）- 错误类型: {error_type}: {e}", exc_info=True)
            
            # 根据错误类型返回友好提示
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return "⚠️ AI服务响应超时，可能是网络问题，请稍后重试。"
            elif "connection" in str(e).lower():
                return "⚠️ 无法连接到AI服务，请检查网络或API配置。"
            else:
                return f"⚠️ AI服务调用失败: {str(e)[:100]}"
    
    async def chat_stream(self, system_prompt: str, history: List[Dict[str, str]], user_message: str, max_continue: int = 3) -> AsyncGenerator[str, None]:
        """
        进行对话（流式输出）
        
        Args:
            system_prompt: Agent 的系统提示词
            history: 历史消息列表（格式：[{"role": "user/assistant", "content": "..."}, ...]）
            user_message: 用户当前消息
            max_continue: 最大继续生成次数（防止无限递归）
            
        Yields:
            str: AI 生成的回复片段（逐块返回）
        """
        # 无客户端时的模拟返回
        if not self.client:
            mock_reply = f"Mock 回复：收到你的消息「{user_message}」"
            # 模拟流式输出
            for char in mock_reply:
                yield char
                await asyncio.sleep(0.05)  # 模拟延迟
            return
        
        try:
            # 构建消息链：System Prompt + History + Current Input
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加历史消息
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 记录系统提示词（用于调试）
            logger.info(f"流式对话请求 - 系统提示词长度: {len(system_prompt)} 字符, 历史消息数: {len(history)}, 用户消息: {user_message[:50]}...")
            
            # 使用流式输出（同步调用，需要在异步函数中处理）
            # 注意：OpenAI 客户端的流式调用是同步的，需要在异步上下文中处理
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                stream=True  # 启用流式输出
            )
            
            # 逐块返回内容（在异步上下文中处理同步流）
            accumulated_content = ""
            finish_reason = None
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    if delta and delta.content:
                        accumulated_content += delta.content
                        yield delta.content
                        # 让出控制权，允许其他协程运行，确保流式数据及时发送
                        await asyncio.sleep(0.001)  # 很小的延迟，确保流式效果
                    
                    # 检查是否完成，并记录 finish_reason
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
                        logger.info(f"流式输出完成，finish_reason: {finish_reason}, 已生成内容长度: {len(accumulated_content)}")
            
            # 如果因为达到最大token限制而截断，判断是否需要自动继续
            # 只有在以下情况才自动继续：
            # 1. finish_reason == 'length'（确实因为token限制截断）
            # 2. 内容长度超过一定阈值（比如1000字符，说明是长内容）
            # 3. 内容包含代码块标记（```），说明是代码生成任务
            # 4. 内容不以问号、感叹号结尾，且不包含明显的追问词（避免干扰多轮对话）
            should_auto_continue = (
                finish_reason == 'length' and 
                max_continue > 0 and
                len(accumulated_content) > 1000 and  # 内容足够长
                ('```' in accumulated_content or '<' in accumulated_content) and  # 包含代码或HTML标记
                not accumulated_content.rstrip().endswith(('?', '？', '!', '！')) and  # 不以问号/感叹号结尾
                not any(word in accumulated_content[-200:] for word in ['请', '需要', '能否', '可以', '希望', '想要'])  # 最后200字符不包含追问词
            )
            
            if should_auto_continue:
                logger.info(f"检测到长内容因token限制被截断，自动继续生成（剩余次数: {max_continue}，内容长度: {len(accumulated_content)}）...")
                logger.debug(f"已生成内容预览（最后500字符）: {accumulated_content[-500:]}")
                # 将已生成的内容添加到历史消息中
                new_history = history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": accumulated_content}
                ]
                # 继续生成（使用"继续"作为提示）
                continue_message = "请继续完成上面的内容，不要重复已生成的部分。"
                continue_count = 0
                async for chunk in self.chat_stream(system_prompt, new_history, continue_message, max_continue - 1):
                    continue_count += len(chunk) if chunk else 0
                    yield chunk
                logger.info(f"自动继续生成完成，继续部分长度: {continue_count} 字符")
            elif finish_reason == 'length':
                logger.info(f"检测到内容因token限制被截断，但判断为AI追问或短内容，不自动继续（内容长度: {len(accumulated_content)}）")
                logger.debug(f"内容预览（最后200字符）: {accumulated_content[-200:]}")
                    
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"AI 服务调用异常（流式对话）- 错误类型: {error_type}: {e}", exc_info=True)
            
            # 根据不同错误类型给出更友好的提示
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                yield "⚠️ AI服务响应超时，可能是网络问题。建议：\n1. 检查网络连接\n2. 如果使用代理，请确认代理设置正确\n3. 稍后重试"
            elif "connection" in str(e).lower() or "connect" in str(e).lower():
                yield "⚠️ 无法连接到AI服务，请检查：\n1. 网络是否正常\n2. API密钥是否正确\n3. 服务提供商是否可用"
            else:
                yield f"⚠️ AI服务调用失败: {str(e)[:100]}\n请稍后重试或联系管理员。"

