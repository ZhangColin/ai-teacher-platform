# 企业积分系统设计文档

**日期**: 2026-03-23
**版本**: 1.0
**作者**: Claude

---

## 1. 概述

### 1.1 背景

AI 智能备课平台需要引入企业级积分管理功能，支持多企业独立运营，每个企业的用户共享企业积分池，使用 AI 能力时按 token 消耗扣减积分。

### 1.2 目标

1. 支持多企业管理，每个企业独立运营
2. 企业用户共享积分池
3. AI 能力按 token 消耗自动扣减积分
4. 支持在线充值和后台手动充值/赠送
5. 企业管理员可管理企业用户和查看消费记录

### 1.3 范围

本设计涵盖：
- 企业和用户关系管理
- 积分余额管理（赠送积分、充值积分、负债积分）
- AI 消费自动扣费
- 积分充值和交易记录
- 模型级汇率配置
- 企业后台管理界面

**暂不包含**：在线支付接口（后续单独实现）

---

## 2. 数据模型设计

### 2.1 新增表

#### EnterpriseModel（企业表）

```python
class EnterpriseModel(Base):
    """企业数据库模型"""
    __tablename__ = "enterprises"

    id = Column(CHAR(36), primary_key=True)
    name = Column(String(100), nullable=False, comment='企业名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='企业代码')
    status = Column(Enum(EnterpriseStatus), nullable=False, default=EnterpriseStatus.active)

    # 积分余额
    balance_gratis = Column(Integer, nullable=False, default=0, comment='赠送积分余额（非负）')
    balance_paid = Column(Integer, nullable=False, default=0, comment='充值积分余额（非负）')
    debt_points = Column(Integer, nullable=False, default=0, comment='负债积分（透支金额，非负）')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 计算属性
    @property
    def total_points(self):
        return self.balance_gratis + self.balance_paid - self.debt_points
```

#### PointTransactionModel（积分交易记录表）

```python
class PointTransactionModel(Base):
    """积分交易记录（充值、赠送、退款等管理员操作）"""
    __tablename__ = "point_transactions"

    id = Column(CHAR(36), primary_key=True)
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    operator_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=True, comment='操作人')

    type = Column(Enum(PointTransactionType), nullable=False, comment='recharge/gift/refund/adjust')
    source_type = Column(Enum(PointSourceType), nullable=False, comment='online/offline/admin_gift')

    amount = Column(Integer, nullable=False, comment='积分金额（正数）')
    balance_before = Column(Integer, nullable=False, comment='变动前总积分')
    balance_after = Column(Integer, nullable=False, comment='变动后总积分')

    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
```

#### AIConsumptionModel（AI 消费记录表）

```python
class AIConsumptionModel(Base):
    """AI 消费记录数据库模型"""
    __tablename__ = "ai_consumptions"

    id = Column(CHAR(36), primary_key=True)
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id"), nullable=False, index=True)
    message_id = Column(CHAR(36), ForeignKey("messages.message_id"), nullable=False, index=True)

    # 模型信息
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    # Token 消耗
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # 积分扣减
    gratis_points_used = Column(Integer, nullable=False, default=0, comment='使用的赠送积分')
    paid_points_used = Column(Integer, nullable=False, default=0, comment='使用的充值积分')
    total_points = Column(Integer, nullable=False, comment='总扣减积分')

    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)
```

#### ModelPointRateModel（模型积分汇率表）

```python
class ModelPointRateModel(Base):
    """模型积分汇率数据库模型"""
    __tablename__ = "model_point_rates"

    id = Column(CHAR(36), primary_key=True)
    model_config_id = Column(CHAR(36), ForeignKey("model_configs.id", ondelete="CASCADE"),
                             nullable=False, unique=True, index=True)

    # 汇率配置
    tokens_per_point = Column(Integer, nullable=False, default=1000, comment='每积分对应token数')
    separate_io = Column(Boolean, nullable=False, default=False, comment='是否区分输入输出')
    tokens_per_point_input = Column(Integer, nullable=True)
    tokens_per_point_output = Column(Integer, nullable=True)

    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
```

### 2.2 修改现有表

#### UserModel（添加企业关联）

```python
# 新增字段
enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
is_enterprise_admin = Column(Boolean, nullable=False, default=False, index=True)

# 新增关系
enterprise = relationship("EnterpriseModel", back_populates="users")
```

### 2.3 枚举定义

```python
class EnterpriseStatus(enum.Enum):
    """企业状态枚举"""
    active = "active"
    suspended = "suspended"
    archived = "archived"


class PointTransactionType(enum.Enum):
    """积分交易类型枚举"""
    recharge = "recharge"
    gift = "gift"
    consume = "consume"
    refund = "refund"
    adjust = "adjust"


class PointSourceType(enum.Enum):
    """积分来源类型枚举"""
    online_payment = "online_payment"
    offline_payment = "offline_payment"
    admin_gift = "admin_gift"
    admin_adjust = "admin_adjust"
    ai_consume = "ai_consume"
```

---

## 3. API 接口设计

### 3.1 企业管理 API（后台管理员）

**路由前缀**: `/api/v1/admin/enterprises`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/enterprises` | 获取企业列表（分页） | 管理员 |
| POST | `/enterprises` | 创建企业 | 管理员 |
| GET | `/enterprises/{id}` | 获取企业详情 | 管理员 |
| PATCH | `/enterprises/{id}` | 更新企业信息 | 管理员 |
| DELETE | `/enterprises/{id}` | 删除企业 | 管理员 |
| POST | `/enterprises/{id}/add-points` | 手动增加积分 | 管理员 |

### 3.2 企业用户管理 API（企业管理员）

**路由前缀**: `/api/v1/enterprise/users`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/users` | 获取企业用户列表 | 企业管理员 |
| POST | `/users` | 创建企业用户 | 企业管理员 |
| PATCH | `/users/{id}` | 更新用户信息 | 企业管理员 |
| DELETE | `/users/{id}` | 删除用户 | 企业管理员 |

### 3.3 积分充值 API（企业管理员）

**路由前缀**: `/api/v1/enterprise/points`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/balance` | 获取企业积分余额 | 企业管理员 |
| POST | `/recharge` | 充值积分（预留支付接口） | 企业管理员 |
| GET | `/transactions` | 获取积分交易记录 | 企业管理员 |

### 3.4 AI 消费记录 API（企业管理员）

**路由前缀**: `/api/v1/enterprise/consumptions`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/` | 获取 AI 消费记录（分页、筛选） | 企业管理员 |
| GET | `/stats` | 获取消费统计 | 企业管理员 |

### 3.5 模型汇率配置 API（管理员）

**路由前缀**: `/api/v1/admin/point-rates`

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/` | 获取汇率配置列表 | 管理员 |
| POST | `/` | 创建汇率配置 | 管理员 |
| PATCH | `/{id}` | 更新汇率配置 | 管理员 |
| DELETE | `/{id}` | 删除汇率配置 | 管理员 |

---

## 4. 前端页面设计

### 4.1 后台管理后台

**侧边栏菜单调整**（与用户管理同级）：

```vue
<el-menu>
  <el-menu-item index="/admin/users">用户管理</el-menu-item>

  <el-sub-menu index="enterprise">
    <template #title>
      <el-icon><OfficeBuilding /></el-icon>
      <span>企业管理</span>
    </template>
    <el-menu-item index="/admin/enterprises">企业列表</el-menu-item>
  </el-sub-menu>

  <!-- ... 其他菜单 ... -->
</el-menu>
```

**新增页面**：
- `AdminEnterprisesPage.vue` - 企业 CRUD、手动充值/赠送
- 汇率配置集成到 `AdminModelProvidersPage.vue` 中

### 4.2 企业管理后台（新增）

**路由**: `/enterprise/*`

**侧边栏菜单**：
```vue
<el-menu>
  <el-menu-item index="/enterprise">
    <el-icon><DataBoard /></el-icon>
    <span>概览</span>
  </el-menu-item>
  <el-menu-item index="/enterprise/users">用户管理</el-menu-item>
  <el-menu-item index="/enterprise/transactions">充值记录</el-menu-item>
  <el-menu-item index="/enterprise/consumptions">消费记录</el-menu-item>
</el-menu>
```

**页面列表**：
- `EnterpriseDashboardPage.vue` - 概览 Dashboard
- `EnterpriseUsersPage.vue` - 用户管理
- `PointTransactionsPage.vue` - 充值记录
- `AIConsumptionsPage.vue` - 消费记录

### 4.3 EnterpriseDashboardPage 布局

```
┌─────────────────────────────────────────────────────────────────┐
│  XX 企业  |  状态：正常  |  用户数：25                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  总积分      │  │  充值积分    │  │  赠送积分    │          │
│  │  10,000      │  │  7,000       │  │  3,000       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  [在线充值]  [充值记录]  [消费记录]                          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │  本月消耗趋势        │  │  模型使用分布                   │  │
│  │  [折线图]            │  │  [饼图/柱状图]                  │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  用户消耗排名 Top 10                                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 扣费逻辑设计

### 5.1 扣费流程

```
用户发起 AI 请求
    │
    ▼
1. 请求前检查
   - 获取用户所属企业
   - 检查企业总积分 > 0
   - 如果 ≤ 0，返回错误："积分不足，请联系企业管理员充值"
    │
    ▼
2. 调用 AI 服务（chat_stream）
   - 正常调用 LLM API
   - 获取响应内容和 token 使用信息
    │
    ▼
3. 计算积分消耗
   - 根据模型和 token 数量查询汇率配置
   - 计算消耗积分：total_tokens / tokens_per_point
    │
    ▼
4. 扣减积分（事务）
   a. 先扣赠送积分
   b. 再扣充值积分
   c. 如果不够，产生负债（debt_points 增加）
    │
    ▼
5. 记录消费日志
   - 写入 ai_consumptions 表
```

### 5.2 核心服务：PointService

```python
class PointService:
    """积分服务"""

    def check_points_before_request(self, user_id: str) -> bool:
        """请求前检查积分是否足够"""
        enterprise = self._get_user_enterprise(user_id)
        return enterprise.total_points > 0

    def calculate_points_from_tokens(
        self, provider_code: str, model_code: str,
        prompt_tokens: int, completion_tokens: int
    ) -> int:
        """根据 token 计算积分"""
        rate = self._get_model_rate(provider_code, model_code)
        tokens_per_point = rate.tokens_per_point if rate else 1000
        total_tokens = prompt_tokens + completion_tokens
        return max(1, (total_tokens + tokens_per_point - 1) // tokens_per_point)

    def deduct_points(self, enterprise_id: str, user_id: str, ...):
        """扣减积分（事务）
        - 先扣赠送积分
        - 再扣充值积分
        - 不够则产生负债
        """
        # 详见设计文档第 5.3 节
```

### 5.3 积分扣减算法

```
输入：需扣减积分 points

1. 获取企业余额（加行锁）
   balance_gratis, balance_paid, debt_points

2. 计算扣减分配
   gratis_to_deduct = min(balance_gratis, points)
   paid_to_deduct = points - gratis_to_deduct

3. 执行扣减
   balance_gratis -= gratis_to_deduct

   if paid_to_deduct <= balance_paid:
       balance_paid -= paid_to_deduct
   else:
       remaining = paid_to_deduct - balance_paid
       balance_paid = 0
       debt_points += remaining

4. 创建消费记录
```

### 5.4 积分充值算法

```
输入：增加积分 amount, 来源 source_type

1. 获取企业余额（加行锁）

2. 优先抵扣负债
   if debt_points > 0:
       debt_to_clear = min(debt_points, amount)
       debt_points -= debt_to_clear
       remaining = amount - debt_to_clear
   else:
       remaining = amount

3. 剩余部分增加余额
   if remaining > 0:
       if source_type == admin_gift:
           balance_gratis += remaining
       else:
           balance_paid += remaining

4. 创建交易记录
```

### 5.5 错误处理

| 场景 | 处理方式 |
|------|----------|
| 用户未关联企业 | 拒绝请求，返回错误 |
| 积分 ≤ 0 | 拒绝请求，返回"积分不足"提示 |
| 扣费失败 | 记录日志，允许请求完成（不阻塞 AI 响应） |
| 汇率配置不存在 | 使用默认汇率（1000 tokens = 1 积分） |

---

## 6. 数据库迁移

### 6.1 迁移步骤

1. 创建新表（enterprises, point_transactions, ai_consumptions, model_point_rates）
2. 修改 users 表（添加 enterprise_id, is_enterprise_admin 字段）
3. 修改 model_configs 表（添加 point_rate 关系）
4. 创建默认企业（可选）
5. 将现有用户关联到默认企业（可选）

### 6.2 初始数据

- 创建默认汇率配置（主流模型的默认汇率）

---

## 7. 实现计划

### 7.1 后端实现

1. **数据模型**
   - 创建新的 ORM 模型
   - 创建数据库迁移脚本

2. **服务层**
   - EnterpriseService（企业管理）
   - PointService（积分管理）
   - 扩展 AIService（集成扣费）

3. **接口层**
   - 企业管理路由
   - 积分充值路由
   - 消费记录路由
   - 汇率配置路由

4. **权限控制**
   - require_admin 依赖（已存在）
   - require_enterprise_admin 依赖（新增）

### 7.2 前端实现

1. **类型定义**
   - 扩展 UserInfo（企业信息）
   - 企业相关 API 类型

2. **布局组件**
   - EnterpriseLayout.vue
   - 更新 AdminLayout.vue

3. **页面组件**
   - AdminEnterprisesPage.vue
   - EnterpriseDashboardPage.vue
   - EnterpriseUsersPage.vue
   - PointTransactionsPage.vue
   - AIConsumptionsPage.vue

4. **API 客户端**
   - 企业相关 API 方法

### 7.3 测试

1. 单元测试（服务层）
2. 集成测试（API 层）
3. E2E 测试（扣费流程）

---

## 8. 验收标准

1. 后台管理员可以创建/编辑/删除企业
2. 后台管理员可以给企业手动充值/赠送积分
3. 企业管理员可以创建企业用户
4. 企业管理员可以查看积分余额和充值记录
5. 企业管理员可以查看 AI 消费记录和统计
6. 用户使用 AI 时自动扣减积分
7. 积分不足时无法发起 AI 请求
8. 汇率配置可以按模型单独设置

---

## 9. 后续扩展

1. 在线支付接口（工商银行 + 微信/支付宝扫码）
2. 积分明细导出功能
3. 企业配额管理（限制用户数、月消费额度等）
4. 消费预警（积分不足时通知）
5. 消费统计报表
