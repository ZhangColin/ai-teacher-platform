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
