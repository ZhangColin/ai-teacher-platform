#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
领域层扫描工具

扫描 Python 和 Java 的领域层实体，对比分析迁移完成度。

扫描目标：
- Python: backend/src/domain/entities/*.py
- Java: backend-java/src/main/java/**/domain/**/*.java

输出格式：JSON 对比结果
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set


def scan_python_entities(project_root: str) -> Set[str]:
    """
    扫描 Python 领域层实体

    Args:
        project_root: 项目根目录

    Returns:
        实体类名集合（不含.py后缀）
    """
    entities_dir = Path(project_root) / "backend" / "src" / "domain" / "entities"

    if not entities_dir.exists():
        print(f"警告: Python 实体目录不存在: {entities_dir}")
        return set()

    entities = set()

    for py_file in entities_dir.glob("*.py"):
        # 跳过 __init__.py 和 __pycache__
        if py_file.name.startswith("__"):
            continue

        # 提取类名（文件名转驼峰）
        # 例如: user.py -> User
        # 例如: artifact.py -> Artifact
        class_name = py_file.stem.capitalize()

        # 特殊处理：session.py -> Session（首字母已大写）
        # 例如: message.py -> Message
        entities.add(class_name)

    return entities


def scan_java_entities(project_root: str) -> Set[str]:
    """
    扫描 Java 领域层实体

    Args:
        project_root: 项目根目录

    Returns:
        实体类名集合（不含包名）
    """
    domain_dir = Path(project_root) / "backend-java" / "src" / "main" / "java"

    if not domain_dir.exists():
        print(f"警告: Java 源码目录不存在: {domain_dir}")
        return set()

    entities = set()
    # 修改正则以匹配带注解的类定义（如 @Data, @Entity 等）
    domain_pattern = re.compile(r'class\s+(\w+)')
    abstract_pattern = re.compile(r'abstract\s+class\s+(\w+)')
    enum_pattern = re.compile(r'enum\s+(\w+)')
    interface_pattern = re.compile(r'interface\s+(\w+)')

    # 递归查找所有 domain 目录下的 Java 文件
    for java_file in domain_dir.rglob("*.java"):
        # 跳过测试文件
        if "test" in str(java_file):
            continue

        # 只处理 domain 目录下的文件
        if "/domain/" not in str(java_file).replace("\\", "/"):
            continue

        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # 跳过 Abstract 类
                if abstract_pattern.search(content):
                    continue

                # 跳过枚举类
                if enum_pattern.search(content):
                    continue

                # 跳过接口
                if interface_pattern.search(content):
                    continue

                # 查找类定义（支持带注解的情况）
                match = domain_pattern.search(content)
                if match:
                    class_name = match.group(1)
                    entities.add(class_name)

        except Exception as e:
            print(f"警告: 读取文件失败 {java_file}: {e}")
            continue

    return entities


def normalize_entity_names(entities: Set[str], language: str) -> Set[str]:
    """
    规范化实体名称，便于对比

    Args:
        entities: 原始实体名称集合
        language: 语言类型（"python" 或 "java"）

    Returns:
        规范化后的实体名称集合
    """
    normalized = set()

    # 常见的命名映射（Python -> Java）
    mappings = {
        # 完全匹配
        "User": "User",
        "Session": "Session",
        "Message": "Message",
        "Artifact": "Artifact",
        "Tool": "Tool",
    }

    for entity in entities:
        if language == "python":
            normalized.add(entity)
        else:  # Java
            normalized.add(entity)

    return normalized


def compare_entities(python_entities: Set[str], java_entities: Set[str]) -> Dict:
    """
    对比 Python 和 Java 实体

    Args:
        python_entities: Python 实体集合
        java_entities: Java 实体集合

    Returns:
        对比结果字典
    """
    # 规范化名称
    py_entities = normalize_entity_names(python_entities, "python")
    java_entities = normalize_entity_names(java_entities, "java")

    # 计算差异
    only_in_python = py_entities - java_entities
    only_in_java = java_entities - py_entities
    common = py_entities & java_entities

    return {
        "layer": "domain",
        "only_in_python": sorted(list(only_in_python)),
        "only_in_java": sorted(list(only_in_java)),
        "common": sorted(list(common)),
        "python_count": len(py_entities),
        "java_count": len(java_entities)
    }


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    print(f"项目根目录: {project_root}")
    print()

    # 扫描 Python 实体
    print("扫描 Python 领域层实体...")
    python_entities = scan_python_entities(str(project_root))
    print(f"  找到 {len(python_entities)} 个实体: {sorted(python_entities)}")
    print()

    # 扫描 Java 实体
    print("扫描 Java 领域层实体...")
    java_entities = scan_java_entities(str(project_root))
    print(f"  找到 {len(java_entities)} 个实体: {sorted(java_entities)}")
    print()

    # 对比分析
    print("对比分析...")
    result = compare_entities(python_entities, java_entities)

    # 输出 JSON 结果
    json_output = json.dumps(result, ensure_ascii=False, indent=2)
    print()
    print("=" * 60)
    print("领域层对比结果（JSON格式）:")
    print("=" * 60)
    print(json_output)

    # 保存到文件
    output_file = project_root / "docs" / "plans" / "2026-03-03-backend-java-migration-verification" / "reports" / "domain-layer-scan.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)

    print()
    print(f"结果已保存到: {output_file}")

    # 打印摘要
    print()
    print("=" * 60)
    print("摘要:")
    print("=" * 60)
    print(f"  Python 实体: {result['python_count']} 个")
    print(f"  Java 实体: {result['java_count']} 个")
    print(f"  共同实体: {len(result['common'])} 个")
    print(f"  仅在 Python: {len(result['only_in_python'])} 个")
    print(f"  仅在 Java: {len(result['only_in_java'])} 个")

    if result['only_in_python']:
        print()
        print(f"  ⚠️  仅在 Python 中存在的实体: {', '.join(result['only_in_python'])}")

    if result['only_in_java']:
        print()
        print(f"  ⚠️  仅在 Java 中存在的实体: {', '.join(result['only_in_java'])}")

    return result


if __name__ == "__main__":
    main()
