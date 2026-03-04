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
