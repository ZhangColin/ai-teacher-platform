#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML 配置迁移到数据库脚本

将 configs/ 目录下的 YAML 配置文件迁移到数据库
"""
import sys
import yaml
import uuid
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

from sqlalchemy.orm import Session
from src.database import engine
from src.db_models import (
    NavigationModuleModel, NavigationModuleType,
    ToolsetModel, AIToolCategoryModel, AIToolModel, AIToolType
)


def load_yaml(file_path: Path) -> dict:
    """加载 YAML 文件"""
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def migrate_navigation(db: Session):
    """迁移导航模块配置"""
    print("迁移导航模块...")
    nav_file = project_root / "configs" / "navigation.yaml"
    nav_data = load_yaml(nav_file)

    if not nav_data or 'modules' not in nav_data:
        print("  警告: navigation.yaml 不存在或格式错误")
        return

    # 检查是否已有数据
    existing_count = db.query(NavigationModuleModel).count()
    if existing_count > 0:
        print(f"  发现 {existing_count} 个已存在的导航模块，跳过迁移")
        return

    for module_data in nav_data['modules']:
        module_type = NavigationModuleType.toolset if module_data.get('type') == 'toolset' else NavigationModuleType.page

        module = NavigationModuleModel(
            id=str(uuid.uuid4()),
            name=module_data.get('name', ''),
            type=module_type,
            config_source=module_data.get('config_source'),
            page_path=module_data.get('page_path'),
            icon=module_data.get('icon'),
            order=module_data.get('order', 0),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(module)

    db.commit()
    print(f"  迁移了 {len(nav_data['modules'])} 个导航模块")


def migrate_toolsets(db: Session):
    """迁移工具集配置"""
    print("迁移工具集...")
    tools_dir = project_root / "configs" / "tools"

    if not tools_dir.exists():
        print("  警告: tools 目录不存在")
        return {}

    toolset_map = {}  # toolset_id -> model id

    # 检查是否已有数据
    existing_count = db.query(ToolsetModel).count()
    if existing_count > 0:
        print(f"  发现 {existing_count} 个已存在的工具集，跳过迁移")
        # 获取现有工具集映射
        for toolset in db.query(ToolsetModel).all():
            toolset_map[toolset.toolset_id] = toolset.id
        return toolset_map

    for toolset_dir in tools_dir.iterdir():
        if not toolset_dir.is_dir():
            continue

        toolset_id = toolset_dir.name

        # 检查是否有工具配置文件
        yaml_files = list(toolset_dir.glob("*.yaml"))
        if not yaml_files:
            continue

        # 从导航配置获取名称，或使用默认值
        name_map = {
            'ai_tools': 'AI模型能力',
            'teaching_researcher': 'AI教研员智能体',
            'test_tools': '测试工具集'
        }
        name = name_map.get(toolset_id, toolset_id)

        toolset = ToolsetModel(
            id=str(uuid.uuid4()),
            toolset_id=toolset_id,
            name=name,
            icon=None,
            order=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(toolset)
        db.flush()  # 获取生成的 ID

        toolset_map[toolset_id] = toolset.id
        print(f"  迁移工具集: {toolset_id}")

    db.commit()
    return toolset_map


def migrate_categories(db: Session, toolset_map: dict):
    """迁移工具分类配置"""
    print("迁移工具分类...")
    tools_dir = project_root / "configs" / "tools"

    category_map = {}  # (toolset_id, category_name) -> model id

    for toolset_id, toolset_db_id in toolset_map.items():
        categories_file = tools_dir / toolset_id / "categories.yaml"
        categories_data = load_yaml(categories_file)

        if not categories_data or 'categories' not in categories_data:
            continue

        # 检查是否已有该工具集的分类
        existing_count = db.query(AIToolCategoryModel).filter(
            AIToolCategoryModel.toolset_id == toolset_db_id
        ).count()
        if existing_count > 0:
            print(f"  工具集 {toolset_id} 已有 {existing_count} 个分类，跳过")
            # 获取现有分类映射
            for category in db.query(AIToolCategoryModel).filter(
                AIToolCategoryModel.toolset_id == toolset_db_id
            ).all():
                category_map[(toolset_id, category.name)] = category.id
            continue

        for cat_data in categories_data['categories']:
            category = AIToolCategoryModel(
                id=str(uuid.uuid4()),
                toolset_id=toolset_db_id,
                name=cat_data.get('name', ''),
                icon=cat_data.get('icon'),
                order=cat_data.get('order', 0),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(category)
            db.flush()

            category_map[(toolset_id, cat_data.get('name', ''))] = category.id

    db.commit()
    print(f"  迁移了 {len(category_map)} 个分类")
    return category_map


def migrate_tools(db: Session, toolset_map: dict, category_map: dict):
    """迁移 AI 工具配置"""
    print("迁移 AI 工具...")
    tools_dir = project_root / "configs" / "tools"

    tool_count = 0

    for toolset_id, toolset_db_id in toolset_map.items():
        toolset_dir = tools_dir / toolset_id

        for yaml_file in toolset_dir.glob("*.yaml"):
            if yaml_file.name == 'categories.yaml':
                continue

            tool_data = load_yaml(yaml_file)
            if not tool_data:
                continue

            # 检查是否已存在相同的 tool_id
            existing_tool = db.query(AIToolModel).filter(
                AIToolModel.tool_id == tool_data.get('tool_id')
            ).first()
            if existing_tool:
                print(f"  工具 {tool_data.get('tool_id')} 已存在，跳过")
                continue

            # 获取分类 ID
            category_name = tool_data.get('category')
            category_id = category_map.get((toolset_id, category_name))

            # 处理系统提示词
            system_prompt = tool_data.get('system_prompt')
            system_prompt_file = tool_data.get('system_prompt_file')

            if system_prompt_file:
                prompt_file = toolset_dir / "prompts" / system_prompt_file
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        system_prompt = f.read()

            # 确定工具类型
            tool_type = AIToolType.media if tool_data.get('type') == 'media' else AIToolType.normal

            tool = AIToolModel(
                id=str(uuid.uuid4()),
                tool_id=tool_data.get('tool_id'),
                toolset_id=toolset_db_id,
                category_id=category_id,
                name=tool_data.get('name'),
                description=tool_data.get('description'),
                system_prompt=system_prompt,
                icon=tool_data.get('icon'),
                type=tool_type,
                content_type=tool_data.get('content_type'),
                media_type=tool_data.get('media_type'),
                model=tool_data.get('model'),
                welcome_message=tool_data.get('welcome_message'),
                visible=tool_data.get('visible', True),
                order=tool_data.get('order', 0),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(tool)
            tool_count += 1

        # 提交当前工具集的工具
        if tool_count > 0:
            db.commit()
            print(f"  工具集 {toolset_id} 迁移了 {tool_count} 个工具")
            tool_count = 0

    print(f"  总共迁移了 {tool_count} 个 AI 工具")


def main():
    """主函数"""
    print("=" * 50)
    print("开始 YAML 配置迁移")
    print("=" * 50)

    # 创建数据库会话
    with Session(engine) as db:
        # 迁移导航模块
        migrate_navigation(db)

        # 迁移工具集
        toolset_map = migrate_toolsets(db)

        # 迁移分类
        category_map = migrate_categories(db, toolset_map)

        # 迁移工具
        migrate_tools(db, toolset_map, category_map)

    print("=" * 50)
    print("迁移完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()