# 测试指南

## 概述

本项目采用多层测试策略，确保代码质量和系统稳定性。

- **后端测试**：pytest + pytest-cov
- **前端测试**：Vitest + Playwright
- **测试覆盖率**：后端38%，目标80%（Phase 2提升）
- **测试隔离**：使用内存数据库，确保测试不影响开发环境

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
python3 -m pytest tests/unit/ tests/integration/ -v
```

### 测试环境隔离

- 单元测试使用 `sqlite:///:memory:`
- 每个测试函数有独立的数据库实例
- 测试不会影响开发数据库
- 174个缓存目录已清理，.gitignore已更新

### 当前测试状态

- **测试数量**：155个（141单元 + 14集成）
- **测试覆盖率**：38%
- **测试通过率**：100%

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

| 阶段 | 后端覆盖率 | 前端覆盖率 | 状态 |
|------|-----------|-----------|------|
| Phase 1 完成 | 38% | - | ✅ 当前 |
| Phase 2 目标 | 80%+ | 80%+ | ⏳ 进行中 |
| Phase 3 目标 | 80%+ | 80%+ | 📋 计划中 |

## 最佳实践

1. **TDD优先**：先写测试，再写实现
2. **测试隔离**：每个测试应该独立，不依赖其他测试
3. **清理数据**：使用fixture自动清理测试数据
4. **Mock外部依赖**：不要依赖真实的外部API
5. **快速失败**：测试应该快速失败，明确指出问题

## 快速测试命令

### 后端

```bash
# 快速测试（约3秒）
cd backend && python3 -m pytest tests/unit/ tests/integration/ -v

# 生成覆盖率报告
cd backend && python3 -m pytest tests/unit/ tests/integration/ --cov=src --cov-report=html
```

### 前端

```bash
# E2E测试（约6秒）
cd frontend && npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```

## 故障排查

### 测试数据库问题

如果测试数据库出现问题：

```bash
# 清理Python缓存
find backend -type d -name "__pycache__" -exec rm -rf {} +
find backend -type d -name ".pytest_cache" -exec rm -rf {} +

# 运行测试
cd backend && python3 -m pytest tests/ -v
```

### 前端测试缓存问题

```bash
# 清理node_modules缓存
rm -rf frontend/node_modules/.cache
rm -rf frontend/.vitest

# 运行测试
cd frontend && npm run test -- --run
```

### E2E测试失败

```bash
# 清理Playwright缓存
cd frontend && npx playwright clean-cache

# 重新安装浏览器
cd frontend && npx playwright install --with-deps chromium

# 运行测试
cd frontend && npm run test:e2e -- tests/e2e/chat.spec.ts --project=chromium
```

## Phase 1 完成状态

✅ **测试基础设施建立完成**

- 清理了320KB无用文件（备份、test.db）
- 清理了174个缓存目录
- 更新了.gitignore规则
- 测试环境完全隔离
- 测试指南文档完成

**下一步**：Phase 2 - 模块化改进循环，提升测试覆盖率到80%

---

**文档版本**：1.0
**最后更新**：2026-03-01
**维护者**：Claude Code
