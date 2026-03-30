# 退款状态流转修复实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复退款状态流转逻辑，工行退款接口返回成功只表示请求已接收，需要调用查询接口确认最终状态

**Architecture:**
- 发起退款后等待2秒，调用查询接口确认最终状态
- 新增 `icbc_query_response` 字段保存查询响应
- 支持手动刷新处理中的退款状态

**Tech Stack:**
- 后端: FastAPI, SQLAlchemy, Alembic, asyncio
- 前端: Vue 3, TypeScript, Element Plus

---

## 文件结构

### 后端文件
| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/src/db_models.py` | 修改 | PaymentRefundModel 新增 icbc_query_response 字段 |
| `backend/alembic/versions/xxx_add_icbc_query_response.py` | 创建 | 数据库迁移文件 |
| `backend/src/services/refund_service.py` | 修改 | 修改 create_refund 和 query_refund_status 方法 |
| `backend/src/interfaces/routers/admin/payment_admin.py` | 验证 | 确认现有查询接口使用新字段 |
| `backend/tests/unit/test_refund_service.py` | 修改 | 更新单元测试 |
| `backend/tests/integration/test_refund_flow.py` | 修改 | 更新集成测试 |

### 前端文件
| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/views/admin/RefundManagement.vue` | 修改 | 处理中状态显示刷新按钮 |
| `frontend/src/api/types.ts` | 修改 | 新增退款查询接口类型定义（如果需要）|

---

## Task 1: 数据库迁移 - 新增 icbc_query_response 字段

**Files:**
- Create: `backend/alembic/versions/YYYYMMDDHHMMSS_add_icbc_query_response.py`
- Modify: `backend/src/db_models.py:610-648`

- [ ] **Step 1: 创建数据库迁移文件**

运行以下命令生成迁移：
```bash
cd backend
alembic revision -m "add_icbc_query_response"
```

预期：生成新的迁移文件，如 `backend/alembic/versions/xxxxxxxxxxxx_add_icbc_query_response.py`

- [ ] **Step 2: 编写迁移内容**

编辑生成的迁移文件，内容如下：

```python
# -*- coding: utf-8 -*-
"""add icbc_query_response to payment_refunds

Revision ID: <自动生成的ID>
Revises: <上一个迁移的ID>
Create Date: <自动生成的时间>

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '<自动生成的ID>'
down_revision = '<上一个迁移的ID>'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('payment_refunds',
        sa.Column('icbc_query_response', sa.JSON(), nullable=True, comment='工行退款查询接口响应')
    )


def downgrade():
    op.drop_column('payment_refunds', 'icbc_query_response')
```

- [ ] **Step 3: 更新数据模型**

修改 `backend/src/db_models.py` 中 `PaymentRefundModel` 类，约在第 628 行后添加：

```python
class PaymentRefundModel(Base):
    # ... 现有字段 ...
    icbc_refund_response = Column(JSON, nullable=True, comment='工行退款发起接口响应')
    icbc_query_response = Column(JSON, nullable=True, comment='工行退款查询接口响应')  # 新增

    # 操作信息
    operator_id = ...
```

- [ ] **Step 4: 应用迁移**

```bash
cd backend
alembic upgrade head
```

预期输出：`Running upgrade xxx -> yyy, add_icbc_query_response`

- [ ] **Step 5: 验证字段已添加**

```bash
mysql -u root -p -e "DESCRIBE ai_teacher_platform.payment_refunds;"
```

预期输出中包含 `icbc_query_response` 字段

- [ ] **Step 6: 提交数据库修改**

```bash
git add backend/src/db_models.py backend/alembic/versions/
git commit -m "feat: 新增 icbc_query_response 字段保存退款查询响应"
```

---

## Task 2: 修改退款服务 - 提取查询状态解析逻辑

**Files:**
- Modify: `backend/src/services/refund_service.py`

- [ ] **Step 1: 先编写测试 - 查询状态解析逻辑**

在 `backend/tests/unit/test_refund_service.py` 末尾添加：

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.refund_service import RefundService
from src.db_models import RefundStatus

class TestRefundStatusParsing:
    """测试退款状态解析逻辑"""

    @pytest.fixture
    def service(self, db_session):
        mock_client = Mock()
        return RefundService(db_session, mock_client)

    def test_parse_query_response_success(self, service):
        """测试解析查询响应 - 成功"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "0",
                "real_reject_amt": "100"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_success
        assert timestamp_field == "success_at"

    def test_parse_query_response_failed(self, service):
        """测试解析查询响应 - 失败"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "1"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_failed
        assert timestamp_field == "failed_at"

    def test_parse_query_response_processing(self, service):
        """测试解析查询响应 - 处理中"""
        query_response = {
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "2"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing
        assert timestamp_field is None

    def test_parse_query_response_missing_biz_content(self, service):
        """测试解析查询响应 - 缺少 response_biz_content"""
        query_response = {"return_code": "0"}
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing  # 默认为处理中
        assert timestamp_field is None

    def test_parse_query_response_missing_pay_status(self, service):
        """测试解析查询响应 - 缺少 pay_status"""
        query_response = {
            "response_biz_content": {
                "return_code": "0"
            }
        }
        status, timestamp_field = service._parse_query_status(query_response)
        assert status == RefundStatus.refund_processing
        assert timestamp_field is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend
pytest tests/unit/test_refund_service.py::TestRefundStatusParsing -v
```

预期：`AttributeError: 'RefundService' object has no attribute '_parse_query_status'`

- [ ] **Step 3: 实现 _parse_query_status 方法**

在 `RefundService` 类中添加新方法（约在第 40 行，`_generate_refund_no` 方法后）：

```python
def _parse_query_status(self, query_response: dict) -> tuple[RefundStatus, str | None]:
    """
    解析工行查询接口响应，确定退款状态

    Args:
        query_response: 工行查询接口响应

    Returns:
        (退款状态, 需要更新时间戳的字段名)
    """
    # 获取 response_biz_content
    if "response_biz_content" in query_response:
        biz_content = query_response["response_biz_content"]
    else:
        # 没有业务内容，保持处理中状态
        return RefundStatus.refund_processing, None

    pay_status = biz_content.get("pay_status")

    if pay_status == "0":
        return RefundStatus.refund_success, "success_at"
    elif pay_status == "1":
        return RefundStatus.refund_failed, "failed_at"
    else:
        # pay_status == "2" 或其他未知值，保持处理中
        return RefundStatus.refund_processing, None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend
pytest tests/unit/test_refund_service.py::TestRefundStatusParsing -v
```

预期：5 passed

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/refund_service.py backend/tests/unit/test_refund_service.py
git commit -m "feat: 新增 _parse_query_status 方法解析查询响应状态"
```

---

## Task 3: 修改 create_refund 方法 - 发起退款后查询状态

**Files:**
- Modify: `backend/src/services/refund_service.py:67-172`

- [ ] **Step 1: 编写测试 - 发起退款成功后查询状态**

在 `backend/tests/unit/test_refund_service.py` 中添加：

```python
class TestRefundCreationWithQuery:
    """测试退款创建后的状态查询"""

    @pytest.fixture
    def service(self, db_session):
        mock_client = Mock()
        return RefundService(db_session, mock_client)

    @pytest.fixture
    def payment_order(self, db_session):
        from src.db_models import PaymentOrderModel, PaymentOrderStatus
        order = PaymentOrderModel(
            id="test-order-id",
            user_id="test-user-id",
            out_trade_no="TEST20260330001",
            amount=1000,
            status=PaymentOrderStatus.paid,
            pay_channel="icbc_aggregate"
        )
        db_session.add(order)
        db_session.commit()
        return order

    @pytest.mark.asyncio
    async def test_create_refund_success_then_query_success(self, service, payment_order):
        """测试发起退款成功，查询返回成功"""
        # 模拟退款接口返回成功
        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "0",
            "intrx_serial_no": "icbc-refund-no",
            "response_biz_content": {...}
        })
        # 模拟查询接口返回成功
        service.icbc_client.query_refund = AsyncMock(return_value={
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "0",  # 成功
                "real_reject_amt": "100"
            }
        })

        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator",
            operator_name="测试"
        )

        assert refund.status == RefundStatus.refund_success
        assert refund.icbc_refund_response is not None
        assert refund.icbc_query_response is not None

    @pytest.mark.asyncio
    async def test_create_refund_success_then_query_processing(self, service, payment_order):
        """测试发起退款成功，查询返回处理中"""
        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "0"
        })
        service.icbc_client.query_refund = AsyncMock(return_value={
            "response_biz_content": {
                "return_code": "0",
                "pay_status": "2"  # 处理中
            }
        })

        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator"
        )

        assert refund.status == RefundStatus.refund_processing

    @pytest.mark.asyncio
    async def test_create_refund_initiate_failed(self, service, payment_order):
        """测试发起退款失败"""
        service.icbc_client.refund_order = AsyncMock(return_value={
            "return_code": "400017",  # 签名验证失败
            "return_msg": "签名验证失败"
        })

        refund = await service.create_refund(
            payment_order_id=payment_order.id,
            refund_amount=100,
            operator_id="test-operator"
        )

        assert refund.status == RefundStatus.refund_failed
        assert refund.icbc_refund_response is not None
        # 发起失败时不会调用查询接口
        assert refund.icbc_query_response is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend
pytest tests/unit/test_refund_service.py::TestRefundCreationWithQuery -v
```

预期：测试失败（当前实现没有查询逻辑）

- [ ] **Step 3: 修改 create_refund 方法**

完全替换 `create_refund` 方法（第 67-172 行）：

```python
async def create_refund(
    self,
    payment_order_id: str,
    refund_amount: int,
    operator_id: str,
    operator_name: str = "",
    refund_reason: str = "",
) -> PaymentRefundModel:
    """
    创建退款订单

    Args:
        payment_order_id: 支付订单ID
        refund_amount: 退款金额（分）
        operator_id: 操作人ID
        operator_name: 操作人姓名
        refund_reason: 退款原因

    Returns:
        退款订单

    Raises:
        ValueError: 订单不允许退款
        Exception: 工行接口调用失败
    """
    import asyncio  # 新增导入

    # 查询支付订单
    payment_order = self.db.query(PaymentOrderModel).filter(
        PaymentOrderModel.id == payment_order_id
    ).first()

    if not payment_order:
        raise ValueError(f"支付订单不存在: {payment_order_id}")

    # 检查是否可以退款
    if not self._can_refund(payment_order, refund_amount):
        raise ValueError("订单不允许退款或退款金额超过可退金额")

    # 生成退款流水号
    out_refund_no = self._generate_refund_no()

    # 创建退款订单
    refund = PaymentRefundModel(
        id=str(uuid.uuid4()),
        out_refund_no=out_refund_no,
        payment_order_id=payment_order_id,
        refund_amount=refund_amount,
        status=RefundStatus.refund_created,
        operator_id=operator_id,
        operator_name=operator_name,
        refund_reason=refund_reason,
        submitted_at=datetime.now(),
    )

    self.db.add(refund)
    self.db.flush()  # 获取 refund.id

    logger.info(f"创建退款订单: {refund.id}, 流水号: {out_refund_no}")

    try:
        # 调用工行退款接口
        icbc_response = await self.icbc_client.refund_order(
            out_trade_no=payment_order.out_trade_no,
            out_refund_no=out_refund_no,
            refund_amount=refund_amount,
            order_id=payment_order.third_trade_no,
        )

        # 保存工行响应
        refund.icbc_refund_response = icbc_response

        # 解析响应
        return_code = icbc_response.get("return_code")
        if return_code != "0":
            # 发起失败
            refund.status = RefundStatus.refund_failed
            refund.failed_at = datetime.now()
            logger.warning(f"退款发起失败: {refund.id}, 错误码: {return_code}")
        else:
            # 发起成功，等待2秒后查询状态
            logger.info(f"退款发起成功，等待2秒后查询: {refund.id}")
            await asyncio.sleep(2)

            try:
                # 调用工行查询接口
                query_response = await self.icbc_client.query_refund(
                    out_trade_no=payment_order.out_trade_no,
                    out_refund_no=out_refund_no,
                    order_id=payment_order.third_trade_no,
                )

                # 保存查询响应
                refund.icbc_query_response = query_response

                # 解析查询结果
                status, timestamp_field = self._parse_query_status(query_response)
                refund.status = status

                # 更新时间戳
                if timestamp_field:
                    setattr(refund, timestamp_field, datetime.now())

                # 更新实际退款金额
                if status == RefundStatus.refund_success:
                    biz_content = query_response.get("response_biz_content", {})
                    if "real_reject_amt" in biz_content:
                        try:
                            refund.real_refund_amount = int(biz_content["real_reject_amt"])
                        except (ValueError, TypeError):
                            pass

                logger.info(f"退款查询完成: {refund.id}, 状态: {status.value}")

            except Exception as e:
                # 查询失败，保持处理中状态
                logger.error(f"退款查询失败: {refund.id}, 错误: {e}")
                refund.status = RefundStatus.refund_processing

        # 更新支付订单的退款统计
        payment_order.refunded_amount += refund_amount
        payment_order.refund_count += 1

        self.db.commit()
        self.db.refresh(refund)

        return refund

    except Exception as e:
        # 回滚退款创建
        self.db.rollback()
        logger.error(f"创建退款失败: {e}")
        raise
```

- [ ] **Step 4: 在文件顶部添加 asyncio 导入**

在 `backend/src/services/refund_service.py` 顶部的导入区域添加：

```python
import asyncio  # 添加这行
import logging
import uuid
```

- [ ] **Step 5: 运行测试确认通过**

```bash
cd backend
pytest tests/unit/test_refund_service.py::TestRefundCreationWithQuery -v
```

预期：3 passed

- [ ] **Step 6: 运行所有退款服务测试**

```bash
cd backend
pytest tests/unit/test_refund_service.py -v
```

预期：所有测试通过

- [ ] **Step 7: 提交**

```bash
git add backend/src/services/refund_service.py backend/tests/unit/test_refund_service.py
git commit -m "feat: 修改 create_refund 发起退款后查询最终状态"
```

---

## Task 4: 修改 query_refund_status 方法

**Files:**
- Modify: `backend/src/services/refund_service.py:174-252`

- [ ] **Step 1: 更新 query_refund_status 方法**

替换 `query_refund_status` 方法（第 174-252 行）：

```python
async def query_refund_status(self, refund_id: str) -> PaymentRefundModel:
    """
    查询退款状态

    Args:
        refund_id: 退款订单ID

    Returns:
        更新后的退款订单

    Raises:
        ValueError: 退款订单不存在
    """
    # 查询退款订单
    refund = self.db.query(PaymentRefundModel).filter(
        PaymentRefundModel.id == refund_id
    ).first()

    if not refund:
        raise ValueError(f"退款订单不存在: {refund_id}")

    # 如果已经是最终状态，不需要查询
    if refund.status in [RefundStatus.refund_success, RefundStatus.refund_cancelled]:
        return refund

    # 查询关联的支付订单
    payment_order = self.db.query(PaymentOrderModel).filter(
        PaymentOrderModel.id == refund.payment_order_id
    ).first()

    if not payment_order:
        logger.error(f"关联的支付订单不存在: {refund.payment_order_id}")
        return refund

    try:
        # 调用工行查询接口
        icbc_response = await self.icbc_client.query_refund(
            out_trade_no=payment_order.out_trade_no,
            out_refund_no=refund.out_refund_no,
            order_id=payment_order.third_trade_no,
        )

        # 保存查询响应
        refund.icbc_query_response = icbc_response

        # 解析状态（使用统一的解析方法）
        status, timestamp_field = self._parse_query_status(icbc_response)

        # 更新状态
        old_status = refund.status
        refund.status = status

        # 更新时间戳
        if timestamp_field:
            setattr(refund, timestamp_field, datetime.now())

        # 更新实际退款金额（成功时）
        if status == RefundStatus.refund_success and not refund.real_refund_amount:
            biz_content = icbc_response.get("response_biz_content", {})
            if "real_reject_amt" in biz_content:
                try:
                    refund.real_refund_amount = int(biz_content["real_reject_amt"])
                except (ValueError, TypeError):
                    pass

        logger.info(f"退款状态查询: {refund_id}, {old_status.value} -> {status.value}")

        self.db.commit()
        self.db.refresh(refund)

        return refund

    except Exception as e:
        logger.error(f"查询退款状态失败: {e}")
        raise
```

- [ ] **Step 2: 运行所有退款服务测试**

```bash
cd backend
pytest tests/unit/test_refund_service.py -v
```

预期：所有测试通过

- [ ] **Step 3: 添加字段保存位置验证测试**

在 `backend/tests/unit/test_refund_service.py` 中添加：

```python
@pytest.mark.asyncio
async def test_query_refund_saves_to_correct_field(self, service, payment_order, db_session):
    """测试查询响应保存到 icbc_query_response 而不是 icbc_refund_response"""
    from src.db_models import PaymentRefundModel

    # 创建一个退款记录
    refund = PaymentRefundModel(
        id="test-refund-id",
        out_refund_no="TEST20260330001",
        payment_order_id=payment_order.id,
        refund_amount=100,
        status=RefundStatus.refund_processing,
        operator_id="test-operator",
        submitted_at=datetime.now()
    )
    db_session.add(refund)
    db_session.commit()

    # 模拟查询接口返回
    service.icbc_client.query_refund = AsyncMock(return_value={
        "response_biz_content": {
            "return_code": "0",
            "pay_status": "0"
        }
    })

    # 执行查询
    result = await service.query_refund_status(refund.id)

    # 验证：查询响应应该保存到 icbc_query_response
    assert result.icbc_query_response is not None
    assert result.icbc_query_response.get("response_biz_content", {}).get("pay_status") == "0"

    # 刷新数据库确保数据已持久化
    db_session.refresh(result)
    assert result.icbc_query_response is not None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend
pytest tests/unit/test_refund_service.py -v
```

预期：所有测试通过

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/refund_service.py backend/tests/unit/test_refund_service.py
git commit -m "refactor: 修改 query_refund_status 使用统一的解析方法并修复字段保存"
```

---

## Task 5: 验证现有查询接口返回 icbc_query_response

**Files:**
- Verify: `backend/src/interfaces/routers/admin/payment_admin.py`

**注意**: 手动查询接口 `POST /api/v1/admin/payment/refunds/{refund_id}/query` 已经存在于 `payment_admin.py` 第 463-492 行。本任务只需验证其返回值包含 `icbc_query_response` 字段。

- [ ] **Step 1: 查看现有查询接口**

```bash
grep -A 30 "def.*query.*refund" backend/src/interfaces/routers/admin/payment_admin.py
```

确认接口已经存在并查看当前实现

- [ ] **Step 2: 验证返回值包含新字段**

查看 `query_refund_status_api` 函数的返回值，确认 `icbc_query_response` 字段会被返回。由于 `RefundService.query_refund_status` 方法会保存 `icbc_query_response`，接口会自动返回这个字段。

如果需要显式返回，确保返回字典中包含：

```python
return {
    "success": True,
    "data": {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "status": refund.status.value,
        "icbc_refund_response": refund.icbc_refund_response,
        "icbc_query_response": refund.icbc_query_response,  # 确保包含此字段
        # ... 其他字段
    }
}
```

- [ ] **Step 3: 运行后端测试**

```bash
cd backend
pytest tests/unit/test_refund_service.py tests/integration/test_refund_flow.py -v
```

预期：所有测试通过

- [ ] **Step 4: 提交（如果有修改）**

```bash
git add backend/src/interfaces/routers/admin/payment_admin.py
git commit -m "fix: 确保查询接口返回 icbc_query_response 字段"
```

---

## Task 6: 前端 - 添加刷新状态按钮

**Files:**
- Modify: `frontend/src/views/admin/RefundManagement.vue`

- [ ] **Step 1: 查看现有文件结构**

```bash
head -100 frontend/src/views/admin/RefundManagement.vue
```

了解现有表格列结构

- [ ] **Step 2: 添加刷新状态按钮**

在表格的"操作"列中，为 `refund_processing` 状态添加刷新按钮：

```vue
<!-- 在操作列中添加 -->
<el-table-column label="操作" width="180">
  <template #default="{ row }">
    <el-button
      v-if="row.status === 'refund_processing'"
      type="primary"
      size="small"
      :loading="refreshingId === row.id"
      @click="handleRefreshStatus(row)"
    >
      刷新状态
    </el-button>
    <span v-else-if="row.status === 'refund_success'" class="text-success">
      已完成
    </span>
    <span v-else-if="row.status === 'refund_failed'" class="text-danger">
      失败
    </span>
  </template>
</el-table-column>
```

- [ ] **Step 3: 添加刷新状态方法**

在 script 部分添加：

```typescript
const refreshingId = ref<string | null>(null)

// 刷新退款状态
const handleRefreshStatus = async (row: any) => {
  refreshingId.value = row.id
  try {
    // 注意：API 路径是 /api/v1/admin/payment/refunds/{id}/query
    const response = await apiClient.post(`/api/v1/admin/payment/refunds/${row.id}/query`)
    if (response.data.success) {
      ElMessage.success('状态已更新')
      // 刷新列表数据
      fetchRefunds()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询失败')
  } finally {
    refreshingId.value = null
  }
}
```

- [ ] **Step 4: 运行前端开发服务器确认**

```bash
cd frontend
npm run dev
```

访问退款管理页面，确认处理中状态显示刷新按钮

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/admin/RefundManagement.vue
git commit -m "feat: 退款列表添加刷新状态按钮"
```

---

## Task 7: 集成测试验证

**Files:**
- Modify: `backend/tests/integration/test_refund_flow.py`

- [ ] **Step 1: 更新集成测试**

修改集成测试以验证新的状态流转：

```python
@pytest.mark.asyncio
async def test_refund_with_query_flow(db_session, mock_icbc_client):
    """测试完整的退款流程：发起 -> 查询 -> 完成"""

    # 1. 创建支付订单
    payment_order = create_test_payment_order(db_session, amount=1000)
    payment_order.status = PaymentOrderStatus.paid
    db_session.commit()

    # 2. 设置 mock 响应
    mock_icbc_client.refund_order = AsyncMock(return_value={
        "return_code": "0",  # 发起成功
        "intrx_serial_no": "icbc-123",
    })

    mock_icbc_client.query_refund = AsyncMock(return_value={
        "response_biz_content": {
            "return_code": "0",
            "pay_status": "0",  # 查询返回成功
            "real_reject_amt": "100"
        }
    })

    # 3. 创建退款
    service = RefundService(db_session, mock_icbc_client)
    refund = await service.create_refund(
        payment_order_id=payment_order.id,
        refund_amount=100,
        operator_id="test-operator"
    )

    # 4. 验证状态
    assert refund.status == RefundStatus.refund_success
    assert refund.icbc_refund_response is not None
    assert refund.icbc_query_response is not None
    assert refund.real_refund_amount == 100

    # 5. 验证调用
    mock_icbc_client.refund_order.assert_called_once()
    mock_icbc_client.query_refund.assert_called_once()
```

- [ ] **Step 2: 运行集成测试**

```bash
cd backend
pytest tests/integration/test_refund_flow.py -v
```

预期：所有测试通过

- [ ] **Step 3: 运行所有后端测试**

```bash
cd backend
pytest tests/unit/test_refund_service.py tests/integration/test_refund_flow.py -v
```

预期：所有测试通过

- [ ] **Step 4: 提交**

```bash
git add backend/tests/integration/test_refund_flow.py
git commit -m "test: 更新集成测试验证新的状态流转"
```

---

## 验收标准

所有任务完成后，验证以下功能：

1. [ ] 发起退款后，如果工行接收成功（return_code=0），会自动等待2秒后查询状态
2. [ ] 发起退款后，如果工行接收失败（return_code≠0），状态设为 `refund_failed`
3. [ ] 查询返回 `pay_status=0` 时，状态设为 `refund_success`
4. [ ] 查询返回 `pay_status=1` 时，状态设为 `refund_failed`
5. [ ] 查询返回 `pay_status=2` 时，状态设为 `refund_processing`
6. [ ] `icbc_refund_response` 保存退款发起接口的响应
7. [ ] `icbc_query_response` 保存查询接口的响应
8. [ ] 前端"处理中"状态的退款记录显示"刷新状态"按钮
9. [ ] 点击刷新按钮后能正确更新退款状态
10. [ ] 所有单元测试和集成测试通过

## 测试命令

```bash
# 后端单元测试
cd backend && pytest tests/unit/test_refund_service.py -v

# 后端集成测试
cd backend && pytest tests/integration/test_refund_flow.py -v

# 前端测试
cd frontend && npm run test:e2e
```
