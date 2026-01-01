# 技术栈路径约定 (Tech Stack Path Conventions)

> **适用场景**: 所有技术角色（架构师、开发、DevOps）在定义路径时的参考标准
> **最后更新**: 2026-01-01

---

## 📋 目录
- [1. 测试路径规范](#1-测试路径规范)
- [2. 模块/源码路径规范](#2-模块源码路径规范)
- [3. 文档路径规范](#3-文档路径规范)
- [4. 构建输出路径规范](#4-构建输出路径规范)
- [5. 命名规范](#5-命名规范)

---

## 1. 测试路径规范

| 技术栈 | 测试路径 | 测试框架 | 备注 |
|:---|:---|:---|:---|
| **Python** | `tests/` 或 `backend/tests/` | pytest, unittest | 项目根目录或 backend 目录下 |
| **Java** | `src/test/java/` | JUnit, TestNG | Maven/Gradle 标准结构 |
| **.NET** | `Tests/` 或 `*.Tests/` | xUnit, NUnit | Visual Studio 标准 |
| **Node.js** | `__tests__/` 或 `tests/` | Jest, Vitest, Mocha | 项目根目录或与源码同级 |
| **Go** | `*_test.go` (与源码同目录) | testing | Go 约定：测试文件与源码同目录 |
| **Rust** | `tests/` | cargo test | 项目根目录 |

### 前端测试路径

| 技术栈 | 测试路径 | 测试框架 | 备注 |
|:---|:---|:---|:---|
| **Vue 3** | `tests/` 或 `__tests__/` | Vitest, Jest | 项目根目录 |
| **React** | `__tests__/` 或 `src/__tests__/` | Jest, Vitest | 与组件同目录或 src 下 |
| **Angular** | `*.spec.ts` (与组件同目录) | Jasmine, Jest | 测试文件与组件同目录 |

---

## 2. 模块/源码路径规范

| 技术栈 | 模块路径 | 备注 |
|:---|:---|:---|
| **Python** | `src/` 或 `app/` 或项目根目录 | 根据项目结构选择 |
| **Java** | `src/main/java/` | Maven/Gradle 标准结构 |
| **.NET** | `src/` 或项目根目录 | Visual Studio 标准 |
| **Node.js** | `src/` 或 `lib/` | 项目根目录下 |
| **Go** | 项目根目录或 `cmd/`, `pkg/` | Go 项目标准布局 |
| **Rust** | `src/` | Cargo 标准结构 |

### 前端源码路径

| 技术栈 | 源码路径 | 备注 |
|:---|:---|:---|
| **Vue 3** | `src/` | 标准 Vue 项目结构 |
| **React** | `src/` | Create React App 标准 |
| **Angular** | `src/app/` | Angular CLI 标准 |

---

## 3. 文档路径规范

> **统一约定**：所有项目使用相同的文档路径结构，便于跨项目协作。

| 文档类型 | 路径 | 说明 |
|:---|:---|:---|
| **需求文档** | `docs/requirements/` | PRD、功能规格、验收剧本 |
| **设计文档** | `docs/design/` | API 接口、数据模型、架构图 |
| **角色定义** | `docs/roles/` | 各角色的工作手册 |
| **部署文档** | `docs/deployment/` | 部署脚本、环境配置（可选） |

---

## 4. 构建输出路径规范

| 技术栈 | 构建输出路径 | 备注 |
|:---|:---|:---|
| **Python** | `dist/` 或 `build/` | 打包后的 wheel/sdist |
| **Java** | `target/` (Maven) 或 `build/` (Gradle) | 编译后的 jar/war |
| **.NET** | `bin/`, `obj/` | Visual Studio 标准 |
| **Node.js** | `dist/` 或 `build/` | 编译后的 JavaScript |
| **Vue 3** | `dist/` | Vite/Webpack 构建输出 |
| **React** | `build/` 或 `dist/` | Create React App 默认 `build/` |

---

## 5. 命名规范

> **目的**: 统一代码命名风格，减少 Code Review 时间，提高代码可读性。

### 5.1 通用命名约定

| 类型 | 命名风格 | 示例 | 说明 |
|:---|:---|:---|:---|
| **文件/目录名** | kebab-case | `user-service.ts`, `api-client.js` | 小写字母，单词间用连字符分隔 |
| **类名** | PascalCase | `UserService`, `ApiClient` | 首字母大写的驼峰命名 |
| **接口/类型** | PascalCase | `UserInfo`, `ApiResponse` | 与类名相同 |
| **变量/函数** | camelCase | `userName`, `getUserInfo()` | 首字母小写的驼峰命名 |
| **常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` | 全大写，单词间用下划线分隔 |
| **私有成员** | 前缀 + camelCase | `_privateField`, `#privateMethod` | 根据语言约定使用 `_` 或 `#` |

### 5.2 后端命名约定

#### Python
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **模块文件** | snake_case | `user_service.py`, `api_client.py` |
| **类名** | PascalCase | `UserService`, `ApiClient` |
| **函数/变量** | snake_case | `get_user_info()`, `user_name` |
| **常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| **私有成员** | 前缀 `_` | `_private_field`, `_private_method()` |

#### Java
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **类文件** | PascalCase | `UserService.java`, `ApiClient.java` |
| **类名** | PascalCase | `UserService`, `ApiClient` |
| **方法/变量** | camelCase | `getUserInfo()`, `userName` |
| **常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| **包名** | lowercase | `com.example.service`, `com.example.client` |

#### Go
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **文件** | snake_case | `user_service.go`, `api_client.go` |
| **公开类型/函数** | PascalCase | `UserService`, `GetUserInfo()` |
| **私有类型/函数** | camelCase | `userService`, `getUserInfo()` |
| **常量** | PascalCase 或 UPPER_SNAKE_CASE | `MaxRetryCount`, `API_BASE_URL` |

#### Node.js/TypeScript
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **文件** | kebab-case | `user-service.ts`, `api-client.ts` |
| **类/接口** | PascalCase | `UserService`, `ApiClient` |
| **函数/变量** | camelCase | `getUserInfo()`, `userName` |
| **常量** | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |

### 5.3 前端命名约定

#### Vue 3
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **组件文件** | PascalCase | `UserCard.vue`, `ApiClient.vue` |
| **组件名** | PascalCase | `<UserCard />`, `<ApiClient />` |
| **Composables** | camelCase + `use` 前缀 | `useUserInfo()`, `useApiClient()` |
| **Props/Emits** | camelCase | `userName`, `onSubmit` |
| **CSS 类名** | kebab-case | `.user-card`, `.api-client` |

#### React
| 类型 | 命名风格 | 示例 |
|:---|:---|:---|
| **组件文件** | PascalCase | `UserCard.tsx`, `ApiClient.tsx` |
| **组件名** | PascalCase | `<UserCard />`, `<ApiClient />` |
| **Hooks** | camelCase + `use` 前缀 | `useUserInfo()`, `useApiClient()` |
| **Props** | camelCase | `userName`, `onSubmit` |
| **CSS 类名** | camelCase 或 kebab-case | `.userCard` 或 `.user-card` |

### 5.4 数据库命名约定

| 类型 | 命名风格 | 示例 | 说明 |
|:---|:---|:---|:---|
| **表名** | snake_case (复数) | `user_profiles`, `order_items` | 小写，单词间用下划线，通常使用复数 |
| **字段名** | snake_case | `user_id`, `created_at`, `is_active` | 小写，单词间用下划线 |
| **主键** | `id` 或 `{table}_id` | `id`, `user_id` | 简洁明确 |
| **外键** | `{referenced_table}_id` | `user_id`, `order_id` | 明确引用关系 |
| **索引名** | `idx_{table}_{field}` | `idx_users_email`, `idx_orders_created_at` | 便于识别 |
| **约束名** | `{type}_{table}_{field}` | `pk_users_id`, `fk_orders_user_id` | 明确约束类型 |

### 5.5 API 命名约定

| 类型 | 命名风格 | 示例 | 说明 |
|:---|:---|:---|:---|
| **RESTful 路径** | kebab-case (复数) | `/api/v1/user-profiles`, `/api/v1/order-items` | 小写，单词间用连字符，使用复数 |
| **查询参数** | camelCase | `?userId=123&pageSize=10` | 或 snake_case，保持项目内一致 |
| **请求体字段** | camelCase | `{ "userName": "John", "email": "..." }` | 与前端保持一致 |
| **响应体字段** | camelCase | `{ "userId": 123, "userName": "John" }` | 与前端保持一致 |

### 5.6 环境变量命名约定

| 类型 | 命名风格 | 示例 | 说明 |
|:---|:---|:---|:---|
| **环境变量** | UPPER_SNAKE_CASE | `API_BASE_URL`, `DATABASE_HOST`, `MAX_RETRY_COUNT` | 全大写，单词间用下划线 |
| **命名空间** | 前缀 + `_` | `REDIS_HOST`, `POSTGRES_PASSWORD` | 使用服务名作为前缀 |

---

## 6. 使用说明

### 6.1 在项目中使用

1. **选择技术栈**：根据项目实际使用的技术栈，从表格中选择对应的路径。
2. **替换占位符**：在 `.cursorrules` 或其他配置文件中，将占位符替换为实际路径。
3. **保持一致性**：同一项目内，相同技术栈的路径应保持一致。

### 6.2 占位符映射示例

在角色文档的 `.cursorrules` 模板中：

```markdown
# 路径占位符替换（参考 tech_stack_conventions.md）
- `{TEST_PATH}` → 根据技术栈选择（如 Python: `tests/`, Java: `src/test/java/`）
- `{MODULE_PATH}` → 根据技术栈选择（如 Python: `src/`, Java: `src/main/java/`）
- `{BUILD_PATH}` → 根据技术栈选择（如 Python: `dist/`, Java: `target/`）
```

### 6.3 特殊项目处理

如果项目使用了非标准路径结构：
- 在项目文档中明确说明路径选择的原因
- 在 `.cursorrules` 中直接使用具体路径，而非占位符
- 考虑是否值得调整为业界标准路径（便于团队协作）

---

## 7. 参考资源

- [Python Project Structure](https://docs.python-guide.org/writing/structure/)
- [Java Maven Standard Directory Layout](https://maven.apache.org/guides/introduction/introduction-to-the-standard-directory-layout.html)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Vue.js Project Structure](https://vuejs.org/guide/scaling-up/tooling.html)

---

**文档维护者**: Architecture Team  
**反馈与改进**: 欢迎基于实际项目经验提出改进建议

