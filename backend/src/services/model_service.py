"""模型配置服务"""
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ModelInfo(BaseModel):
    """模型信息"""
    id: str  # 模型ID，格式：provider:model_name
    name: str  # 显示名称
    provider: str  # 服务商名称
    description: str  # 描述


class ModelService:
    """模型配置服务"""

    def __init__(self, config_path: str = None):
        """
        初始化模型服务

        Args:
            config_path: 模型配置文件路径（YAML）
        """
        if config_path is None:
            # 默认路径：项目根目录下的 configs/models.yaml
            # 从 backend/src/services/model_service.py 向上4级到项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / "configs" / "models.yaml"

        self.config_path = Path(config_path)
        self.models: List[ModelInfo] = []
        self._load_models()

    def _load_models(self):
        """从YAML文件加载模型配置"""
        try:
            if not self.config_path.exists():
                logger.warning(f"模型配置文件不存在: {self.config_path}")
                self.models = []
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not config_data or 'models' not in config_data:
                logger.warning(f"模型配置文件格式错误: {self.config_path}")
                self.models = []
                return

            # 解析模型列表
            self.models = [
                ModelInfo(
                    id=model_data['id'],
                    name=model_data['name'],
                    provider=model_data['provider'],
                    description=model_data.get('description', '')
                )
                for model_data in config_data['models']
            ]

            logger.info(f"✅ 成功加载 {len(self.models)} 个模型配置")

        except Exception as e:
            logger.error(f"❌ 加载模型配置失败: {e}")
            self.models = []

    def get_available_models(self) -> List[ModelInfo]:
        """获取所有可用的模型列表"""
        return self.models

    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """
        根据模型ID获取模型信息

        Args:
            model_id: 模型ID，格式：provider:model_name

        Returns:
            模型信息，如果不存在返回 None
        """
        for model in self.models:
            if model.id == model_id:
                return model
        return None

    def reload(self):
        """重新加载模型配置"""
        logger.info("🔄 重新加载模型配置...")
        self._load_models()
