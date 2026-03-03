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
