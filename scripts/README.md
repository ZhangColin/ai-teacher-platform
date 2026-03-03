# 端点扫描工具使用说明

## 概述

本工具集用于自动扫描和对比 Python FastAPI 后端与 Java Spring Boot 后端的 API 端点，以验证迁移进度。

## 工具列表

### 1. scan-python-endpoints.py

扫描 Python FastAPI 后端的所有 API 端点。

**功能：**
- 使用 AST 解析 Python 文件
- 支持 `@router.get()`, `@router.post()` 等装饰器
- 自动提取 `APIRouter(prefix=...)` 前缀
- 支持 `async def` 和 `def` 函数定义

**输出格式：**
```json
[
  {
    "method": "GET",
    "path": "/api/v1/auth/me",
    "function": "get_me",
    "file": "/path/to/backend/src/.../auth.py"
  }
]
```

**使用方法：**
```bash
python3 scripts/scan-python-endpoints.py > python-endpoints.json
```

### 2. scan-java-endpoints.py

扫描 Java Spring Boot 后端的所有 API 端点。

**功能：**
- 使用正则表达式查找 `@GetMapping`, `@PostMapping` 等注解
- 自动提取类级别的 `@RequestMapping` 前缀
- 提取方法名和文件路径

**输出格式：**
```json
[
  {
    "method": "POST",
    "path": "/api/v1/auth/login",
    "function": "login",
    "file": "/path/to/backend-java/.../AuthController.java"
  }
]
```

**使用方法：**
```bash
python3 scripts/scan-java-endpoints.py > java-endpoints.json
```

### 3. compare-endpoints.py

对比两个端点列表并生成差异报告。

**功能：**
- 找出仅在 Python 中的端点（未迁移）
- 找出仅在 Java 中的端点（新增）
- 计算迁移覆盖率
- 生成 Markdown 格式的详细报告

**使用方法：**
```bash
# 使用默认文件名
python3 scripts/compare-endpoints.py

# 指定输入和输出文件
python3 scripts/compare-endpoints.py \
  python-endpoints.json \
  java-endpoints.json \
  endpoint-diff.md
```

**输出格式：**
- JSON 格式：对比结果统计
- Markdown 文件：详细的差异报告

## 快速开始

### 1. 扫描端点

```bash
# 扫描 Python 后端
python3 scripts/scan-python-endpoints.py > python-endpoints.json

# 扫描 Java 后端
python3 scripts/scan-java-endpoints.py > java-endpoints.json
```

### 2. 生成对比报告

```bash
python3 scripts/compare-endpoints.py \
  python-endpoints.json \
  java-endpoints.json \
  endpoint-diff.md
```

### 3. 查看报告

```bash
cat endpoint-diff.md
```

## 报告示例

```markdown
# API 端点对比报告

## 总体统计

- **Python 端点数量**: 69
- **Java 端点数量**: 10
- **迁移覆盖率**: 10.1%

## ✅ 共同端点

数量: 7

- GET /api/v1/auth/me
- POST /api/v1/auth/login
- ...

## ❌ 仅在 Python 中（未迁移）

数量: 62

- POST /api/v1/admin/users
- PATCH /api/v1/admin/users/{user_id}
- ...

## ⚠️  仅在 Java 中（新增）

数量: 3

- GET /api/v1/common-tools/{tool_id}
- ...
```

## 注意事项

1. **路径前缀处理**
   - Python: 扫描器会提取 `APIRouter(prefix=...)` 和 `app.include_router(..., prefix=...)`
   - Java: 扫描器会提取 `@RequestMapping` 类级别注解

2. **路径参数标准化**
   - 对比时会将路径参数统一为小写格式
   - 例如：`{toolId}` 和 `{tool_id}` 会被识别为相同端点

3. **文件编码**
   - 所有脚本使用 UTF-8 编码
   - 确保源代码文件也是 UTF-8 编码

4. **权限要求**
   - 脚本需要读取 backend 和 backend-java 目录的权限
   - 生成的报告文件需要有写入权限

## 技术细节

### Python 扫描器实现

- 使用 `ast` 模块解析 Python 代码
- 查找 `AsyncFunctionDef` 和 `FunctionDef` 节点
- 识别装饰器调用：`@router.get()`, `@app.post()` 等
- 提取 `APIRouter(prefix=...)` 参数

### Java 扫描器实现

- 使用正则表达式查找注解
- 模式：`@(Get|Post|Put|Delete|Patch)Mapping("path")`
- 查找 `@RequestMapping` 类级别前缀
- 提取公共方法签名

### 对比算法

1. 将端点标准化为 `{METHOD} {path}` 格式
2. 使用集合运算找出差异
3. 计算覆盖率：`共同端点 / Python端点总数`

## 故障排除

### 问题：扫描结果为空

**可能原因：**
- 路径不正确
- 文件权限问题

**解决方案：**
```bash
# 检查目录是否存在
ls backend/src/routers/
ls backend-java/src/main/java/**/rest/

# 检查文件权限
ls -la backend/src/routers/*.py
```

### 问题：对比报告中的路径参数不匹配

**可能原因：**
- Java 使用驼峰命名：`{toolId}`
- Python 使用下划线命名：`{tool_id}`

**解决方案：**
对比脚本会自动标准化路径参数，但如果仍有问题，可以手动调整 `normalize_path()` 函数。

### 问题：覆盖率计算不准确

**可能原因：**
- 路径前缀不一致
- 端点重复定义

**解决方案：**
检查扫描器输出，确保路径前缀正确。使用 `jq` 工具检查 JSON：
```bash
jq '.[] | .path' python-endpoints.json | sort -u
```

## 扩展使用

### 集成到 CI/CD

可以将扫描工具集成到持续集成流程中：

```yaml
# .github/workflows/endpoint-check.yml
- name: 扫描端点
  run: |
    python3 scripts/scan-python-endpoints.py > python.json
    python3 scripts/scan-java-endpoints.py > java.json
    python3 scripts/compare-endpoints.py python.json java.json report.md

- name: 检查覆盖率
  run: |
    COVERAGE=$(jq -r '.coverage' result.json | sed 's/%//')
    if (( $(echo "$COVERAGE < 80" | bc -l) )); then
      echo "覆盖率不足 80%: $COVERAGE%"
      exit 1
    fi
```

### 自定义扫描路径

编辑脚本文件，修改扫描路径：

```python
# scan-python-endpoints.py
for pattern in ['src/routers/**/*.py', 'src/interfaces/**/*.py']:
    # 添加自定义路径
    for file_path in Path(project_root).glob(pattern):
        ...
```

## 维护

- 定期更新扫描器以支持新的路由定义方式
- 添加更多 HTTP 方法的支持（如 `HEAD`, `OPTIONS`）
- 改进路径参数标准化算法

## 联系方式

如有问题或建议，请联系开发团队。
