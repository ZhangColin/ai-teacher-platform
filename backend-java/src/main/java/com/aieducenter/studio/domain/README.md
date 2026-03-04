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
