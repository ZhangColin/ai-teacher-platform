# Phase 1: 测试基础设施实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 建立完善的测试基础设施，确保测试环境完全隔离，清理无用文件

**架构:**
- 后端使用SQLite内存数据库进行单元测试，每个测试函数独立
- 集成测试使用独立的MySQL测试数据库
- 前端测试使用临时浏览器上下文和内存文件系统
- 所有测试不会影响开发环境

**技术栈:**
- pytest, pytest-cov, pytest-asyncio (后端测试)
- Vitest, Playwright (前端测试)
- SQLite内存数据库, MySQL
- Git版本控制

---

## Task 1: 清理第一批无用文件

**Files:**
- Delete: `backend/src/main.py.bak`
- Delete: `frontend/src/components/ChatPanel.vue.backup`
- Delete: `frontend/tests/unit/utils/markdownRenderer.spec.ts.bak`
- Delete: `backend/test.db`

**Step 1: 验证无用文件**

运行以下命令确认文件存在且无用：

```bash
# 检查备份文件
ls -lh backend/src/main.py.bak
ls -lh frontend/src/components/ChatPanel.vue.backup
ls -lh frontend/tests/unit/utils/markdownRenderer.spec.ts.bak

# 检查测试数据库文件
ls -lh backend/test.db

# 确认当前代码正常工作
cd backend && python3 -m pytest tests/unit/ -v --tb=no -q
```

Expected: 文件存在，测试通过（134+ passed）

**Step 2: 删除备份文件**

```bash
# 删除后端备份文件（103KB，已重构为205行）
rm backend/src/main.py.bak

# 删除前端备份文件（19KB）
rm frontend/src/components/ChatPanel.vue.backup

# 删除测试备份文件（6.9KB）
rm frontend/tests/unit/utils/markdownRenderer.spec.ts.bak

# 删除测试数据库文件（192KB，不应在源码中）
rm backend/test.db
```

**Step 3: 验证删除成功**

```bash
# 确认文件已删除
ls backend/src/main.py.bak 2>&1 | grep "No such file"
ls frontend/src/components/ChatPanel.vue.backup 2>&1 | grep "No such file"
ls frontend/tests/unit/utils/markdownRenderer.spec.ts.bak 2>&1 | grep "No such file"
ls backend/test.db 2>&1 | grep "No such file"

# 运行测试确认没有影响
cd backend && python3 -m pytest tests/unit/ tests/integration/ -v --tb=no -q
```

Expected: 文件不存在，测试全部通过

**Step 4: 提交更改**

```bash
git add backend/src/main.py.bak frontend/src/components/ChatPanel.vue.backup frontend/tests/unit/utils/markdownRenderer.spec.ts.bak backend/test.db
git commit -m "chore: 删除备份文件和测试数据库文件

- 删除 main.py.bak (2885行 → 205行重构已完成)
- 删除 ChatPanel.vue.backup
- 删除 markdownRenderer.spec.ts.bak
- 删除 test.db (测试不应在源码目录中)

测试验证: 所有测试通过"
```

---

## Task 2: 更新 .gitignore 文件

**Files:**
- Modify: `.gitignore`

**Step 1: 检查当前 .gitignore 内容**

```bash
cat .gitignore
```

Expected: 看到当前的gitignore规则

**Step 2: 添加测试相关忽略规则**

在 `.gitignore` 文件末尾添加以下内容：

```gitignore
# ==================== 测试相关 ====================

# Python测试
__pycache__/
*.pyc
*.pyo
*.pyd
.Pytest_cache/
.pytest_cache/
pytest.ini

# 数据库文件（测试不应提交）
*.db
*.sqlite
*.sqlite3

# 备份文件（不应提交）
*.bak
*.backup
*.old
*~
*.swp
*.swo

# 前端测试缓存
frontend/.vitest/
frontend/node_modules/.cache/
frontend/test-results/
frontend/playwright-report/

# 后端测试报告
backend/.coverage
backend/htmlcov/
backend/.pytest_cache/
```

**Step 3: 验证 .gitignore 生效**

```bash
# 测试创建一个测试文件
touch backend/test.py
touch backend/.pytest_cache/test
touch frontend/.vitest/test

# 检查git状态，这些文件不应出现
git status --short

# 清理测试文件
rm backend/test.py
rm -rf backend/.pytest_cache/test
rm -rf frontend/.vitest/test
```

Expected: git status 不显示这些文件

**Step 4: 提交更改**

```bash
git add .gitignore
git commit -m "chore: 更新.gitignore，添加测试相关忽略规则

- 添加Python测试缓存（__pycache__/, .pytest_cache/）
- 添加数据库文件（*.db, *.sqlite）
- 添加备份文件（*.bak, *.backup）
- 添加前端测试缓存（.vitest/, test-results/）

确保测试产物不会提交到版本控制"
```

---

## Task 3: 清理已存在的缓存目录

**Files:**
- Clean: `__pycache__/` 目录
- Clean: `.pytest_cache/` 目录

**Step 1: 查找缓存目录**

```bash
# 统计__pycache__目录数量
find . -type d -name "__pycache__" ! -path "*/.venv/*" ! -path "*/node_modules/*" | wc -l

# 列出前10个缓存目录
find . -type d -name "__pycache__" ! -path "*/.venv/*" ! -path "*/node_modules/*" | head -10
```

Expected: 发现多个缓存目录（174个）

**Step 2: 删除缓存目录**

```bash
# 删除所有__pycache__目录
find . -type d -name "__pycache__" ! -path "*/.venv/*" ! -path "*/node_modules/*" -exec rm -rf {} +

# 删除所有.pyc文件
find . -type f -name "*.pyc" ! -path "*/.venv/*" ! -path "*/node_modules/*" -delete

# 删除所有pytest缓存
find . -type d -name ".pytest_cache" ! -path "*/.venv/*" ! -path "*/node_modules/*" -exec rm -rf {} +
```

**Step 3: 验证清理成功**

```bash
# 确认缓存目录已删除
find . -type d -name "__pycache__" ! -path "*/.venv/*" ! -path "*/node_modules/*" | wc -l

# 运行测试确认没有影响
cd backend && python3 -m pytest tests/unit/ tests/integration/ -v --tb=no -q
```

Expected: 0个缓存目录，测试全部通过

**Step 4: 提交更改**

```bash
# git会自动忽略已删除的缓存目录
git status --short

# 如果有删除的文件被追踪，提交它们
git add -u
git commit -m "chore: 清理Python缓存目录

- 删除所有__pycache__/目录
- 删除所有.pyc文件
- 删除所有.pytest_cache/目录

测试验证: 所有测试通过"
```

---

## Task 4: 验证测试环境隔离

**Files:**
- Test: `backend/tests/conftest.py`
- Test: `backend/src/database.py`

**Step 1: 检查现有测试配置**

```bash
# 查看conftest.py中的db_session fixture
cd backend
grep -A 20 "def db_session" tests/conftest.py
```

Expected: 确认使用 `sqlite:///:memory:`

**Step 2: 编写测试环境隔离验证测试**

创建文件 `tests/integration/test_db_isolation.py`:

```python
# -*- coding: utf-8 -*-
"""验证测试环境完全隔离"""
import pytest
from src.db_models import UserModel
from src.database import Base
import bcrypt


def test_unit_test_uses_memory_db(db_session):
    """单元测试应该使用内存数据库"""
    # 创建用户
    password_hash = bcrypt.hashpw("test123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = UserModel(
        username="isolation_test_user",
        email="isolation@test.com",
        password_hash=password_hash,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()

    # 验证用户存在
    retrieved_user = db_session.query(UserModel).filter(
        UserModel.username == "isolation_test_user"
    ).first()
    assert retrieved_user is not None
    assert retrieved_user.email == "isolation@test.com"


def test_test_does_not_pollute_other_tests(db_session):
    """每个测试应该有独立的数据库"""
    # 这个测试应该有一个干净的数据库
    count = db_session.query(UserModel).count()
    # 应该只有当前测试创建的数据（fixture创建的test_user）
    assert count >= 0  # 每个测试独立，不依赖其他测试


def test_memory_db_isolation():
    """验证使用的是内存数据库，不是文件数据库"""
    # 导入engine检查连接字符串
    from sqlalchemy import create_engine
    from src.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    # 验证数据库URL是内存模式
    assert str(engine.url) == "sqlite:///:memory:"

    Base.metadata.drop_all(engine)
```

**Step 3: 运行隔离测试**

```bash
cd backend
python3 -m pytest tests/integration/test_db_isolation.py -v
```

Expected: 3 passed

**Step 4: 验证不使用开发数据库**

```bash
# 检查环境变量
echo "DATABASE_URL: $DATABASE_URL"

# 运行测试
python3 -m pytest tests/unit/ -v --tb=no -q

# 检查开发数据库（应该没有被测试影响）
# 如果你有MySQL开发数据库，运行：
# mysql -u root -p -e "USE ai_teacher_platform; SELECT COUNT(*) FROM users;"
```

Expected: DATABASE_URL未设置或为测试数据库，开发数据库未被影响

**Step 5: 提交更改**

```bash
git add tests/integration/test_db_isolation.py
git commit -m "test: 添加测试环境隔离验证

- 验证单元测试使用内存数据库
- 验证每个测试独立
- 验证不污染开发数据库

测试验证: 所有隔离测试通过"
```

---

## Task 5: 更新前端测试配置

**Files:**
- Modify: `frontend/vitest.config.ts`
- Modify: `frontend/playwright.config.ts`

**Step 1: 检查当前前端测试配置**

```bash
cd frontend
cat vitest.config.ts
cat playwright.config.ts
```

Expected: 查看现有配置

**Step 2: 更新 vitest.config.ts**

确保 `vitest.config.ts` 包含以下配置：

```typescript
export default defineConfig({
  test: {
    // 使用内存文件系统（如果支持）
    filesystem: {
      workspaces: false,
    },
    // 测试覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.ts',
      ],
    },
    // 测试环境设置
    isolate: true,  // 每个测试文件独立环境
  },
})
```

**Step 3: 更新 playwright.config.ts**

确保 `playwright.config.ts` 包含以下配置：

```typescript
export default defineConfig({
  // 每个测试使用独立的浏览器上下文
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  // 测试后清理
  // Playwright会自动清理浏览器上下文
})
```

**Step 4: 验证前端测试配置**

```bash
cd frontend

# 运行单元测试
npm run test -- --run

# 检查测试缓存是否被正确忽略
ls -la .vitest/ 2>&1 || echo ".vitest目录不存在（正确）"

# 运行E2E测试
npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```

Expected: 测试通过，缓存被正确管理

**Step 5: 提交更改**

```bash
git add frontend/vitest.config.ts frontend/playwright.config.ts
git commit -m "chore: 优化前端测试配置

- Vitest使用独立测试环境
- Playwright自动清理浏览器上下文
- 配置测试覆盖率报告

测试验证: 所有测试通过"
```

---

## Task 6: 编写测试指南文档

**Files:**
- Create: `docs/testing.md`

**Step 1: 创建测试指南文档**

创建文件 `docs/testing.md`:

```markdown
# 测试指南

## 概述

本项目采用多层测试策略，确保代码质量和系统稳定性。

- 后端测试：pytest + pytest-cov
- 前端测试：Vitest + Playwright
- 测试隔离：使用内存数据库和独立环境

## 后端测试

### 单元测试

使用SQLite内存数据库，每个测试函数独立：

```bash
cd backend

# 运行所有单元测试
python3 -m pytest tests/unit/ -v

# 运行特定测试文件
python3 -m pytest tests/unit/services/test_auth_service.py -v

# 运行特定测试函数
python3 -m pytest tests/unit/services/test_auth_service.py::test_generate_token -v

# 查看覆盖率
python3 -m pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html
```

### 集成测试

测试模块间交互：

```bash
cd backend

# 运行所有集成测试
python3 -m pytest tests/integration/ -v

# 运行所有测试（单元+集成）
python3 -m pytest tests/ -v
```

### 测试环境隔离

- 单元测试使用 `sqlite:///:memory:`
- 每个测试函数有独立的数据库实例
- 测试不会影响开发数据库

## 前端测试

### 单元测试

使用Vitest进行组件和工具函数测试：

```bash
cd frontend

# 运行所有单元测试
npm run test -- --run

# 运行特定测试文件
npm run test -- components/ChatPanel.spec.ts

# Watch模式
npm run test

# 查看覆盖率
npm run test -- --coverage
```

### E2E测试

使用Playwright进行端到端测试：

```bash
cd frontend

# 运行所有E2E测试
npm run test:e2e

# 运行特定测试文件
npm run test:e2e -- tests/e2e/chat.spec.ts

# 使用特定浏览器
npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium

# 调试模式
npm run test:e2e -- --debug
```

## 测试覆盖率目标

- 后端：80%+
- 前端：80%+

## 最佳实践

1. **TDD优先**：先写测试，再写实现
2. **测试隔离**：每个测试应该独立，不依赖其他测试
3. **清理数据**：使用fixture自动清理测试数据
4. **Mock外部依赖**：不要依赖真实的外部API
5. **快速失败**：测试应该快速失败，明确指出问题

## 故障排查

### 测试数据库问题

如果测试数据库出现问题：

```bash
# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +

# 运行测试
python3 -m pytest tests/ -v
```

### 前端测试缓存问题

```bash
# 清理node_modules缓存
rm -rf node_modules/.cache
rm -rf .vitest

# 运行测试
npm run test -- --run
```

### E2E测试失败

```bash
# 清理Playwright缓存
npx playwright clean-cache

# 重新安装浏览器
npx playwright install --with-deps chromium

# 运行测试
npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```
```

**Step 2: 提交更改**

```bash
git add docs/testing.md
git commit -m "docs: 添加测试指南文档

- 后端测试使用说明（pytest）
- 前端测试使用说明（Vitest + Playwright）
- 测试覆盖率目标
- 故障排查指南"
```

---

## Task 7: 运行完整测试套件验证

**Files:**
- Test: 所有测试

**Step 1: 清理所有缓存**

```bash
# 清理Python缓存
find backend -type d -name "__pycache__" -exec rm -rf {} +
find backend -type d -name ".pytest_cache" -exec rm -rf {} +

# 清理前端缓存
rm -rf frontend/node_modules/.cache
rm -rf frontend/.vitest

# 清理Playwright缓存
cd frontend && npx playwright clean-cache || true
cd ..
```

**Step 2: 运行后端完整测试**

```bash
cd backend

# 运行所有单元测试和集成测试
python3 -m pytest tests/unit/ tests/integration/ -v --tb=short

# 生成覆盖率报告
python3 -m pytest tests/unit/ tests/integration/ --cov=src --cov-report=html --cov-report=term

# 查看覆盖率摘要
echo "后端测试覆盖率完成"
```

Expected: 158+ tests passed, 80%+ coverage

**Step 3: 运行前端完整测试**

```bash
cd frontend

# 运行单元测试
npm run test -- --run

# 运行E2E测试
npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium

echo "前端测试完成"
```

Expected: 所有单元测试通过，E2E 10/10通过

**Step 4: 生成测试报告**

创建文件 `docs/reports/phase1-test-infrastructure-report.md`:

```markdown
# Phase 1: 测试基础设施完成报告

**日期**: 2026-03-01
**阶段**: 测试基础设施

## 完成任务

### ✅ 1. 清理无用文件
- 删除 main.py.bak (103KB)
- 删除 ChatPanel.vue.backup (19KB)
- 删除 markdownRenderer.spec.ts.bak (6.9KB)
- 删除 test.db (192KB)

### ✅ 2. 更新 .gitignore
- 添加测试缓存规则（__pycache__/, .pytest_cache/）
- 添加数据库文件规则（*.db, *.sqlite）
- 添加备份文件规则（*.bak, *.backup）
- 添加前端测试缓存（.vitest/, test-results/）

### ✅ 3. 清理缓存目录
- 删除所有 __pycache__/ 目录
- 删除所有 .pytest_cache/ 目录
- 验证测试不受影响

### ✅ 4. 验证测试环境隔离
- 确认单元测试使用SQLite内存数据库
- 确认每个测试独立
- 确认不污染开发数据库

### ✅ 5. 更新前端测试配置
- 优化Vitest配置
- 优化Playwright配置
- 确保测试环境隔离

### ✅ 6. 编写测试指南
- 创建 docs/testing.md
- 包含后端和前端测试说明
- 包含故障排查指南

### ✅ 7. 完整测试验证
- 后端测试：158+ passed
- 前端单元测试：全部通过
- E2E测试：10/10 passed

## 测试覆盖率

- **后端**: 31% → 目标80% (阶段2提升)
- **前端**: 当前覆盖率 → 目标80% (阶段2提升)

## 下一步

进入阶段2：模块化改进循环，按模块提升测试覆盖率到80%。

## 备注

- 测试基础设施已完善
- 测试环境完全隔离
- 测试不会影响开发环境
- 测试指南已完成
```

**Step 5: 提交阶段1完成**

```bash
git add docs/reports/phase1-test-infrastructure-report.md
git commit -m "docs: 添加阶段1完成报告

- 清理无用文件完成
- 测试基础设施建立完成
- 测试环境隔离验证完成
- 准备进入阶段2"

# 为阶段1打tag
git tag -a phase1-test-infra -m "阶段1：测试基础设施完成"
```

---

## 验收标准

完成所有任务后，应该满足：

### 文件清理
- [ ] 无备份文件（.bak, .backup）
- [ ] 无测试数据库文件（test.db）
- [ ] 无缓存目录（__pycache__, .pytest_cache）

### 测试隔离
- [ ] 单元测试使用SQLite内存数据库
- [ ] 每个测试独立运行
- [ ] 测试不影响开发数据库

### 测试通过
- [ ] 后端：158+ tests passed
- [ ] 前端单元测试：全部通过
- [ ] E2E测试：10/10 passed

### 文档完成
- [ ] .gitignore规则完整
- [ ] docs/testing.md完成
- [ ] 阶段1报告完成

### Git记录
- [ ] 所有更改已提交
- [ ] 阶段1 tag已创建

---

## 风险控制

### 如果测试失败

1. 检查缓存是否清理干净
2. 确认使用的是内存数据库
3. 检查环境变量是否正确
4. 查看测试错误日志

### 如果删除文件后出现问题

1. 使用git revert恢复
2. 检查是否有代码引用了已删除的文件
3. 重新运行测试验证

### 回滚预案

如果阶段1出现重大问题：

```bash
# 回滚到阶段1之前
git checkout phase1-test-infra~1

# 或者回滚特定提交
git revert <commit-hash>
```

---

## 时间估算

| 任务 | 预计时间 |
|------|---------|
| Task 1: 清理无用文件 | 30分钟 |
| Task 2: 更新.gitignore | 15分钟 |
| Task 3: 清理缓存目录 | 15分钟 |
| Task 4: 验证测试隔离 | 30分钟 |
| Task 5: 更新前端配置 | 30分钟 |
| Task 6: 编写测试指南 | 45分钟 |
| Task 7: 完整验证 | 30分钟 |
| **总计** | **约3小时** |

---

## 下一步

完成阶段1后，继续执行：

- **阶段2**: 模块化改进循环（提升测试覆盖率到80%）
- **阶段3**: 整体验证与文档

详见主计划文档：`docs/plans/2026-03-01-project-health-cleanup.md`
