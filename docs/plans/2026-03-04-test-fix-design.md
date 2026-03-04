# 测试修复设计文档

**日期**: 2026-03-04
**作者**: AI Assistant
**状态**: 设计阶段

---

## 📋 概述

本文档详细描述了 AI 智能备课平台测试系统的全面修复方案。测试报告显示：
- Java 后端：39个测试文件编译失败
- 前端：1个测试失败
- Vitest：覆盖率报告未生成
- E2E：无法运行（依赖后端）

**修复策略**：渐进式修复（方案A）
**目标**：所有测试通过，不删除、不跳过任何测试

---

## 🔍 问题分类

### 1. Java 后端测试编译错误 (39个文件)

#### 1.1 MessageEntity getter/setter 方法不匹配 (3个文件)

**问题**: 测试代码调用 `getId()/setId()`，但 Lombok @Data 生成的是 `getMessageId()/setMessageId()`

**影响文件**:
```
backend-java/src/test/java/com/aieducenter/studio/infrastructure/persistence/jpa/
├── MessageJpaRepositoryTest.java
├── UserJpaRepositoryTest.java
└── SessionJpaRepositoryTest.java
```

**修复方式**:
```java
// 修改前
message1.setId("msg-1");
message1.getId();

// 修改后
message1.setMessageId("msg-1");
message1.getMessageId();
```

---

#### 1.2 Message 构造函数签名不匹配 (约15个文件)

**问题**: 测试调用 3 参数构造函数 `new Message(id, role, content)`，但实际 @AllArgsConstructor 需要 6 个参数

**Message 实际签名**:
```java
@AllArgsConstructor
public class Message {
    private String id;           // 参数1
    private String sessionId;    // 参数2
    private MessageRole role;    // 参数3
    private String content;      // 参数4
    private Artifact artifact;   // 参数5
    private LocalDateTime createdAt; // 参数6
}
```

**影响文件**:
```
backend-java/src/test/java/com/aieducenter/studio/
├── application/service/AIServiceCompleteTest.java (多处)
├── application/service/AIServiceTest.java
├── application/service/SessionServiceTest.java
├── domain/ai/MessageTest.java
├── interfaces/rest/ChatControllerIntegrationTest.java
└── ... 其他约10个文件
```

**修复方式** (推荐使用工厂方法):
```java
// 修改前
new Message("msg1", MessageRole.USER, "Previous message")

// 方式1: 使用工厂方法 (推荐)
Message.createUserMessage(sessionId, content)

// 方式2: 完整构造函数
new Message("msg1", sessionId, MessageRole.USER, "content", null, LocalDateTime.now())

// 方式3: Setter 方法
Message msg = new Message();
msg.setId("msg1");
msg.setRole(MessageRole.USER);
msg.setContent("content");
```

---

#### 1.3 AIService 缺少方法 (1个文件)

**问题**: 测试调用不存在的方法

**缺失方法**:

##### 1.3.1 `isCodeBlockComplete(String content)`

**测试用例**:
```java
@Test
void isCodeBlockComplete_Complete() {
    assertTrue(aiService.isCodeBlockComplete("```python\nprint('hello')\n```"));
    assertTrue(aiService.isCodeBlockComplete("```html\n<div></div>\n```"));
}

@Test
void isCodeBlockComplete_Incomplete() {
    assertFalse(aiService.isCodeBlockComplete("```python\nprint('hello')"));
    assertFalse(aiService.isCodeBlockComplete("```python\n```"));
    assertFalse(aiService.isCodeBlockComplete(""));
}
```

**实现方案**:
```java
/**
 * 检查代码块是否完整（闭合）
 * @param content 内容
 * @return true-代码块完整，false-不完整或无代码块
 */
public boolean isCodeBlockComplete(String content) {
    if (content == null || content.isEmpty()) {
        return false;
    }
    // 使用现有的 hasUnclosedCodeBlock 方法
    return !hasUnclosedCodeBlock(content);
}
```

##### 1.3.2 `detectCodeBlock(String markdown)`

**测试用例**:
```java
@Test
void detectCodeBlock_MatchSuccess() {
    String result = aiService.detectCodeBlock("```python\nprint('hello')\n```");
    assertEquals("print('hello')", result);
}

@Test
void detectCodeBlock_NoCodeBlock() {
    String result = aiService.detectCodeBlock("Just plain text");
    assertNull(result);
}
```

**实现方案**:
```java
/**
 * 从markdown中提取代码块内容
 * @param markdown markdown文本
 * @return 代码块内容，如果没有则返回null
 */
public String detectCodeBlock(String markdown) {
    if (markdown == null || markdown.isEmpty()) {
        return null;
    }

    Pattern pattern = Pattern.compile("```\\w*\\n([\\s\\S]*?)\\n```");
    Matcher matcher = pattern.matcher(markdown);

    if (matcher.find()) {
        return matcher.group(1);
    }

    return null;
}
```

---

#### 1.4 LangChain4j API 歧义 (2处)

**问题**: `ChatLanguageModel.generate()` 有两个重载：
```java
Response<AiMessage> generate(List<ChatMessage> messages)
Response<AiMessage> generate(List<ChatMessage> messages, List<ToolSpecification> tools)
```

测试代码使用 `any()` 导致歧义。

**影响位置**:
```
AIServiceCompleteTest.java:297
AIServiceCompleteTest.java:315
```

**修复方式**:
```java
// 修改前
when(chatLanguageModel.generate(any(List.class), any())).thenReturn(...)

// 修改后 - 显式指定类型
when(chatLanguageModel.generate(any(List.class), any(List.class))).thenReturn(...)
```

---

#### 1.5 其他可能的测试同步问题 (约20个文件)

需要逐个检查以下测试文件，确保与当前实现同步：

```
backend-java/src/test/java/com/aieducenter/studio/
├── application/service/
│   ├── ArtifactParserTest.java
│   ├── TitleGeneratorTest.java
│   ├── CommonToolServiceTest.java
│   ├── CourseServiceTest.java
│   ├── ToolServiceTest.java
│   ├── UserServiceTest.java
│   ├── WorkServiceTest.java
│   └── YamlConfigLoaderTest.java
├── infrastructure/persistence/jpa/
│   ├── CommonToolJpaRepositoryTest.java
│   ├── CourseCategoryJpaRepositoryTest.java (如果存在)
│   ├── CourseDocumentJpaRepositoryTest.java (如果存在)
│   ├── ToolCategoryJpaRepositoryTest.java (如果存在)
│   ├── WorkCategoryJpaRepositoryTest.java (如果存在)
│   └── WorkJpaRepositoryTest.java (如果存在)
├── e2e/
│   ├── AdminWorkflowE2ETest.java
│   ├── UserJourneyE2ETest.java
│   ├── CourseManagementE2ETest.java
│   └── WorkManagementE2ETest.java
├── interfaces/rest/
│   └── AuthControllerIntegrationTest.java
└── domain/
    ├── user/UserTest.java
    ├── ai/MessageRoleTest.java
    ├── ai/MessageTest.java
    ├── artifact/ArtifactTest.java
    ├── tool/CommonToolTypeTest.java
    ├── tool/ToolTest.java
    └── session/SessionTest.java
```

---

### 2. 前端测试失败 (1个文件)

#### 2.1 ConversationList 时间格式化正则错误

**文件**: `frontend/tests/unit/components/ConversationList.spec.ts`

**问题**: 正则表达式 `/周[一二三四五六七]/` 不匹配 "周日"

**位置**: 第678行

**修复方式**:
```typescript
// 修改前
expect(formattedTime).toMatch(/周[一二三四五六七]/);

// 修改后
expect(formattedTime).toMatch(/周[一二三四五六日]/);
```

---

### 3. Vitest 覆盖率报告未生成

#### 3.1 配置问题

**文件**: `frontend/vitest.config.ts`

**可能原因**:
- 覆盖率目录未明确指定
- 报告生成路径问题

**修复方式**:
```typescript
coverage: {
  provider: 'v8',
  reporter: ['text', 'json', 'html'],
  coverageDirectory: './coverage', // 添加此行
  reportsDirectory: './coverage',   // 添加此行 (Vitest 4.x)
  exclude: [
    'node_modules/',
    'tests/',
    '**/*.d.ts',
    '**/*.config.*',
    '**/mockData',
    'src/main.ts',
  ],
}
```

---

### 4. E2E 测试依赖问题

#### 4.1 后端服务未运行

**文件**: `frontend/tests/e2e/chat.spec.ts`

**问题**: E2E 测试需要后端 API 服务运行

**解决方案**:
1. 修复 Java 后端编译错误
2. 启动后端服务
3. 运行 E2E 测试

---

## 🎯 修复方案

### 渐进式修复策略 (方案A)

#### 阶段 1: MessageEntity getter/setter 修复 (10分钟)

**目标**: 修复 JPA 实体测试的 getter/setter 调用

**文件清单**:
1. `MessageJpaRepositoryTest.java`
2. `UserJpaRepositoryTest.java`
3. `SessionJpaRepositoryTest.java`

**验证命令**:
```bash
cd backend-java
mvn test -Dtest=MessageJpaRepositoryTest
mvn test -Dtest=UserJpaRepositoryTest
mvn test -Dtest=SessionJpaRepositoryTest
```

---

#### 阶段 2: Message 构造函数修复 (30分钟)

**目标**: 同步所有 Message 对象创建方式

**优先级文件**:
1. `AIServiceCompleteTest.java` - 最多问题
2. `AIServiceTest.java`
3. `SessionServiceTest.java`
4. `MessageTest.java`
5. `ChatControllerIntegrationTest.java`

**其他文件** (需要检查):
6. `ArtifactParserTest.java`
7. `TitleGeneratorTest.java`
8. `CommonToolServiceTest.java`
9. `CourseServiceTest.java`
10. `ToolServiceTest.java`
11. `UserServiceTest.java`
12. `WorkServiceTest.java`
13. 所有 JPA Repository 测试
14. 所有 E2E 测试
15. 所有集成测试

**修复原则**:
- 优先使用工厂方法 `Message.createUserMessage()` 和 `Message.createAssistantMessage()`
- 如果需要完整控制，使用 6 参数构造函数
- 测试数据使用 Setter 方式也可以

**验证命令**:
```bash
cd backend-java
mvn test -Dtest=AIServiceCompleteTest
mvn test -Dtest=AIServiceTest
mvn test -Dtest=SessionServiceTest
```

---

#### 阶段 3: AIService 方法添加 (15分钟)

**目标**: 添加缺失的公共方法

**文件**: `AIService.java`

**添加位置**: 在 `autoContinue()` 方法之后，类结束之前

**添加内容**:
```java
/**
 * 检查代码块是否完整（闭合）
 *
 * 用于判断AI生成的内容中代码块是否闭合，
 * 支持自动继续生成功能。
 *
 * @param content 待检查的内容
 * @return true-代码块完整或无代码块，false-代码块不完整
 */
public boolean isCodeBlockComplete(String content) {
    if (content == null || content.isEmpty()) {
        return false;
    }
    return !hasUnclosedCodeBlock(content);
}

/**
 * 从markdown中提取第一个代码块的内容
 *
 * 用于从AI生成的markdown响应中提取代码块，
 * 支持代码预览和语法高亮功能。
 *
 * @param markdown markdown文本
 * @return 代码块内容（不含语言标识和反引号），如果没有代码块则返回null
 */
public String detectCodeBlock(String markdown) {
    if (markdown == null || markdown.isEmpty()) {
        return null;
    }

    // 匹配 ```lang\ncontent\n``` 格式
    Pattern pattern = Pattern.compile("```\\w*\\n([\\s\\S]*?)\\n```");
    Matcher matcher = pattern.matcher(markdown);

    if (matcher.find()) {
        return matcher.group(1);
    }

    return null;
}
```

**需要的导入**:
```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;
```

**验证命令**:
```bash
cd backend-java
mvn test -Dtest=AIServiceCompleteTest#isCodeBlockComplete_Complete
mvn test -Dtest=AIServiceCompleteTest#isCodeBlockComplete_Incomplete
mvn test -Dtest=AIServiceCompleteTest#detectCodeBlock_MatchSuccess
mvn test -Dtest=AIServiceCompleteTest#detectCodeBlock_NoCodeBlock
```

---

#### 阶段 4: LangChain4j API 歧义修复 (5分钟)

**目标**: 明确指定 generate 方法参数类型

**文件**: `AIServiceCompleteTest.java`

**修复位置**: 第297行、第315行

**修复方式**:
```java
// 第297行附近
when(chatLanguageModel.generate(any(List.class), any(List.class)))
    .thenReturn(mockResponse);

// 第315行附近
when(chatLanguageModel.generate(any(List.class), any(List.class)))
    .thenReturn(mockResponse);
```

**验证命令**:
```bash
cd backend-java
mvn test -Dtest=AIServiceCompleteTest#chatStream_WithHistory
mvn test -Dtest=AIServiceCompleteTest#chat_SingleSuccess
```

---

#### 阶段 5: 前端测试修复 (2分钟)

**目标**: 修复时间格式化正则表达式

**文件**: `frontend/tests/unit/components/ConversationList.spec.ts`

**修复位置**: 第678行

**修复方式**:
```typescript
// 修改前
expect(formattedTime).toMatch(/周[一二三四五六七]/);

// 修改后
expect(formattedTime).toMatch(/周[一二三四五六日]/);
```

**验证命令**:
```bash
cd frontend
npm run test -- tests/unit/components/ConversationList.spec.ts
```

---

#### 阶段 6: Vitest 配置修复 (5分钟)

**目标**: 生成覆盖率报告

**文件**: `frontend/vitest.config.ts`

**修复方式**:
```typescript
export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.spec.ts', 'tests/unit/**/*.test.ts', 'tests/views/**/*.test.ts'],
    exclude: ['tests/e2e/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      coverageDirectory: './coverage',
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
```

**验证命令**:
```bash
cd frontend
npm run test:coverage -- --run
ls -la coverage/  # 应该看到 index.html, coverage-final.json 等文件
```

---

#### 阶段 7: 全量测试验证 (15分钟)

**目标**: 确保所有测试通过

**Java 后端全量测试**:
```bash
cd backend-java
mvn clean test
```

**预期结果**:
- ✅ 编译成功，无错误
- ✅ 39个测试类全部执行
- ✅ 至少 35+ 个测试用例通过

**前端全量测试**:
```bash
cd frontend
npm run test -- --run
```

**预期结果**:
- ✅ 582个测试全部通过
- ✅ 无失败、无跳过

**覆盖率报告**:
```bash
cd frontend
npm run test:coverage -- --run
```

**预期结果**:
- ✅ 生成 coverage/index.html
- ✅ 终端显示覆盖率统计

---

## 📊 完整文件清单

### 需要修改的文件总计: 43 个

#### Java 后端 (39个)

```
backend-java/src/test/java/com/aieducenter/studio/
├── application/service/
│   ├── AIServiceCompleteTest.java    [P0] Message构造 + LangChain4j
│   ├── AIServiceTest.java              [P1] Message构造
│   ├── SessionServiceTest.java         [P1] Message构造
│   ├── ArtifactParserTest.java         [P2] 检查同步
│   ├── TitleGeneratorTest.java         [P2] 检查同步
│   ├── CommonToolServiceTest.java      [P2] 检查同步
│   ├── CourseServiceTest.java          [P2] 检查同步
│   ├── ToolServiceTest.java            [P2] 检查同步
│   ├── UserServiceTest.java            [P2] 检查同步
│   ├── WorkServiceTest.java            [P2] 检查同步
│   └── (其他服务测试)
├── infrastructure/persistence/jpa/
│   ├── MessageJpaRepositoryTest.java   [P0] getter/setter
│   ├── UserJpaRepositoryTest.java      [P0] getter/setter
│   ├── SessionJpaRepositoryTest.java   [P0] getter/setter
│   ├── CommonToolJpaRepositoryTest.java [P2] 检查同步
│   └── (其他JPA测试)
├── domain/
│   ├── ai/MessageTest.java             [P1] Message构造
│   ├── session/SessionTest.java        [P2] 检查同步
│   ├── user/UserTest.java              [P2] 检查同步
│   └── (其他领域测试)
├── interfaces/rest/
│   ├── ChatControllerIntegrationTest.java  [P1] Message构造
│   ├── AuthControllerIntegrationTest.java   [P2] 检查同步
│   └── (其他集成测试)
└── e2e/
    ├── AdminWorkflowE2ETest.java       [P3] 检查同步
    ├── UserJourneyE2ETest.java         [P3] 检查同步
    ├── CourseManagementE2ETest.java    [P3] 检查同步
    └── WorkManagementE2ETest.java      [P3] 检查同步

backend-java/src/main/java/com/aieducenter/studio/
└── application/service/
    └── AIService.java                  [P0] 添加方法
```

**优先级说明**:
- P0: 核心问题，必须修复
- P1: 高优先级
- P2: 中优先级，需要检查
- P3: 低优先级，最后检查

#### 前端 (2个)

```
frontend/
├── tests/unit/components/
│   └── ConversationList.spec.ts        [P0] 正则修复
└── vitest.config.ts                    [P0] 覆盖率配置
```

---

## ✅ 成功标准

### Java 后端
- ✅ `mvn clean test` 编译成功
- ✅ 39个测试类全部加载
- ✅ 零编译错误
- ✅ 至少 90% 测试通过 (35+)
- ⚠️ 允许少量测试失败（需要后续修复）

### 前端
- ✅ 582个测试全部通过 (100%)
- ✅ 零失败、零跳过
- ✅ 覆盖率报告生成

### Vitest
- ✅ 生成 `coverage/index.html`
- ✅ 生成 `coverage/coverage-final.json`
- ✅ 终端显示覆盖率统计

### E2E
- ✅ 可以运行（需要后端服务）
- ⚠️ 不要求全部通过（依赖环境）

---

## 🚨 风险与缓解

### 风险 1: 测试逻辑与实现不匹配

**风险等级**: 高

**描述**: 某些测试可能基于旧版本的实现逻辑

**缓解措施**:
- 先修复编译错误
- 运行测试，检查失败原因
- 如果测试逻辑确实过时，更新测试
- 只有在证明测试无用时才删除

---

### 风险 2: 工厂方法不支持某些测试场景

**风险等级**: 中

**描述**: 某些测试需要特定的 Message 状态

**缓解措施**:
- 使用完整构造函数
- 或使用 Setter 方法
- 添加新的工厂方法（如果确实需要）

---

### 风险 3: Vitest 覆盖率仍然无法生成

**风险等级**: 低

**描述**: 配置修改后仍无法生成报告

**缓解措施**:
- 检查 Vitest 版本
- 检查文件权限
- 尝试不同的 reporter 配置
- 查看 Vitest 文档

---

## 📝 实施注意事项

1. **不要删除任何测试** - 除非有明确证据证明测试无用
2. **不要跳过任何测试** - 所有测试都应该能够运行
3. **保持测试语义** - 修复应该是机械的，不改变测试意图
4. **分阶段验证** - 每个阶段完成后立即验证
5. **记录问题** - 如果遇到无法修复的测试，详细记录原因

---

## 🔗 相关文档

- [TEST_REPORT.md](../../TEST_REPORT.md) - 原始测试报告
- [CLAUDE.md](../../CLAUDE.md) - 项目指南
- [MEMORY.md](../../memory/MEMORY.md) - 项目记忆

---

**下一步**: 调用 `writing-plans` skill 生成详细的实施计划
