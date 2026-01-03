"""工具服务：加载和管理工具配置"""
import yaml
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict
from ..models import Tool

logger = logging.getLogger(__name__)


class ToolService:
    """工具加载和管理服务"""
    
    def __init__(self, config_dir: str = "configs/tools"):
        """
        初始化工具服务
        
        Args:
            config_dir: 工具配置文件目录路径（相对于项目根目录）
        """
        self.config_dir = Path(config_dir)
        self._tools_cache: Optional[List[Tool]] = None
        self._cache_timestamp: Optional[float] = None
    
    def load_tool(self, config_path: Path) -> Optional[Tool]:
        """
        从配置文件加载单个工具
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Tool 实例，如果加载失败返回 None
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 构建 Tool
            tool = Tool(
                tool_id=config_data.get('tool_id', ''),
                name=config_data.get('name', ''),
                description=config_data.get('description'),
                system_prompt=config_data.get('system_prompt', ''),
                category=config_data.get('category', ''),
                icon=config_data.get('icon'),
                visible=config_data.get('visible', True),  # 默认值为 True
                type=config_data.get('type', 'normal'),  # 默认值为 'normal'
                welcome_message=config_data.get('welcome_message', ''),
                order=config_data.get('order', 999)  # 默认值为 999
            )
            
            # 验证配置
            if not tool.validate():
                return None
            
            return tool
            
        except Exception as e:
            # 加载失败，静默返回 None（根据业务规则，失败的工具不包含在列表中）
            logger.warning(f"加载工具配置失败: {config_path}, 错误: {e}")
            return None
    
    def load_all_tools(self) -> List[Tool]:
        """
        加载所有配置的工具（带缓存机制）
        只返回 visible=true 的工具
        
        Returns:
            工具列表（只包含成功加载且 visible=true 的工具）
        """
        # 检查缓存是否有效（5分钟过期）
        current_time = time.time()
        if (self._tools_cache is not None and 
            self._cache_timestamp is not None and 
            current_time - self._cache_timestamp < 300):
            return self._tools_cache
        
        tools = []
        
        if not self.config_dir.exists():
            self._tools_cache = tools
            self._cache_timestamp = current_time
            return tools
        
        # 扫描所有 .yaml 文件
        for config_file in self.config_dir.glob("*.yaml"):
            tool = self.load_tool(config_file)
            if tool and tool.visible:  # 只返回 visible=true 的工具
                tools.append(tool)
        
        # 也支持 .yml 扩展名
        for config_file in self.config_dir.glob("*.yml"):
            tool = self.load_tool(config_file)
            if tool and tool.visible:  # 只返回 visible=true 的工具
                tools.append(tool)
        
        # 更新缓存
        self._tools_cache = tools
        self._cache_timestamp = current_time
        
        return tools
    
    def get_tool_by_id(self, tool_id: str) -> Optional[Tool]:
        """
        根据 tool_id 获取指定的工具
        
        Args:
            tool_id: 工具唯一标识符
            
        Returns:
            Tool 实例，如果不存在返回 None
        """
        tools = self.load_all_tools()
        return next((t for t in tools if t.tool_id == tool_id), None)
    
    def load_category_config(self) -> Dict[str, Dict]:
        """
        加载分类配置文件
        
        Returns:
            分类配置字典，key 为分类名称，value 包含 order 和 icon
        """
        category_config_path = self.config_dir / "categories.yaml"
        category_config: Dict[str, Dict] = {}
        
        if category_config_path.exists():
            try:
                with open(category_config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                if config_data and 'categories' in config_data:
                    for cat in config_data['categories']:
                        category_name = cat.get('name', '')
                        if category_name:
                            category_config[category_name] = {
                                'order': cat.get('order', 999),
                                'icon': cat.get('icon')
                            }
            except Exception as e:
                logger.warning(f"加载分类配置失败: {category_config_path}, 错误: {e}")
        
        return category_config
    
    def group_by_category(self, tools: List[Tool]) -> List[Dict]:
        """
        按 category 聚合工具，生成分类结构，并按配置的顺序排序
        
        Args:
            tools: 工具列表
            
        Returns:
            分类列表，每个分类包含 name、icon（可选）、order、tools（已排序）
        """
        # 加载分类配置
        category_config = self.load_category_config()
        
        # 使用字典按 category 分组
        category_dict: Dict[str, Dict] = {}
        
        for tool in tools:
            category_name = tool.category
            if category_name not in category_dict:
                # 创建新分类
                cat_config = category_config.get(category_name, {})
                category_dict[category_name] = {
                    'name': category_name,
                    'icon': cat_config.get('icon') or tool.icon,  # 优先使用配置的图标
                    'order': cat_config.get('order', 999),  # 从配置获取，默认999
                    'tools': []
                }
            
            # 添加工具到分类
            category_dict[category_name]['tools'].append(tool)
        
        # 对每个分类内的工具按 order 排序
        for category in category_dict.values():
            category['tools'].sort(key=lambda t: t.order)
        
        # 转换为列表并按 order 排序
        categories = list(category_dict.values())
        categories.sort(key=lambda c: c['order'])
        
        return categories

