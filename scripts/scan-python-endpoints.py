# scripts/scan-python-endpoints.py
import ast
import json
import sys
from pathlib import Path

def extract_fastapi_routes(file_path):
    """从 Python 文件中提取 FastAPI 路由"""
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"警告: 文件不存在: {file_path}", file=sys.stderr)
        return []

    routes = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError as e:
        print(f"警告: 无法解析文件 {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"警告: 读取文件失败 {file_path}: {e}", file=sys.stderr)
        return []

    # 查找 router 的 prefix
    router_prefix = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'router':
                    # 查找 APIRouter(prefix=...)
                    if isinstance(node.value, ast.Call):
                        for keyword in node.value.keywords:
                            if keyword.arg == 'prefix':
                                if isinstance(keyword.value, ast.Constant):
                                    router_prefix = keyword.value.value

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                # 检查 @app.get, @router.post 等
                if isinstance(decorator, ast.Call):
                    # 处理 decorator.func.attr 情况（如 router.get, app.post）
                    if hasattr(decorator.func, 'attr'):
                        method = decorator.func.attr.upper()
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            # 提取路径参数
                            path_arg = decorator.args[0] if decorator.args else None
                            if isinstance(path_arg, ast.Constant):
                                path = path_arg.value
                                # 组合 prefix 和 path
                                if path:
                                    full_path = (
                                        router_prefix.rstrip('/') + '/' +
                                        path.lstrip('/')
                                    )
                                else:
                                    full_path = router_prefix
                                full_path = full_path.rstrip('/') or full_path
                                routes.append({
                                    'method': method,
                                    'path': full_path,
                                    'function': node.name,
                                    'file': str(file_path)
                                })
                    # 处理 decorator.func.value.attr 情况（如某些嵌套调用）
                    elif hasattr(decorator.func, 'value') and hasattr(decorator.func.value, 'attr'):
                        if decorator.func.value.attr in ['router', 'app', 'api']:
                            method = decorator.func.attr.upper() if hasattr(decorator.func, 'attr') else None
                            if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                                path_arg = (
                                    decorator.args[0] if decorator.args else None
                                )
                                if isinstance(path_arg, ast.Constant):
                                    path = path_arg.value
                                    if path:
                                        full_path = (
                                            router_prefix.rstrip('/') + '/' +
                                            path.lstrip('/')
                                        )
                                    else:
                                        full_path = router_prefix
                                    full_path = full_path.rstrip('/') or full_path
                                    routes.append({
                                        'method': method,
                                        'path': full_path,
                                        'function': node.name,
                                        'file': str(file_path)
                                    })

    return routes

def scan_project(project_root):
    """扫描整个项目"""
    all_routes = []

    # 扫描 routers 和 interfaces 目录
    for pattern in ['src/routers/**/*.py', 'src/interfaces/**/*.py']:
        for file_path in Path(project_root).glob(pattern):
            if '__' not in str(file_path):
                routes = extract_fastapi_routes(file_path)
                all_routes.extend(routes)

    return all_routes

if __name__ == '__main__':
    backend_path = Path(__file__).parent.parent / 'backend'
    routes = scan_project(backend_path)

    # 按路径和方法去重
    unique_routes = {}
    for route in routes:
        key = f"{route['method']} {route['path']}"
        if key not in unique_routes:
            unique_routes[key] = route

    print(json.dumps(list(unique_routes.values()), indent=2, ensure_ascii=False))
