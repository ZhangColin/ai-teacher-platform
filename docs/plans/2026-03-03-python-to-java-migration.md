# Python到Java完整迁移实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 将AI智能备课平台后端从Python (FastAPI)完全迁移到Java (Spring Boot)，保持100%功能一致性，包括80+ API端点、855个测试用例、SSE流式对话等所有功能。

**架构：** 严格DDD架构（domain/application/infrastructure/interfaces），使用Spring WebFlux响应式编程、LangChain4j AI框架、Spring Security JWT认证。

**技术栈：** Spring Boot 3.2.0、WebFlux、Spring Data JPA、MyBatis-Plus、LangChain4j 0.29.1、JUnit 5、Mockito

---

## 阶段1：项目基础设施搭建（2周）

### Task 1: 创建Spring Boot项目骨架

**Files:**
- Create: `backend-java/pom.xml`
- Create: `backend-java/src/main/java/com/platform/AiTeacherPlatformApplication.java`
- Create: `backend-java/src/main/resources/application.yml`
- Create: `backend-java/src/test/java/com/platform/AiTeacherPlatformApplicationTests.java`

**Step 1: 创建Maven项目配置文件**

创建 `backend-java/pom.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.platform</groupId>
    <artifactId>ai-teacher-platform</artifactId>
    <version>1.0.0</version>
    <name>AI Teacher Platform</name>
    <description>AI智能备课平台 - Java后端</description>

    <properties>
        <java.version>17</java.version>
        <langchain4j.version>0.29.1</langchain4j.version>
        <mybatis-plus.version>3.5.5</mybatis-plus.version>
        <jjwt.version>0.11.5</jjwt.version>
        <hutool.version>5.8.23</hutool.version>
    </properties>

    <dependencies>
        <!-- Spring Boot WebFlux -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webflux</artifactId>
        </dependency>

        <!-- Spring Data JPA -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>

        <!-- MyBatis-Plus -->
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
            <version>${mybatis-plus.version}</version>
        </dependency>

        <!-- Spring Security -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>

        <!-- JWT -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>${jjwt.version}</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>

        <!-- LangChain4j -->
        <dependency>
            <groupId>dev.langchain4j</groupId>
            <artifactId>langchain4j</artifactId>
            <version>${langchain4j.version}</version>
        </dependency>
        <dependency>
            <groupId>dev.langchain4j</groupId>
            <artifactId>langchain4j-open-ai</artifactId>
            <version>${langchain4j.version}</version>
        </dependency>

        <!-- MySQL -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- HikariCP -->
        <dependency>
            <groupId>com.zaxxer</groupId>
            <artifactId>HikariCP</artifactId>
        </dependency>

        <!-- YAML配置 -->
        <dependency>
            <groupId>org.yaml</groupId>
            <artifactId>snakeyaml</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- Hutool工具类 -->
        <dependency>
            <groupId>cn.hutool</groupId>
            <artifactId>hutool-all</artifactId>
            <version>${hutool.version}</version>
        </dependency>

        <!-- 测试依赖 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>io.projectreactor</groupId>
            <artifactId>reactor-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

**Step 2: 验证pom.xml**

Run: `cd backend-java && mvn dependency:tree`
Expected: 显示所有依赖树，无错误

**Step 3: 创建主应用类**

创建 `backend-java/src/main/java/com/platform/AiTeacherPlatformApplication.java`:

```java
package com.platform;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AiTeacherPlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiTeacherPlatformApplication.class, args);
    }
}
```

**Step 4: 创建application.yml配置**

创建 `backend-java/src/main/resources/application.yml`:

```yaml
spring:
  application:
    name: ai-teacher-platform

  # 数据库配置
  datasource:
    url: jdbc:mysql://localhost:3306/ai_teacher?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai
    username: root
    password: ${DB_PASSWORD:}
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      pool-name: AiTeacherHikariCP
      minimum-idle: 5
      maximum-pool-size: 20
      max-lifetime: 1800000
      connection-timeout: 30000
      connection-test-query: SELECT 1

  # JPA配置
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    database-platform: org.hibernate.dialect.MySQL8Dialect
    properties:
      hibernate:
        format_sql: true

# 服务器配置
server:
  port: 8080
  compression:
    enabled: true

# 日志配置
logging:
  level:
    root: INFO
    com.platform: DEBUG
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE
```

**Step 5: 创建基础测试类**

创建 `backend-java/src/test/java/com/platform/AiTeacherPlatformApplicationTests.java`:

```java
package com.platform;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class AiTeacherPlatformApplicationTests {

    @Test
    void contextLoads() {
        // 验证Spring上下文可以正常加载
    }
}
```

创建 `backend-java/src/test/resources/application-test.yml`:

```yaml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password:
  jpa:
    hibernate:
      ddl-auto: create-drop
```

**Step 6: 运行测试验证项目搭建**

Run: `cd backend-java && mvn test`
Expected: 测试通过，Spring上下文加载成功

**Step 7: 提交项目骨架**

```bash
cd backend-java
git init
git add .
git commit -m "feat: 创建Spring Boot项目骨架

- 配置Maven依赖（WebFlux、JPA、Security、LangChain4j）
- 创建主应用类
- 配置application.yml
- 创建基础测试类"
```

---

### Task 2: 搭建DDD包结构

**Files:**
- Create: `backend-java/src/main/java/com/platform/domain/README.md`
- Create: `backend-java/src/main/java/com/platform/application/README.md`
- Create: `backend-java/src/main/java/com/platform/infrastructure/README.md`
- Create: `backend-java/src/main/java/com/platform/interfaces/README.md`

**Step 1: 创建领域层包结构**

Run:
```bash
cd backend-java/src/main/java/com/platform
mkdir -p domain/user domain/session domain/artifact domain/tool domain/work/domain/course domain/ai
mkdir -p domain/user/repository domain/session/repository domain/artifact/repository domain/tool/repository domain/work/repository domain/course/repository
```

创建 `domain/README.md`:

```markdown
# 领域层（Domain Layer）

## 职责
- 实体（Entity）：业务对象的核心表示
- 值对象（Value Object）：不可变的值类型
- 仓储接口（Repository）：数据访问抽象
- 领域服务（Domain Service）：复杂业务逻辑

## 包结构
- `domain/user/` - 用户聚合
- `domain/session/` - 会话聚合
- `domain/artifact/` - 成果物聚合
- `domain/tool/` - 工具聚合
- `domain/work/` - 作品聚合
- `domain/course/` - 课程聚合
- `domain/ai/` - AI相关领域对象

## 原则
- 实体必须是富领域模型，包含业务逻辑
- 仓储只定义接口，不包含实现
- 领域服务处理跨实体的业务逻辑
- 依赖基础设施层，但不依赖应用层和接口层
```

**Step 2: 创建应用层包结构**

Run:
```bash
mkdir -p application/service application/dto/request application/dto/response application/facade
```

创建 `application/README.md`:

```markdown
# 应用层（Application Layer）

## 职责
- 应用服务（Application Service）：编排业务流程
- DTO（Data Transfer Object）：数据传输对象
- 门面（Facade）：简化的接口

## 包结构
- `application/service/` - 应用服务（对应Python的services/）
- `application/dto/request/` - 请求DTO
- `application/dto/response/` - 响应DTO
- `application/facade/` - 门面服务

## 原则
- 应用服务是无状态的
- 应用服务编排领域对象和领域服务
- DTO与领域模型相互转换
- 依赖领域层和基础设施层
```

**Step 3: 创建基础设施层包结构**

Run:
```bash
mkdir -p infrastructure/persistence/jpa infrastructure/persistence/mapper
mkdir -p infrastructure/ai/provider infrastructure/ai/langchain4j infrastructure/ai/streaming
mkdir -p infrastructure/config infrastructure/security infrastructure/external
```

创建 `infrastructure/README.md`:

```markdown
# 基础设施层（Infrastructure Layer）

## 职责
- 持久化（Persistence）：数据访问实现
- AI集成：AI提供商、LangChain4j
- 配置（Config）：YAML配置加载
- 安全（Security）：JWT、认证授权
- 外部服务（External）：支付、第三方集成

## 包结构
- `infrastructure/persistence/jpa/` - JPA仓储实现
- `infrastructure/persistence/mapper/` - MyBatis映射
- `infrastructure/ai/provider/` - AI提供商实现
- `infrastructure/ai/langchain4j/` - LangChain4j集成
- `infrastructure/ai/streaming/` - 流式响应
- `infrastructure/config/` - 配置加载器
- `infrastructure/security/` - 安全组件
- `infrastructure/external/` - 外部服务客户端

## 原则
- 实现领域层定义的仓储接口
- 封装外部技术细节（数据库、API、文件系统）
- 可以被应用层和接口层依赖
- 不依赖领域层、应用层、接口层
```

**Step 4: 创建接口层包结构**

Run:
```bash
mkdir -p interfaces/rest interfaces/dto interfaces/exception interfaces/middleware
```

创建 `interfaces/README.md`:

```markdown
# 接口层（Interfaces Layer）

## 职责
- REST控制器：处理HTTP请求
- DTO：接口层数据传输对象
- 异常处理：统一异常处理
- 中间件：拦截器、过滤器

## 包结构
- `interfaces/rest/` - REST控制器
- `interfaces/dto/` - 接口DTO
- `interfaces/exception/` - 异常处理
- `interfaces/middleware/` - 中间件

## 原则
- 控制器保持薄，只处理HTTP相关逻辑
- 业务逻辑委托给应用服务
- DTO与领域模型、应用DTO相互转换
- 依赖应用层，可以依赖基础设施层
```

**Step 5: 提交包结构**

```bash
git add .
git commit -m "feat: 搭建DDD四层架构包结构

- 领域层（domain）：实体、值对象、仓储接口
- 应用层（application）：服务、DTO、门面
- 基础设施层（infrastructure）：持久化、AI、配置、安全
- 接口层（interfaces）：REST控制器、异常处理"
```

---

### Task 3: 创建领域实体 - User

**Files:**
- Create: `backend-java/src/main/java/com/platform/domain/user/User.java`
- Create: `backend-java/src/main/java/com/platform/domain/user/repository/UserRepository.java`
- Test: `backend-java/src/test/java/com/platform/domain/user/UserTest.java`

**Step 1: 读取Python的User实体定义**

Read: `backend/src/domain/entities/user.py`

**Step 2: 编写User实体的测试**

创建 `backend-java/src/test/java/com/platform/domain/user/UserTest.java`:

```java
package com.platform.domain.user;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

@DisplayName("User实体测试")
class UserTest {

    @Test
    @DisplayName("创建用户 - 成功")
    void createNew_Success() {
        // When
        User user = User.createNew(
            "test-user-id",
            "testuser",
            "test@example.com",
            LocalDateTime.now()
        );

        // Then
        assertThat(user).isNotNull();
        assertThat(user.getUserId()).isEqualTo("test-user-id");
        assertThat(user.getUsername()).isEqualTo("testuser");
        assertThat(user.getEmail()).isEqualTo("test@example.com");
        assertThat(user.getIsAdmin()).isFalse();
        assertThat(user.getCreatedAt()).isNotNull();
    }

    @Test
    @DisplayName("检查用户是否可以访问工具 - 有权限返回true")
    void canAccessTool_HasPermission_ReturnsTrue() {
        // Given
        User user = User.createNew("uid", "user", "email", LocalDateTime.now());

        // When
        boolean result = user.canAccessTool("any-tool");

        // Then
        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("是否为付费用户 - 默认返回false")
    void isPremiumUser_Default_ReturnsFalse() {
        // Given
        User user = User.createNew("uid", "user", "email", LocalDateTime.now());

        // When
        boolean result = user.isPremiumUser();

        // Then
        assertThat(result).isFalse();
    }
}
```

**Step 3: 运行测试验证失败**

Run: `cd backend-java && mvn test -Dtest=UserTest`
Expected: FAIL with "Cannot find symbol: class User"

**Step 4: 实现User实体**

创建 `backend-java/src/main/java/com/platform/domain/user/User.java`:

```java
package com.platform.domain.user;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 用户实体
 *
 * 对应Python: backend/src/domain/entities/user.py
 * 对应数据库: backend/src/db_models.py UserModel
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {

    /**
     * 用户唯一标识（UUID字符串）
     * 对应Python: user_id: str
     * 对应数据库: user_id CHAR(36)
     */
    private String userId;

    /**
     * 用户名（唯一）
     * 对应Python: username: str
     * 对应数据库: username VARCHAR(50)
     */
    private String username;

    /**
     * 邮箱地址（唯一）
     * 对应Python: email: str
     * 对应数据库: email VARCHAR(100)
     */
    private String email;

    /**
     * 是否为管理员
     * 对应Python: is_admin: bool
     * 对应数据库: is_admin BOOLEAN
     */
    private Boolean isAdmin;

    /**
     * 创建时间
     * 对应Python: created_at: datetime
     * 对应数据库: created_at DATETIME
     */
    private LocalDateTime createdAt;

    /**
     * 昵称
     * 对应数据库: nickname VARCHAR(50)
     */
    private String nickname;

    /**
     * 手机号
     * 对应数据库: phone VARCHAR(20)
     */
    private String phone;

    /**
     * 密码哈希
     * 对应数据库: password_hash VARCHAR(255)
     */
    private String passwordHash;

    /**
     * 头像URL
     * 对应数据库: avatar VARCHAR(255)
     */
    private String avatar;

    /**
     * 创建新用户（工厂方法）
     * 对应Python: @classmethod create_new()
     *
     * @param userId 用户ID
     * @param username 用户名
     * @param email 邮箱
     * @param createdAt 创建时间
     * @return 用户实体
     */
    public static User createNew(
            String userId,
            String username,
            String email,
            LocalDateTime createdAt
    ) {
        User user = new User();
        user.setUserId(userId);
        user.setUsername(username);
        user.setEmail(email);
        user.setIsAdmin(false);
        user.setCreatedAt(createdAt);
        return user;
    }

    /**
     * 生成用户ID（UUID）
     * 对应Python的UUID生成逻辑
     *
     * @return UUID字符串
     */
    public static String generateUserId() {
        return UUID.randomUUID().toString();
    }

    /**
     * 检查用户是否可以访问指定工具
     * 对应Python: can_access_tool(tool_id: str) -> bool
     *
     * @param toolId 工具ID
     * @return true-可以访问，false-不可以访问
     */
    public boolean canAccessTool(String toolId) {
        // TODO: 实现工具访问权限检查逻辑
        // 当前默认返回true，后续可以根据用户等级、工具限制等实现
        return true;
    }

    /**
     * 检查是否为付费用户
     * 对应Python: is_premium_user() -> bool
     *
     * @return true-付费用户，false-免费用户
     */
    public boolean isPremiumUser() {
        // TODO: 实现付费用户检查逻辑
        // 当前默认返回false，后续需要实现
        return false;
    }
}
```

**Step 5: 创建UserRepository接口**

创建 `backend-java/src/main/java/com/platform/domain/user/repository/UserRepository.java`:

```java
package com.platform.domain.user.repository;

import com.platform.domain.user.User;

import java.util.Optional;

/**
 * 用户仓储接口
 *
 * 对应Python: backend/src/domain/repositories/user.py
 * 对应数据库表: users
 */
public interface UserRepository {

    /**
     * 根据用户ID获取用户
     * 对应Python: get_by_id(user_id: str) -> Optional[User]
     *
     * @param userId 用户ID
     * @return 用户（可能为空）
     */
    Optional<User> findById(String userId);

    /**
     * 根据用户名获取用户
     * 对应Python: get_by_username(username: str) -> Optional[User]
     *
     * @param username 用户名
     * @return 用户（可能为空）
     */
    Optional<User> findByUsername(String username);

    /**
     * 根据邮箱获取用户
     * 对应Python: get_by_email(email: str) -> Optional[User]
     *
     * @param email 邮箱
     * @return 用户（可能为空）
     */
    Optional<User> findByEmail(String email);

    /**
     * 创建用户
     * 对应Python: create(user: User) -> User
     *
     * @param user 用户实体
     * @return 创建后的用户
     */
    User create(User user);

    /**
     * 更新用户
     * 对应Python: update(user: User) -> User
     *
     * @param user 用户实体
     * @return 更新后的用户
     */
    User update(User user);

    /**
     * 删除用户
     * 对应Python: delete(user_id: str) -> None
     *
     * @param userId 用户ID
     */
    void delete(String userId);

    /**
     * 获取用户列表（分页）
     * 对应Python: list_all(skip: int, limit: int) -> list[User]
     *
     * @param skip 跳过条数
     * @param limit 限制条数
     * @return 用户列表
     */
    java.util.List<User> listAll(int skip, int limit);
}
```

**Step 6: 运行测试验证通过**

Run: `cd backend-java && mvn test -Dtest=UserTest`
Expected: PASS - 所有4个测试通过

**Step 7: 提交User实体**

```bash
git add .
git commit -m "feat: 创建User领域实体和仓储接口

- 实现User实体（对应Python user.py）
- 实现工厂方法createNew()
- 实现业务方法canAccessTool()和isPremiumUser()
- 定义UserRepository接口
- 添加完整的单元测试"
```

---

### Task 4: 创建JPA实体 - UserEntity

**Files:**
- Create: `backend-java/src/main/java/com/platform/infrastructure/persistence/jpa/UserEntity.java`
- Create: `backend-java/src/main/java/com/platform/infrastructure/persistence/jpa/UserJpaRepository.java`
- Create: `backend-java/src/main/java/com/platform/infrastructure/persistence/jpa/UserRepositoryImpl.java`
- Test: `backend-java/src/test/java/com/platform/infrastructure/persistence/jpa/UserEntityTest.java`

**Step 1: 读取Python的SQLAlchemy模型定义**

Read: `backend/src/db_models.py` 第11-27行（UserModel定义）

**Step 2: 编写UserEntity的测试**

创建 `backend-java/src/test/java/com/platform/infrastructure/persistence/jpa/UserEntityTest.java`:

```java
package com.platform.infrastructure.persistence.jpa;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
@DisplayName("UserEntity JPA测试")
class UserEntityTest {

    @Autowired
    private UserJpaRepository jpaRepository;

    @Test
    @DisplayName("保存用户 - 成功")
    void save_Success() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid");
        entity.setUsername("testuser");
        entity.setEmail("test@example.com");
        entity.setPasswordHash("hashed");
        entity.setIsAdmin(false);

        // When
        UserEntity saved = jpaRepository.save(entity);

        // Then
        assertThat(saved).isNotNull();
        assertThat(saved.getUserId()).isEqualTo("test-uid");
    }

    @Test
    @DisplayName("根据用户名查询 - 找到返回用户")
    void findByUsername_Found_ReturnsUser() {
        // Given
        UserEntity entity = new UserEntity();
        entity.setUserId("test-uid");
        entity.setUsername("testuser");
        entity.setEmail("test@example.com");
        entity.setPasswordHash("hashed");
        entity.setIsAdmin(false);
        jpaRepository.save(entity);

        // When
        Optional<UserEntity> found = jpaRepository.findByUsername("testuser");

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getUsername()).isEqualTo("testuser");
    }

    @Test
    @DisplayName("根据用户名查询 - 未找到返回空")
    void findByUsername_NotFound_ReturnsEmpty() {
        // When
        Optional<UserEntity> found = jpaRepository.findByUsername("nonexistent");

        // Then
        assertThat(found).isEmpty();
    }
}
```

**Step 3: 运行测试验证失败**

Run: `cd backend-java && mvn test -Dtest=UserEntityTest`
Expected: FAIL with "Cannot find symbol: class UserEntity"

**Step 4: 实现UserEntity**

创建 `backend-java/src/main/java/com/platform/infrastructure/persistence/jpa/UserEntity.java`:

```java
package com.platform.infrastructure.persistence.jpa;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 用户JPA实体
 *
 * 对应Python: backend/src/db_models.py UserModel (第11-27行)
 * 对应数据库表: users
 */
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_username", columnList = "username"),
    @Index(name = "idx_email", columnList = "email")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UserEntity {

    /**
     * 用户ID（主键）
     * 对应Python: user_id = Column(CHAR(36), primary_key=True)
     */
    @Id
    @Column(name = "user_id", columnDefinition = "CHAR(36)", length = 36)
    private String userId;

    /**
     * 用户名（唯一）
     * 对应Python: username = Column(String(50), unique=True, nullable=False)
     */
    @Column(name = "username", length = 50, unique = true, nullable = false)
    private String username;

    /**
     * 邮箱（唯一）
     * 对应Python: email = Column(String(100), unique=True)
     */
    @Column(name = "email", length = 100, unique = true)
    private String email;

    /**
     * 密码哈希
     * 对应Python: password_hash = Column(String(255), nullable=False)
     */
    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    /**
     * 是否为管理员
     * 对应Python: is_admin = Column(Boolean, nullable=False, default=False)
     */
    @Column(name = "is_admin", nullable = false)
    private Boolean isAdmin = false;

    /**
     * 昵称
     * 对应Python: nickname = Column(String(50))
     */
    @Column(name = "nickname", length = 50)
    private String nickname;

    /**
     * 手机号
     * 对应Python: phone = Column(String(20))
     */
    @Column(name = "phone", length = 20)
    private String phone;

    /**
     * 头像URL
     * 对应Python: avatar = Column(String(255))
     */
    @Column(name = "avatar", length = 255)
    private String avatar;

    /**
     * 创建时间
     * 对应Python: created_at = Column(DateTime, default=func.now())
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * 更新时间
     * 对应Python: updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
     */
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * 用户的关系映射
     * 注意：为了延迟加载，这些关系在查询时需要特殊处理
     */

    /**
     * 用户的会话列表（一对多）
     * 对应Python: sessions = relationship("SessionModel", back_populates="user")
     */
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<SessionEntity> sessions = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

**Step 5: 创建UserJpaRepository**

创建 `backend-java/src/main/java/com/platform/infrastructure/persistence/jpa/UserJpaRepository.java`:

```java
package com.platform.infrastructure.persistence.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * User JPA Repository
 *
 * Spring Data JPA自动生成实现
 */
@Repository
public interface UserJpaRepository extends JpaRepository<UserEntity, String> {

    /**
     * 根据用户名查询
     *
     * @param username 用户名
     * @return 用户实体（可能为空）
     */
    Optional<UserEntity> findByUsername(String username);

    /**
     * 根据邮箱查询
     *
     * @param email 邮箱
     * @return 用户实体（可能为空）
     */
    Optional<UserEntity> findByEmail(String email);

    /**
     * 检查用户名是否存在
     *
     * @param username 用户名
     * @return true-存在，false-不存在
     */
    boolean existsByUsername(String username);

    /**
     * 检查邮箱是否存在
     *
     * @param email 邮箱
     * @return true-存在，false-不存在
     */
    boolean existsByEmail(String email);
}
```

**Step 6: 运行测试验证通过**

Run: `cd backend-java && mvn test -Dtest=UserEntityTest`
Expected: PASS - 所有3个测试通过

**Step 7: 提交UserEntity**

```bash
git add .
git commit -m "feat: 创建UserEntity JPA实体和Repository

- 实现UserEntity（对应Python UserModel）
- 配置JPA索引和约束
- 实现级联删除关系
- 创建UserJpaRepository接口
- 添加完整的JPA测试"
```

---

## 阶段2：安全认证（1周）

### Task 5: 实现JWT工具类

**Files:**
- Create: `backend-java/src/main/java/com/platform/infrastructure/security/JWTProvider.java`
- Create: `backend-java/src/test/java/com/platform/infrastructure/security/JWTProviderTest.java`

**Step 1: 读取Python的JWT实现**

Read: `backend/src/services/auth_service.py`

**Step 2: 编写JWTProvider测试**

创建 `backend-java/src/test/java/com/platform/infrastructure/security/JWTProviderTest.java`:

```java
package com.platform.infrastructure.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;

@DisplayName("JWTProvider测试")
class JWTProviderTest {

    private JWTProvider jwtProvider;

    @BeforeEach
    void setUp() {
        jwtProvider = new JWTProvider(
            "test-secret-key-must-be-at-least-32-characters-long-for-security",
            Duration.ofHours(24)
        );
    }

    @Test
    @DisplayName("生成Token - 成功")
    void generateToken_Success() {
        // When
        String token = jwtProvider.generateToken("user-123");

        // Then
        assertThat(token).isNotEmpty();
        assertThat(token).isNotBlank();
    }

    @Test
    @DisplayName("验证Token - 有效token返回用户ID")
    void validateToken_ValidToken_ReturnsUserId() {
        // Given
        String userId = "user-123";
        String token = jwtProvider.generateToken(userId);

        // When
        String extractedUserId = jwtProvider.validateToken(token);

        // Then
        assertThat(extractedUserId).isEqualTo(userId);
    }

    @Test
    @DisplayName("验证Token - 无效token抛出异常")
    void validateToken_InvalidToken_ThrowsException() {
        // Given
        String invalidToken = "invalid.token.here";

        // When & Then
        assertThatThrownBy(() -> jwtProvider.validateToken(invalidToken))
            .isInstanceOf(Exception.class);
    }

    @Test
    @DisplayName("验证Token - 过期token抛出异常")
    void validateToken_ExpiredToken_ThrowsException() {
        // Given
        JWTProvider shortLivedProvider = new JWTProvider(
            "test-secret-key-must-be-at-least-32-characters-long-for-security",
            Duration.ofSeconds(-1) // 已过期
        );
        String token = shortLivedProvider.generateToken("user-123");

        // When & Then
        assertThatThrownBy(() -> jwtProvider.validateToken(token))
            .isInstanceOf(Exception.class);
    }
}
```

**Step 3: 运行测试验证失败**

Run: `cd backend-java && mvn test -Dtest=JWTProviderTest`
Expected: FAIL with "Cannot find symbol: class JWTProvider"

**Step 4: 实现JWTProvider**

创建 `backend-java/src/main/java/com/platform/infrastructure/security/JWTProvider.java`:

```java
package com.platform.infrastructure.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.Getter;
import org.springframework.stereotype.Component;

import java.security.Key;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

/**
 * JWT提供者
 *
 * 对应Python: backend/src/services/auth_service.py
 * 负责JWT的生成和验证
 */
@Component
@Getter
public class JWTProvider {

    private final Key secretKey;
    private final Duration expiration;
    private final JwtParser parser;

    /**
     * 构造函数
     *
     * @param secretKey 密钥（至少32字符）
     * @param expiration 过期时间
     */
    public JWTProvider(String secretKey, Duration expiration) {
        if (secretKey.length() < 32) {
            throw new IllegalArgumentException("JWT密钥必须至少32字符");
        }

        this.secretKey = Keys.hmacShaKeyFor(secretKey.getBytes());
        this.expiration = expiration;
        this.parser = Jwts.parserBuilder()
            .setSigningKey(this.secretKey)
            .build();
    }

    /**
     * 生成JWT Token
     * 对应Python: generate_token(user_id: str, remember_me: bool = False) -> str
     *
     * @param userId 用户ID
     * @return JWT Token
     */
    public String generateToken(String userId) {
        Instant now = Instant.now();
        Instant expiry = now.plus(this.expiration);

        return Jwts.builder()
            .setSubject(userId)
            .setIssuedAt(Date.from(now))
            .setExpiration(Date.from(expiry))
            .signWith(this.secretKey, SignatureAlgorithm.HS512)
            .compact();
    }

    /**
     * 生成长期Token（记住我）
     * 对应Python: generate_token(..., remember_me=True) -> str (7天有效期)
     *
     * @param userId 用户ID
     * @return JWT Token（7天有效期）
     */
    public String generateLongLivedToken(String userId) {
        Instant now = Instant.now();
        Instant expiry = now.plus(Duration.ofDays(7));

        return Jwts.builder()
            .setSubject(userId)
            .setIssuedAt(Date.from(now))
            .setExpiration(Date.from(expiry))
            .signWith(this.secretKey, SignatureAlgorithm.HS512)
            .compact();
    }

    /**
     * 验证Token并返回用户ID
     * 对应Python: verify_token(token: str) -> str
     *
     * @param token JWT Token
     * @return 用户ID
     * @throws JwtException Token无效或过期
     */
    public String validateToken(String token) throws JwtException {
        Jws<Claims> claims = parser.parseClaimsJws(token);
        return claims.getBody().getSubject();
    }

    /**
     * 从Token中提取用户ID（不验证签名）
     * 对应Python: get_user_id_from_token(token: str) -> str
     *
     * @param token JWT Token
     * @return 用户ID（可能为null）
     */
    public String getUserIdFromToken(String token) {
        try {
            Jws<Claims> claims = parser.parseClaimsJws(token);
            return claims.getBody().getSubject();
        } catch (JwtException e) {
            return null;
        }
    }
}
```

**Step 5: 运行测试验证通过**

Run: `cd backend-java && mvn test -Dtest=JWTProviderTest`
Expected: PASS - 所有4个测试通过

**Step 6: 提交JWTProvider**

```bash
git add .
git commit -m "feat: 实现JWTProvider工具类

- 实现Token生成（generateToken）
- 实现长期Token（generateLongLivedToken，7天）
- 实现Token验证（validateToken）
- 添加完整的单元测试"
```

---

由于计划文件非常长（包含完整的6个阶段、约200+个任务），我会继续创建完整的计划文件。让我继续添加剩余的核心任务...

（继续编写完整的实施计划...）
