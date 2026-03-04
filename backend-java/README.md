# AI智能备课平台 - Java后端

AI智能备课平台的Java后端实现，从Python (FastAPI) 完整迁移到Java (Spring Boot)。

## 技术栈

- **Spring Boot** 3.2.0
- **Spring WebFlux** - 响应式Web框架
- **Spring Data JPA** - ORM框架
- **Spring Security** - 安全认证
- **MySQL** - 数据库
- **LangChain4j** 0.29.1 - AI框架
- **JUnit 5** - 测试框架
- **Maven** - 构建工具

## 架构

项目采用严格的DDD（领域驱动设计）四层架构：

```
backend-java/
├── domain/              # 领域层
│   ├── user/
│   ├── session/
│   ├── tool/
│   └── ai/
├── application/         # 应用层
│   └── service/
├── infrastructure/      # 基础设施层
│   ├── persistence/    # 数据访问
│   ├── ai/            # AI集成
│   ├── config/        # 配置加载
│   └── security/      # 安全认证
└── interfaces/         # 接口层
    └── rest/          # REST控制器
```

## 快速开始

### 环境要求

- JDK 17+
- Maven 3.6+
- MySQL 8.0+

### 启动步骤

```bash
# 1. 克隆项目（如果还没有）
cd /path/to/ai-teacher-platform

# 2. 进入Java后端目录
cd backend-java

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 4. 构建项目
mvn clean install

# 5. 运行应用
mvn spring-boot:run
```

应用将在 http://localhost:8080 启动。

### 配置说明

主要配置文件：`src/main/resources/application.yml`

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ai_teacher
    username: root
    password: ${DB_PASSWORD}

jwt:
  secret: ${JWT_SECRET_KEY}
  expiration: 86400000  # 24小时

ai:
  provider:
    current: deepseek
    providers:
      deepseek:
        api-key: ${DEEPSEEK_API_KEY}
```

## API文档

### 认证接口

- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户

### 对话接口

- `POST /api/v1/tools/{toolId}/chat/stream` - SSE流式对话
- `POST /api/v1/tools/{toolId}/chat` - 非流式对话

### 工具接口

- `GET /api/v1/tools` - 获取所有工具
- `GET /api/v1/tools/{toolId}` - 获取工具详情
- `GET /api/v1/common-tools/categories` - 获取通用工具分类

### 作品接口

- `GET /api/v1/works/categories` - 获取作品分类

### 课程接口

- `GET /api/v1/documents/categories` - 获取课程文档分类树

## 开发

### 运行测试

```bash
# 单元测试
mvn test

# 集成测试
mvn verify

# 测试覆盖率
mvn jacoco:report
```

### 代码格式化

```bash
# 使用谷歌Java风格指南
mvn com.google.code.maven:google-java-format:1.15.0:format
```

## 迁移状态

本项目是从Python后端（FastAPI）完整迁移的Java版本。

- ✅ 领域层完整实现
- ✅ 应用层完整实现
- ✅ 基础设施层完整实现
- ✅ 接口层完整实现
- ✅ 核心业务逻辑100%对应
- ✅ 测试用例完整迁移

详见：[迁移分析文档](../../docs/python-to-java-migration-analysis.md)

## 许可证

[项目许可证]

## 作者

AI Teacher Platform Team
