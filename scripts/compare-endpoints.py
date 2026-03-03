# scripts/compare-endpoints.py
import json
import sys
from pathlib import Path

def load_endpoints(json_file):
    """加载端点 JSON"""
    # 检查文件是否存在
    if not Path(json_file).exists():
        raise FileNotFoundError(f"端点文件不存在: {json_file}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 格式错误 in {json_file}: {e}")

def normalize_path(path):
    """标准化路径（移除路径参数的差异）"""
    if not path or path.strip() == '':
        return None
    # 将路径参数统一转换为 {param} 格式
    # 匹配 {toolId}, {tool_id} 等
    import re
    # 将驼峰式路径参数转换为下划线式
    path = re.sub(r'\{([a-z])([A-Z])', r'{\1_\2', path)
    path = re.sub(r'\{([a-z]+)([A-Z])([a-z]+)\}', r'{\1_\2\3}', path)
    # 再次处理可能的多驼峰情况
    path = path.lower()
    return path

def compare_endpoints(python_endpoints, java_endpoints):
    """对比两个端点列表"""
    python_set = set()
    for ep in python_endpoints:
        key = f"{ep['method']} {normalize_path(ep['path'])}"
        python_set.add(key)

    java_set = set()
    for ep in java_endpoints:
        key = f"{ep['method']} {normalize_path(ep['path'])}"
        java_set.add(key)

    # 找出差异
    only_in_python = python_set - java_set
    only_in_java = java_set - python_set
    common = python_set & java_set

    return {
        'only_in_python': sorted(list(only_in_python)),
        'only_in_java': sorted(list(only_in_java)),
        'common': sorted(list(common)),
        'python_count': len(python_set),
        'java_count': len(java_set),
        'coverage': f"{len(common) / len(python_set) * 100:.1f}%" if python_set else "N/A"
    }

def generate_markdown_report(result, output_file):
    """生成 Markdown 报告"""
    with open(output_file, 'w') as f:
        f.write('# API 端点对比报告\n\n')
        f.write(f"**生成时间**: {Path(__file__).stat().st_mtime}\n\n")

        f.write("## 总体统计\n\n")
        f.write(f"- **Python 端点数量**: {result['python_count']}\n")
        f.write(f"- **Java 端点数量**: {result['java_count']}\n")
        f.write(f"- **迁移覆盖率**: {result['coverage']}\n\n")

        f.write("## ✅ 共同端点\n\n")
        f.write(f"数量: {len(result['common'])}\n\n")
        for endpoint in result['common'][:10]:  # 只显示前10个
            f.write(f"- {endpoint}\n")
        if len(result['common']) > 10:
            f.write(f"- ... 还有 {len(result['common']) - 10} 个\n")

        f.write("\n## ❌ 仅在 Python 中（未迁移）\n\n")
        f.write(f"数量: {len(result['only_in_python'])}\n\n")
        for endpoint in result['only_in_python']:
            f.write(f"- {endpoint}\n")

        f.write("\n## ⚠️  仅在 Java 中（新增）\n\n")
        f.write(f"数量: {len(result['only_in_java'])}\n\n")
        for endpoint in result['only_in_java']:
            f.write(f"- {endpoint}\n")

if __name__ == '__main__':
    try:
        python_file = (
            sys.argv[1] if len(sys.argv) > 1 else 'python-endpoints.json'
        )
        java_file = (
            sys.argv[2] if len(sys.argv) > 2 else 'java-endpoints.json'
        )
        output_file = (
            sys.argv[3] if len(sys.argv) > 3 else 'endpoint-diff.md'
        )

        python_endpoints = load_endpoints(python_file)
        java_endpoints = load_endpoints(java_file)

        result = compare_endpoints(python_endpoints, java_endpoints)
        generate_markdown_report(result, output_file)

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 生成报告时发生异常: {e}", file=sys.stderr)
        sys.exit(1)
