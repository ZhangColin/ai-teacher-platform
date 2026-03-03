#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用层服务扫描工具

扫描 Python 和 Java 的应用层服务，对比分析迁移完成度。

扫描目标：
- Python: backend/src/services/*_service.py
- Java: backend-java/src/main/java/**/application/service/*.java

输出格式：JSON 对比结果
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set


def scan_python_services(project_root: str) -> Dict[str, Dict]:
    """
    扫描 Python 应用层服务

    Args:
        project_root: 项目根目录

    Returns:
        服务信息字典 {服务名: {"methods": [...], "file": "..."}}
    """
    services_dir = Path(project_root) / "backend" / "src" / "services"

    if not services_dir.exists():
        print(f"警告: Python 服务目录不存在: {services_dir}")
        return {}

    services = {}

    # 扫描所有 *_service.py 文件
    for py_file in services_dir.glob("*_service.py"):
        # 跳过 __init__.py 和 __pycache__
        if py_file.name.startswith("__"):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取类名（例如: AIService, UserService）
            class_match = re.search(r'class\s+(\w+Service)\s*[:\(]', content)
            if not class_match:
                # 可能是特殊服务（如 artifact_parser, title_generator）
                class_match = re.search(r'class\s+(\w+)\s*[:\(]', content)

            if class_match:
                class_name = class_match.group(1)
            else:
                # 使用文件名作为类名
                class_name = py_file.stem.replace('_', ' ').title().replace(' ', '')

            # 提取所有公共方法
            methods = []
            method_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(', re.MULTILINE)

            for match in method_pattern.finditer(content):
                method_name = match.group(1)

                # 跳过私有方法
                if method_name.startswith('_'):
                    continue

                # 跳过特殊方法
                if method_name.startswith('__'):
                    continue

                methods.append(method_name)

            services[class_name] = {
                "methods": sorted(methods),
                "file": str(py_file.relative_to(project_root))
            }

        except Exception as e:
            print(f"警告: 读取文件失败 {py_file}: {e}")
            continue

    return services


def scan_java_services(project_root: str) -> Dict[str, Dict]:
    """
    扫描 Java 应用层服务

    Args:
        project_root: 项目根目录

    Returns:
        服务信息字典 {服务名: {"methods": [...], "file": "..."}}
    """
    service_dir = Path(project_root) / "backend-java" / "src" / "main" / "java"

    if not service_dir.exists():
        print(f"警告: Java 源码目录不存在: {service_dir}")
        return {}

    services = {}

    # 递归查找所有 application/service 目录下的 Java 文件
    for java_file in service_dir.rglob("*.java"):
        # 跳过测试文件
        if "test" in str(java_file):
            continue

        # 只处理 application/service 目录下的文件
        file_path = str(java_file).replace("\\", "/")
        if "/application/service/" not in file_path:
            continue

        try:
            with open(java_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取类名
            class_pattern = re.compile(r'public\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)')
            interface_pattern = re.compile(r'public\s+interface\s+(\w+)')

            class_match = class_pattern.search(content)
            interface_match = interface_pattern.search(content)

            if class_match:
                class_name = class_match.group(1)
            elif interface_match:
                class_name = interface_match.group(1)
            else:
                # 使用文件名
                class_name = java_file.stem

            # 提取所有公共方法
            methods = []
            method_pattern = re.compile(
                r'public\s+(?:static\s+)?(?:synchronized\s+)?(?:final\s+)?(?:<[^>]+>\s+)?\w+\s+(\w+)\s*\('
            )

            for match in method_pattern.finditer(content):
                method_name = match.group(1)

                # 跳过常见的方法
                skip_methods = {'main', 'equals', 'hashCode', 'toString', 'getClass'}
                if method_name in skip_methods:
                    continue

                methods.append(method_name)

            services[class_name] = {
                "methods": sorted(methods),
                "file": str(java_file.relative_to(project_root))
            }

        except Exception as e:
            print(f"警告: 读取文件失败 {java_file}: {e}")
            continue

    return services


def normalize_service_name(service_name: str, language: str) -> str:
    """
    规范化服务名称

    Args:
        service_name: 服务名称
        language: 语言类型

    Returns:
        规范化后的服务名称
    """
    # Python: 移除 _service 后缀
    if language == "python":
        if service_name.endswith("Service"):
            return service_name
        # 特殊服务
        return service_name

    # Java: 直接返回
    return service_name


def compare_services(python_services: Dict, java_services: Dict) -> Dict:
    """
    对比 Python 和 Java 服务

    Args:
        python_services: Python 服务字典
        java_services: Java 服务字典

    Returns:
        对比结果字典
    """
    # 规范化服务名称
    py_services = {
        normalize_service_name(name, "python"): info
        for name, info in python_services.items()
    }
    java_svcs = {
        normalize_service_name(name, "java"): info
        for name, info in java_services.items()
    }

    # 计算差异
    py_names = set(py_services.keys())
    java_names = set(java_svcs.keys())

    only_in_python = py_names - java_names
    only_in_java = java_names - py_names
    common = py_names & java_names

    # 构建详细对比
    detailed_comparison = {}

    for service_name in common:
        py_methods = set(py_services[service_name]["methods"])
        java_methods = set(java_svcs[service_name]["methods"])

        detailed_comparison[service_name] = {
            "python_methods": sorted(list(py_methods)),
            "java_methods": sorted(list(java_methods)),
            "only_in_python": sorted(list(py_methods - java_methods)),
            "only_in_java": sorted(list(java_methods - py_methods)),
            "common_methods": sorted(list(py_methods & java_methods)),
            "python_file": py_services[service_name]["file"],
            "java_file": java_svcs[service_name]["file"]
        }

    return {
        "layer": "application",
        "only_in_python": sorted(list(only_in_python)),
        "only_in_java": sorted(list(only_in_java)),
        "common": sorted(list(common)),
        "python_count": len(py_names),
        "java_count": len(java_names),
        "detailed_comparison": detailed_comparison
    }


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent

    print(f"项目根目录: {project_root}")
    print()

    # 扫描 Python 服务
    print("扫描 Python 应用层服务...")
    python_services = scan_python_services(str(project_root))
    print(f"  找到 {len(python_services)} 个服务:")
    for name in sorted(python_services.keys()):
        print(f"    - {name}: {len(python_services[name]['methods'])} 个方法")
    print()

    # 扫描 Java 服务
    print("扫描 Java 应用层服务...")
    java_services = scan_java_services(str(project_root))
    print(f"  找到 {len(java_services)} 个服务:")
    for name in sorted(java_services.keys()):
        print(f"    - {name}: {len(java_services[name]['methods'])} 个方法")
    print()

    # 对比分析
    print("对比分析...")
    result = compare_services(python_services, java_services)

    # 输出 JSON 结果
    json_output = json.dumps(result, ensure_ascii=False, indent=2)
    print()
    print("=" * 60)
    print("应用层对比结果（JSON格式）:")
    print("=" * 60)
    print(json_output)

    # 保存到文件
    output_file = project_root / "docs" / "plans" / "2026-03-03-backend-java-migration-verification" / "reports" / "application-layer-scan.json"
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
    print(f"  Python 服务: {result['python_count']} 个")
    print(f"  Java 服务: {result['java_count']} 个")
    print(f"  共同服务: {len(result['common'])} 个")
    print(f"  仅在 Python: {len(result['only_in_python'])} 个")
    print(f"  仅在 Java: {len(result['only_in_java'])} 个")

    if result['only_in_python']:
        print()
        print(f"  ⚠️  仅在 Python 中存在的服务: {', '.join(result['only_in_python'])}")

    if result['only_in_java']:
        print()
        print(f"  ⚠️  仅在 Java 中存在的服务: {', '.join(result['only_in_java'])}")

    # 打印方法对比详情
    if result['detailed_comparison']:
        print()
        print("=" * 60)
        print("方法对比详情:")
        print("=" * 60)
        for service_name, comparison in result['detailed_comparison'].items():
            print()
            print(f"  {service_name}:")
            print(f"    共同方法: {len(comparison['common_methods'])} 个")
            print(f"    仅 Python: {len(comparison['only_in_python'])} 个")
            print(f"    仅 Java: {len(comparison['only_in_java'])} 个")

            if comparison['only_in_python']:
                print(f"      Python 独有: {', '.join(comparison['only_in_python'][:5])}")
                if len(comparison['only_in_python']) > 5:
                    print(f"                    ... 还有 {len(comparison['only_in_python']) - 5} 个")

            if comparison['only_in_java']:
                print(f"      Java 独有: {', '.join(comparison['only_in_java'][:5])}")
                if len(comparison['only_in_java']) > 5:
                    print(f"                  ... 还有 {len(comparison['only_in_java']) - 5} 个")

    return result


if __name__ == "__main__":
    main()
