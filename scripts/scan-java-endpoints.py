# scripts/scan-java-endpoints.py
import re
import json
import sys
from pathlib import Path

def extract_spring_routes(file_path):
    """从 Java 文件中提取 Spring MVC 路由"""
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"警告: 文件不存在: {file_path}", file=sys.stderr)
        return []

    routes = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"警告: 读取文件失败 {file_path}: {e}", file=sys.stderr)
        return []

    # 查找类级别的 @RequestMapping
    class_prefix_pattern = r'@RequestMapping\(["\']([^"\']+)["\']'
    class_prefix_match = re.search(class_prefix_pattern, content)
    class_prefix = class_prefix_match.group(1) if class_prefix_match else ''

    # 查找 @GetMapping, @PostMapping 等
    mapping_pattern = r'@(Get|Post|Put|Delete|Patch)Mapping\(["\']([^"\']+)["\']'
    for match in re.finditer(mapping_pattern, content):
        method = match.group(1).upper()
        path = match.group(2)

        # 查找方法名
        func_pattern = r'public\s+\w+\s+(\w+)\s*\('
        func_match = re.search(func_pattern, content[match.end():match.end()+200])
        func_name = func_match.group(1) if func_match else 'unknown'

        # 组合类级别前缀和方法路径
        full_path = class_prefix.rstrip('/') + '/' + path.lstrip('/') if path else class_prefix
        full_path = full_path.rstrip('/') or full_path

        routes.append({
            'method': method,
            'path': full_path,
            'function': func_name,
            'file': str(file_path)
        })

    return routes

def scan_project(project_root):
    """扫描整个项目"""
    all_routes = []

    # 扫描 interfaces/rest 目录
    for file_path in Path(project_root).glob('src/main/java/**/rest/*.java'):
        routes = extract_spring_routes(file_path)
        all_routes.extend(routes)

    return all_routes

if __name__ == '__main__':
    backend_path = Path(__file__).parent.parent / 'backend-java'
    routes = scan_project(backend_path)

    # 按路径和方法去重
    unique_routes = {}
    for route in routes:
        key = f"{route['method']} {route['path']}"
        if key not in unique_routes:
            unique_routes[key] = route

    print(json.dumps(list(unique_routes.values()), indent=2, ensure_ascii=False))
