# 测试数据库隔离方案

## 📋 问题背景

测试数据库和开发数据库必须严格分离，避免：
- ❌ 测试清空开发数据
- ❌ 测试污染开发数据
- ❌ 并发测试相互干扰

## 🎯 解决方案

### 1. 数据库隔离架构

```
┌─────────────────────────────────────────┐
│         开发环境                         │
│  DATABASE_URL = ai_teacher_platform     │
│  → 你的开发数据，不会被测试影响          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         测试环境                         │
│  DATABASE_URL = ai_teacher_platform_test│
│  → 独立测试数据库，随意操作              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         单元测试（内存模式）              │
│  sqlite:///:memory:                     │
│  → 超快速，每个测试独立数据库            │
└─────────────────────────────────────────┘
```

### 2. 首次设置（仅需一次）

#### Step 1: 创建测试数据库

```bash
cd backend
chmod +x scripts/setup_test_db.sh
./scripts/setup_test_db.sh
```

这个脚本会：
- ✅ 创建独立的测试数据库 `ai_teacher_platform_test`
- ✅ 运行数据库迁移
- ✅ 创建测试用户数据
- ✅ 保证不影响开发数据库

#### Step 2: 配置环境变量

测试环境配置文件：`backend/.env.test`

```bash
# 已自动创建，包含：
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_teacher_platform_test?charset=utf8mb4
JWT_SECRET_KEY=test-secret-key-for-testing-only
CURRENT_PROVIDER=mock
```

### 3. 运行测试

#### 单元测试（使用内存 SQLite）

```bash
cd backend

# 方式1：使用 --mock-db 标记
pytest tests/unit/ --mock-db

# 方式2：使用单元测试标记
pytest tests/unit/ -m unit

# 优点：
# ✅ 超快速（~1-2秒）
# ✅ 不需要外部数据库
# ✅ 测试完全隔离
```

#### 集成测试（使用 MySQL 测试数据库）

```bash
cd backend

# 自动加载 .env.test 配置
pytest tests/integration/

# 或手动指定环境变量
export DATABASE_URL="mysql+pymysql://root:password@localhost:3306/ai_teacher_platform_test?charset=utf8mb4"
pytest tests/integration/

# 优点：
# ✅ 真实环境
# ✅ 支持 MySQL 特有功能
# ✅ 与生产环境一致
```

#### 全部测试

```bash
# 单元测试 + 集成测试
pytest tests/ -v

# 查看覆盖率
pytest --cov=backend/src --cov-report=html
open htmlcov/index.html
```

### 4. 数据库清理

#### 自动清理

- **单元测试**：每个测试函数使用全新的内存数据库，测试结束自动销毁
- **集成测试**：使用 pytest-testdb 插件，每个测试事务自动回滚

#### 手动清理测试数据库（如需要）

```bash
# 完全重建测试数据库
cd backend
./scripts/setup_test_db.sh

# 或手动清理
mysql -u root -p -e "DROP DATABASE IF EXISTS ai_teacher_platform_test;"
```

### 5. 验证隔离效果

#### 检查测试数据库

```bash
mysql -u root -p -e "USE ai_teacher_platform_test; SELECT COUNT(*) FROM users;"
```

#### 检查开发数据库（应该为空或只有你的数据）

```bash
mysql -u root -p -e "USE ai_teacher_platform; SELECT COUNT(*) FROM users;"
```

### 6. 故障排查

#### 问题1: 测试数据库连接失败

```bash
# 检查 MySQL 是否运行
mysql -u root -p -e "SELECT 1;"

# 检查测试数据库是否存在
mysql -u root -p -e "SHOW DATABASES LIKE 'ai_teacher_platform_test';"

# 重新创建测试数据库
cd backend && ./scripts/setup_test_db.sh
```

#### 问题2: 测试污染了开发数据

```bash
# 检查当前使用的数据库
python -c "from src.database import get_db; print('DB:', get_db())"

# 确保测试使用正确的数据库
echo $DATABASE_URL
# 应该包含 ai_teacher_platform_test
```

#### 问题3: 测试运行缓慢

```bash
# 使用单元测试模式（内存 SQLite）
pytest tests/unit/ --mock-db

# 跳过集成测试
pytest tests/ -m "not integration"
```

## ✅ 隔离保证

| 场景 | 使用的数据库 | 是否影响开发数据 |
|------|------------|----------------|
| 单元测试 | `sqlite:///:memory:` | ✅ 完全不影响 |
| 集成测试 | `ai_teacher_platform_test` | ✅ 完全不影响 |
| 开发环境运行 | `ai_teacher_platform` | N/A |
| 生产环境 | `ai_teacher_platform` | N/A |

## 📝 最佳实践

1. **永远不要在代码中硬编码数据库连接**
   ```python
   # ❌ 错误
   DATABASE_URL = "mysql://...ai_teacher_platform..."

   # ✅ 正确
   DATABASE_URL = os.getenv("DATABASE_URL")
   ```

2. **运行测试前确认环境变量**
   ```bash
   # 查看当前数据库配置
   echo $DATABASE_URL
   ```

3. **CI/CD 中使用测试数据库**
   ```yaml
   # .github/workflows/test.yml
   env:
     DATABASE_URL: mysql+pymysql://root:${{ secrets.DB_PASSWORD }}@localhost:3306/ai_teacher_platform_test
   ```

## 🎉 总结

通过这个方案：

- ✅ **开发数据完全安全**：测试不会影响你的开发数据
- ✅ **测试快速可靠**：单元测试使用内存数据库，速度提升10倍
- ✅ **环境隔离**：开发、测试、生产完全分离
- ✅ **易于维护**：一键设置，自动清理
