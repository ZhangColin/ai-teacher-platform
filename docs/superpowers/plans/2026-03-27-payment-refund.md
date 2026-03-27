# 支付退款功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为管理后台添加退款功能，支持部分退款和多次退款，仅管理员可操作。

**Architecture:** 在现有支付系统基础上，新增退款订单模型、退款服务、工行退款客户端方法，以及管理后台退款管理页面。退款不处理积分回退。

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, TypeScript, Element Plus, httpx, cryptography

---

## 文件结构

```
backend/src/
├── db_models.py                         # 修改：添加 RefundStatus 枚举、PaymentRefundModel
├── models.py                            # 修改：添加退款相关 Pydantic 模型
├── services/
│   ├── icbc_qrcode_client.py            # 修改：添加 refund_order、query_refund 方法
│   └── refund_service.py                # 新增：退款服务
└── interfaces/
    └── routers/
        └── admin/
            └── payment_admin.py          # 修改：添加退款相关 API

backend/tests/
├── unit/
│   └── test_refund_service.py           # 新增：退款服务测试
└── integration/
    └── test_refund_flow.py              # 新增：退款流程测试

alembic/versions/
└── xxx_add_payment_refunds.py           # 新增：数据库迁移

frontend/src/
├── types/index.ts                       # 修改：添加退款相关类型
├── router/index.ts                      # 修改：添加退款管理路由
├── views/admin/
│   ├── RefundManagement.vue             # 新增：退款管理页面
│   └── PaymentOrdersView.vue            # 修改：添加退款相关按钮和列
└── layouts/
    └── AdminLayout.vue                  # 修改：添加退款管理菜单
```

---

## Task 1: 数据库模型修改

**Files:**
- Modify: `backend/src/db_models.py:100-120` (添加枚举)
- Modify: `backend/src/db_models.py:590-595` (添加 PaymentRefundModel)
- Modify: `backend/src/db_models.py:580` (添加退款统计字段)
- Create: `alembic/versions/xxx_add_payment_refunds.py`

- [ ] **Step 1: 添加退款状态枚举**

在 `db_models.py` 文件中，在 `PaymentOrderStatus` 枚举后面添加 `RefundStatus` 枚举：

```python
class RefundStatus(str, enum.Enum):
    """退款状态枚举"""
    refund_created = "refund_created"      # 退款已创建
    refund_processing = "refund_processing" # 退款处理中
    refund_success = "refund_success"       # 退款成功
    refund_failed = "refund_failed"         # 退款失败
    refund_cancelled = "refund_cancelled"   # 退款取消
```

- [ ] **Step 2: 添加退款订单模型**

在 `PaymentOrderModel` 类定义之后，添加 `PaymentRefundModel` 类：

```python
class PaymentRefundModel(Base):
    """退款订单数据库模型"""
    __tablename__ = "payment_refunds"

    # 基础字段
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    out_refund_no = Column(String(64), unique=True, nullable=False, index=True, comment='商户退款流水号')
    payment_order_id = Column(CHAR(36), ForeignKey("payment_orders.id"), nullable=False, index=True, comment='关联支付订单ID')

    # 金额
    refund_amount = Column(Integer, nullable=False, comment='退款金额（分）')
    real_refund_amount = Column(Integer, nullable=True, comment='实际退款金额（分）')

    # 状态
    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.refund_created, index=True)

    # 工行返回数据
    third_refund_no = Column(String(64), nullable=True, comment='工行退款流水号')
    icbc_refund_response = Column(JSON, nullable=True, comment='工行退款完整响应')

    # 操作信息
    operator_id = Column(CHAR(36), nullable=False, comment='操作人ID')
    operator_name = Column(String(50), nullable=True, comment='操作人姓名')
    refund_reason = Column(String(200), nullable=True, comment='退款原因')

    # 时间记录
    submitted_at = Column(DateTime, nullable=True, comment='发起退款时间')
    success_at = Column(DateTime, nullable=True, comment='退款成功时间')
    failed_at = Column(DateTime, nullable=True, comment='退款失败时间')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 联合索引
    __table_args__ = (
        Index("idx_refund_payment", "payment_order_id"),
        Index("idx_refund_status", "status"),
        Index("idx_refund_created", "created_at"),
    )
```

- [ ] **Step 3: 添加支付订单退款统计字段**

在 `PaymentOrderModel` 类中，找到 `notified_at` 字段之后，添加两个字段：

```python
# 退款统计
refunded_amount = Column(Integer, nullable=False, default=0, comment='已退款金额（分）')
refund_count = Column(Integer, nullable=False, default=0, comment='退款次数')
```

- [ ] **Step 4: 创建数据库迁移**

```bash
cd backend
alembic revision --autogenerate -m "add_payment_refunds"
```

预期：生成迁移文件在 `alembic/versions/` 目录

- [ ] **Step 5: 检查迁移文件内容**

打开生成的迁移文件，确认包含：
- `payment_refunds` 表创建
- `payment_orders` 表的 `refunded_amount` 和 `refund_count` 字段添加

- [ ] **Step 6: 执行迁移**

```bash
alembic upgrade head
```

预期：输出 "Running upgrade" 并成功

- [ ] **Step 7: 验证数据库表结构**

```bash
mysql -u root -p -e "DESCRIBE ai_teacher_platform.payment_refunds;" | head -20
```

预期：显示 payment_refunds 表结构，包含所有字段

- [ ] **Step 8: 提交**

```bash
git add backend/src/db_models.py alembic/versions/
git commit -m "feat: 添加退款订单数据库模型"
```

---

## Task 2: Pydantic 模型添加

**Files:**
- Modify: `backend/src/models.py:400-500` (在支付相关模型后添加)

- [ ] **Step 1: 添加退款请求模型**

在 `models.py` 文件末尾添加：

```python
# ==================== 退款模块 ====================

class CreateRefundRequest(BaseModel):
    """创建退款请求"""
    payment_order_id: str = Field(..., description="支付订单ID")
    refund_amount: int = Field(..., ge=1, description="退款金额（分），最小1分")
    refund_reason: str = Field("", max_length=200, description="退款原因")


class RefundListItem(BaseModel):
    """退款订单列表项"""
    id: str
    out_refund_no: str
    payment_order_id: str
    payment_order_out_trade_no: Optional[str] = None  # 关联的支付订单号
    refund_amount: int
    real_refund_amount: Optional[int] = None
    status: str
    third_refund_no: Optional[str] = None
    operator_id: str
    operator_name: Optional[str] = None
    refund_reason: Optional[str] = None
    submitted_at: Optional[str] = None
    success_at: Optional[str] = None
    failed_at: Optional[str] = None
    created_at: str


class RefundListResponse(BaseModel):
    """退款订单列表响应"""
    items: List[RefundListItem]
    total: int
    page: int
    page_size: int


class RefundDetailResponse(BaseModel):
    """退款订单详情响应"""
    id: str
    out_refund_no: str
    payment_order_id: str
    payment_order_out_trade_no: Optional[str] = None
    payment_order_amount: Optional[int] = None
    refund_amount: int
    real_refund_amount: Optional[int] = None
    status: str
    third_refund_no: Optional[str] = None
    icbc_refund_response: Optional[dict] = None
    operator_id: str
    operator_name: Optional[str] = None
    refund_reason: Optional[str] = None
    submitted_at: Optional[str] = None
    success_at: Optional[str] = None
    failed_at: Optional[str] = None
    created_at: str
    updated_at: str
```

- [ ] **Step 2: 修改 PaymentOrderResponse 模型**

找到 `PaymentOrderResponse` 类定义，在 `notified_at` 字段后添加：

```python
    # 退款统计
    refunded_amount: int = Field(0, description="已退款金额（分）")
    refund_count: int = Field(0, description="退款次数")
```

- [ ] **Step 3: 验证导入**

```bash
cd backend
python -c "from backend.src.models import CreateRefundRequest, RefundListItem, RefundListResponse, RefundDetailResponse; print('Import OK')"
```

预期：Import OK

- [ ] **Step 4: 提交**

```bash
git add backend/src/models.py
git commit -m "feat: 添加退款相关 Pydantic 模型"
```

---

## Task 3: 工行客户端退款方法

**Files:**
- Modify: `backend/src/services/icbc_qrcode_client.py:428-450`

- [ ] **Step 1: 添加退款API端点常量**

在 `IcbcQrCodeClient` 类中，找到 `API_QUERY_ORDER` 常量后添加：

```python
    # 新增API端点
    API_REFUND_ORDER = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1"
    API_QUERY_REFUND = "https://gw.open.icbc.com.cn/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1"
```

- [ ] **Step 2: 添加发起退款方法**

在 `query_order` 方法后，添加 `refund_order` 方法：

```python
    async def refund_order(
        self,
        out_trade_no: str,
        out_refund_no: str,
        refund_amount: int,
        order_id: str = None,
    ) -> dict:
        """
        发起退款

        Args:
            out_trade_no: 商户订单号
            out_refund_no: 商户退款流水号
            refund_amount: 退款金额（分）
            order_id: 工行订单号（可选，与out_trade_no二选一）

        Returns:
            工行响应结果
            {
                "return_code": "0",  # 0=成功
                "return_msg": "success",
                "outtrx_serial_no": "商户退款流水号",
                "intrx_serial_no": "工行退款流水号",
                "reject_amt": "退款金额（分）",
                "real_reject_amt": "实际退款金额（分）"
            }
        """
        # 生成 msg_id
        msg_id = self._generate_msg_id()

        # 当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建 biz_content
        biz_content = {
            "mer_id": self.mer_id,
            "out_trade_no": out_trade_no,
            "outtrx_serial_no": out_refund_no,
            "ret_total_amt": str(refund_amount),
            "trnsc_ccy": "001",  # 人民币
            "icbc_appid": self.app_id,
            "mer_prtcl_no": self.mer_prtcl_no,
            "order_apd_inf": "",  # 订单附加信息
        }

        # 如果有工行订单号，添加到biz_content
        if order_id:
            biz_content["order_id"] = order_id

        # 构建请求参数
        params = {
            "app_id": self.app_id,
            "msg_id": msg_id,
            "format": "json",
            "charset": "UTF-8",
            "sign_type": "RSA2",
            "timestamp": timestamp,
            "biz_content": json.dumps(biz_content, ensure_ascii=False),
        }

        # 签名 - 需要传入 URL 路径
        sign_str = self._build_sign_str(params, "/api/cardbusiness/aggregatepay/b2c/online/merrefund/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行退款请求 - 订单号:{out_trade_no}, 退款金额:{refund_amount}分, msg_id:{msg_id}")
        logger.debug(f"签名原文: {sign_str}")

        # 按照工行文档格式：所有参数放在 body 中（form-urlencoded 格式）
        body_params = {
            "app_id": params["app_id"],
            "msg_id": params["msg_id"],
            "format": params["format"],
            "charset": params["charset"],
            "sign_type": params["sign_type"],
            "timestamp": params["timestamp"],
            "sign": params["sign"],
            "biz_content": params["biz_content"],  # JSON 字符串
        }

        logger.debug(f"请求Body参数: {body_params}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_REFUND_ORDER,
                data=body_params,  # form-urlencoded 格式
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行退款响应 - 订单号:{out_trade_no}, 响应码:{result.get('return_code')}")
        logger.debug(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        return result
```

- [ ] **Step 3: 添加退款查询方法**

在 `refund_order` 方法后，添加 `query_refund` 方法：

```python
    async def query_refund(
        self,
        out_trade_no: str,
        out_refund_no: str,
        order_id: str = None,
    ) -> dict:
        """
        查询退款状态

        Args:
            out_trade_no: 商户订单号
            out_refund_no: 商户退款流水号
            order_id: 工行订单号（可选）

        Returns:
            工行响应结果
            {
                "return_code": "0",
                "return_msg": "success",
                "pay_status": "0",  # 0=成功, 1=失败, 2=未知
                "outtrx_serial_no": "商户退款流水号",
                "intrx_serial_no": "工行退款流水号",
                "reject_amt": "退款总金额（分）",
                "real_reject_amt": "实际退款金额（分）"
            }
        """
        # 生成 msg_id
        msg_id = self._generate_msg_id()

        # 当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 构建 biz_content
        biz_content = {
            "mer_id": self.mer_id,
            "out_trade_no": out_trade_no,
            "outtrx_serial_no": out_refund_no,
            "mer_prtcl_no": self.mer_prtcl_no,
        }

        if order_id:
            biz_content["order_id"] = order_id

        # 构建请求参数
        params = {
            "app_id": self.app_id,
            "msg_id": msg_id,
            "format": "json",
            "charset": "UTF-8",
            "sign_type": "RSA2",
            "timestamp": timestamp,
            "biz_content": json.dumps(biz_content, ensure_ascii=False),
        }

        # 签名
        sign_str = self._build_sign_str(params, "/api/cardbusiness/aggregatepay/b2c/online/refundqry/V1")
        sign = self._sign(sign_str)
        params["sign"] = sign

        logger.info(f"工行退款查询请求 - 退款流水号:{out_refund_no}, msg_id:{msg_id}")

        # 发送请求
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.API_QUERY_REFUND,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"工行退款查询响应 - 退款流水号:{out_refund_no}, pay_status:{result.get('pay_status', 'N/A')}")

        return result
```

- [ ] **Step 4: 验证语法**

```bash
cd backend
python -c "from backend.src.services.icbc_qrcode_client import IcbcQrCodeClient; print('Import OK')"
```

预期：Import OK

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/icbc_qrcode_client.py
git commit -m "feat: 工行客户端添加退款和查询方法"
```

---

## Task 4: 退款服务

**Files:**
- Create: `backend/src/services/refund_service.py`

- [ ] **Step 1: 创建退款服务文件**

创建 `backend/src/services/refund_service.py` 文件：

```python
# -*- coding: utf-8 -*-
"""退款服务"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from src.db_models import (
    PaymentOrderModel, PaymentRefundModel, RefundStatus, PaymentOrderStatus
)

logger = logging.getLogger(__name__)


class RefundService:
    """退款服务"""

    def __init__(self, db: Session, icbc_client):
        """
        初始化退款服务

        Args:
            db: 数据库会话
            icbc_client: 工行客户端实例
        """
        self.db = db
        self.icbc_client = icbc_client

    def _generate_refund_no(self) -> str:
        """
        生成退款流水号

        格式：REF + yyyyMMddHHmmss + 8位随机数

        Returns:
            退款流水号
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8].upper()
        return f"REF{timestamp}{random_str}"

    def _can_refund(self, payment_order: PaymentOrderModel, refund_amount: int) -> bool:
        """
        检查是否可以退款

        Args:
            payment_order: 支付订单
            refund_amount: 退款金额（分）

        Returns:
            是否可以退款
        """
        # 检查订单状态
        if payment_order.status != PaymentOrderStatus.paid:
            logger.warning(f"订单状态不允许退款: {payment_order.status}")
            return False

        # 检查退款金额
        can_refund_amount = payment_order.amount - payment_order.refunded_amount
        if refund_amount > can_refund_amount:
            logger.warning(f"退款金额超过可退金额: 退款={refund_amount}, 可退={can_refund_amount}")
            return False

        return True

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
            if return_code == "0":
                # 退款提交成功
                refund.status = RefundStatus.refund_processing
                refund.third_refund_no = icbc_response.get("intrx_serial_no")

                # 尝试获取实际退款金额
                if "real_reject_amt" in icbc_response:
                    try:
                        refund.real_refund_amount = int(icbc_response["real_reject_amt"])
                    except (ValueError, TypeError):
                        pass

                logger.info(f"退款提交成功: {refund.id}")
            else:
                # 退款提交失败
                refund.status = RefundStatus.refund_failed
                refund.failed_at = datetime.now()
                logger.warning(f"退款提交失败: {refund.id}, 错误码: {return_code}")

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

            # 保存工行响应
            refund.icbc_refund_response = icbc_response

            # 解析响应状态
            # 注意：工行查询响应可能在 response_biz_content 中
            biz_content = icbc_response.get("response_biz_content", icbc_response)
            pay_status = biz_content.get("pay_status")

            if pay_status == "0":
                # 退款成功
                refund.status = RefundStatus.refund_success
                refund.success_at = datetime.now()
                if not refund.real_refund_amount:
                    try:
                        refund.real_refund_amount = int(biz_content.get("real_reject_amt", refund.refund_amount))
                    except (ValueError, TypeError):
                        refund.real_refund_amount = refund.refund_amount
                logger.info(f"退款成功: {refund_id}")
            elif pay_status == "1":
                # 退款失败
                refund.status = RefundStatus.refund_failed
                refund.failed_at = datetime.now()
                logger.info(f"退款失败: {refund_id}")
            else:
                # 状态未知，继续处理中
                refund.status = RefundStatus.refund_processing
                logger.info(f"退款状态未知: {refund_id}")

            self.db.commit()
            self.db.refresh(refund)

            return refund

        except Exception as e:
            logger.error(f"查询退款状态失败: {e}")
            self.db.rollback()
            raise

    def get_refund_by_id(self, refund_id: str) -> Optional[PaymentRefundModel]:
        """
        根据ID获取退款订单

        Args:
            refund_id: 退款订单ID

        Returns:
            退款订单，不存在则返回 None
        """
        return self.db.query(PaymentRefundModel).filter(
            PaymentRefundModel.id == refund_id
        ).first()

    def list_refunds(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        out_trade_no: Optional[str] = None,
        out_refund_no: Optional[str] = None,
    ) -> tuple[list[PaymentRefundModel], int]:
        """
        获取退款订单列表

        Args:
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            out_trade_no: 商户订单号筛选
            out_refund_no: 退款流水号筛选

        Returns:
            (退款订单列表, 总数)
        """
        query = self.db.query(PaymentRefundModel)

        # 关联支付订单进行筛选
        if out_trade_no:
            query = query.join(PaymentOrderModel).filter(
                PaymentOrderModel.out_trade_no.like(f"%{out_trade_no}%")
            )

        if out_refund_no:
            query = query.filter(
                PaymentRefundModel.out_refund_no.like(f"%{out_refund_no}%")
            )

        if status:
            query = query.filter(PaymentRefundModel.status == status)

        # 总数
        total = query.count()

        # 分页
        refunds = query.order_by(
            PaymentRefundModel.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return refunds, total

    def get_payment_order_refunds(self, payment_order_id: str) -> list[PaymentRefundModel]:
        """
        获取支付订单的所有退款记录

        Args:
            payment_order_id: 支付订单ID

        Returns:
            退款记录列表
        """
        return self.db.query(PaymentRefundModel).filter(
            PaymentRefundModel.payment_order_id == payment_order_id
        ).order_by(PaymentRefundModel.created_at.desc()).all()
```

- [ ] **Step 2: 验证语法**

```bash
cd backend
python -c "from backend.src.services.refund_service import RefundService; print('Import OK')"
```

预期：Import OK

- [ ] **Step 3: 提交**

```bash
git add backend/src/services/refund_service.py
git commit -m "feat: 创建退款服务"
```

---

## Task 5: 管理员API路由

**Files:**
- Modify: `backend/src/interfaces/routers/admin/payment_admin.py:1-50` (导入部分)
- Modify: `backend/src/interfaces/routers/admin/payment_admin.py:247-end` (添加路由)

- [ ] **Step 1: 更新导入**

在文件顶部的导入部分，添加：

```python
from src.models import (
    UserInfo,
    PaymentOrderResponse,
    SystemConfigResponse,
    UpdateSystemConfigRequest,
    TestNotifyRequest,
    CreateRefundRequest,           # 新增
    RefundListResponse,            # 新增
    RefundDetailResponse,          # 新增
)
from src.db_models import PaymentOrderModel, SystemConfigModel, PointTransactionModel, PaymentRefundModel, RefundStatus  # 新增
```

- [ ] **Step 2: 更新 get_payment_service 函数**

找到 `get_payment_service` 函数，确保可以获取退款服务：

```python
def get_refund_service(db: Session = Depends(get_db)) -> "RefundService":
    """获取退款服务实例"""
    from src.services.refund_service import RefundService
    from src.services.icbc_qrcode_client import IcbcQRCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    icbc_client = IcbcQRCodeClient(**config)
    return RefundService(db, icbc_client)
```

- [ ] **Step 3: 添加退款列表接口**

在文件末尾添加：

```python
@router.get("/refunds")
async def list_refunds(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    out_trade_no: str = None,
    out_refund_no: str = None,
):
    """
    获取退款订单列表（管理员）

    Args:
        current_user: 当前管理员用户
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        status: 状态筛选
        out_trade_no: 商户订单号筛选
        out_refund_no: 退款流水号筛选

    Returns:
        退款订单列表响应
    """
    from src.services.refund_service import RefundService
    from src.services.icbc_qrcode_client import IcbcQRCodeClient
    from src.config.icbc_config import get_icbc_client_config

    config = get_icbc_client_config()
    icbc_client = IcbcQRCodeClient(**config)
    refund_service = RefundService(db, icbc_client)

    refunds, total = refund_service.list_refunds(
        page=page,
        page_size=page_size,
        status=status,
        out_trade_no=out_trade_no,
        out_refund_no=out_refund_no,
    )

    # 构建响应列表
    items = []
    for refund in refunds:
        # 获取关联的支付订单号
        payment_order = db.query(PaymentOrderModel).filter(
            PaymentOrderModel.id == refund.payment_order_id
        ).first()

        item = {
            "id": refund.id,
            "out_refund_no": refund.out_refund_no,
            "payment_order_id": refund.payment_order_id,
            "payment_order_out_trade_no": payment_order.out_trade_no if payment_order else None,
            "refund_amount": refund.refund_amount,
            "real_refund_amount": refund.real_refund_amount,
            "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
            "third_refund_no": refund.third_refund_no,
            "operator_id": refund.operator_id,
            "operator_name": refund.operator_name,
            "refund_reason": refund.refund_reason,
            "submitted_at": refund.submitted_at.isoformat() if refund.submitted_at else None,
            "success_at": refund.success_at.isoformat() if refund.success_at else None,
            "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
            "created_at": refund.created_at.isoformat(),
        }
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
```

- [ ] **Step 4: 添加退款详情接口**

```python
@router.get("/refunds/{refund_id}")
async def get_refund_detail(
    refund_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    获取退款订单详情（管理员）

    Args:
        refund_id: 退款订单ID
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        退款订单详情
    """
    refund = refund_service.get_refund_by_id(refund_id)
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"退款订单不存在: {refund_id}"
        )

    # 获取关联的支付订单
    payment_order = refund_service.db.query(PaymentOrderModel).filter(
        PaymentOrderModel.id == refund.payment_order_id
    ).first()

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "payment_order_id": refund.payment_order_id,
        "payment_order_out_trade_no": payment_order.out_trade_no if payment_order else None,
        "payment_order_amount": payment_order.amount if payment_order else None,
        "refund_amount": refund.refund_amount,
        "real_refund_amount": refund.real_refund_amount,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "third_refund_no": refund.third_refund_no,
        "icbc_refund_response": refund.icbc_refund_response,
        "operator_id": refund.operator_id,
        "operator_name": refund.operator_name,
        "refund_reason": refund.refund_reason,
        "submitted_at": refund.submitted_at.isoformat() if refund.submitted_at else None,
        "success_at": refund.success_at.isoformat() if refund.success_at else None,
        "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
        "created_at": refund.created_at.isoformat(),
        "updated_at": refund.updated_at.isoformat(),
    }
```

- [ ] **Step 5: 添加创建退款接口**

```python
@router.post("/refunds/create")
async def create_refund(
    request_data: CreateRefundRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    发起退款（管理员）

    Args:
        request_data: 创建退款请求
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        创建的退款订单
    """
    logger.info(f"管理员 {current_user.username} 发起退款: 订单={request_data.payment_order_id}, 金额={request_data.refund_amount}")

    refund = await refund_service.create_refund(
        payment_order_id=request_data.payment_order_id,
        refund_amount=request_data.refund_amount,
        operator_id=current_user.user_id,
        operator_name=current_user.nickname or current_user.username,
        refund_reason=request_data.refund_reason,
    )

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "payment_order_id": refund.payment_order_id,
        "refund_amount": refund.refund_amount,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "created_at": refund.created_at.isoformat(),
    }
```

- [ ] **Step 6: 添加查询退款状态接口**

```python
@router.post("/refunds/{refund_id}/query")
async def query_refund_status(
    refund_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    refund_service=Depends(get_refund_service),
):
    """
    查询退款状态（管理员）

    Args:
        refund_id: 退款订单ID
        current_user: 当前管理员用户
        refund_service: 退款服务

    Returns:
        更新后的退款订单
    """
    logger.info(f"管理员 {current_user.username} 查询退款状态: {refund_id}")

    refund = await refund_service.query_refund_status(refund_id)

    return {
        "id": refund.id,
        "out_refund_no": refund.out_refund_no,
        "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
        "real_refund_amount": refund.real_refund_amount,
        "third_refund_no": refund.third_refund_no,
        "success_at": refund.success_at.isoformat() if refund.success_at else None,
        "failed_at": refund.failed_at.isoformat() if refund.failed_at else None,
    }
```

- [ ] **Step 7: 添加支付订单退款记录接口**

```python
@router.get("/orders/{order_id}/refunds")
async def get_payment_order_refunds(
    order_id: str,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """
    获取支付订单的退款记录（管理员）

    Args:
        order_id: 支付订单ID
        current_user: 当前管理员用户
        db: 数据库会话

    Returns:
        退款记录列表
    """
    refunds = db.query(PaymentRefundModel).filter(
        PaymentRefundModel.payment_order_id == order_id
    ).order_by(PaymentRefundModel.created_at.desc()).all()

    items = []
    for refund in refunds:
        items.append({
            "id": refund.id,
            "out_refund_no": refund.out_refund_no,
            "refund_amount": refund.refund_amount,
            "real_refund_amount": refund.real_refund_amount,
            "status": refund.status.value if isinstance(refund.status, RefundStatus) else refund.status,
            "operator_name": refund.operator_name,
            "refund_reason": refund.refund_reason,
            "created_at": refund.created_at.isoformat(),
            "success_at": refund.success_at.isoformat() if refund.success_at else None,
        })

    return {"items": items}
```

- [ ] **Step 8: 更新订单列表接口返回退款统计**

找到 `list_all_orders` 函数，在构建 `PaymentOrderResponse` 前确保包含退款统计字段。

- [ ] **Step 9: 验证API**

```bash
cd backend
python -c "from backend.src.interfaces.routers.admin.payment_admin import router; print('Import OK')"
```

预期：Import OK

- [ ] **Step 10: 提交**

```bash
git add backend/src/interfaces/routers/admin/payment_admin.py
git commit -m "feat: 添加退款管理API接口"
```

---

## Task 6: 前端类型定义

**Files:**
- Modify: `frontend/src/types/index.ts:1400-end`

- [ ] **Step 1: 添加退款类型定义**

在 `types/index.ts` 文件末尾添加：

```typescript
// ==================== 退款模块 ====================

/**
 * 退款状态枚举
 */
export type RefundStatus = 'refund_created' | 'refund_processing' | 'refund_success' | 'refund_failed' | 'refund_cancelled'

/**
 * 退款状态显示文本映射
 */
export const RefundStatusText: Record<RefundStatus, string> = {
  refund_created: '已创建',
  refund_processing: '处理中',
  refund_success: '退款成功',
  refund_failed: '退款失败',
  refund_cancelled: '已取消'
}

/**
 * 退款状态标签类型映射
 */
export const RefundStatusType: Record<RefundStatus, 'success' | 'warning' | 'danger' | 'info'> = {
  refund_created: 'info',
  refund_processing: 'warning',
  refund_success: 'success',
  refund_failed: 'danger',
  refund_cancelled: 'info'
}

/**
 * 退款订单列表项
 */
export interface RefundListItem {
  id: string
  out_refund_no: string // 退款流水号
  payment_order_id: string // 支付订单ID
  payment_order_out_trade_no?: string // 商户订单号
  refund_amount: number // 退款金额（分）
  real_refund_amount?: number // 实际退款金额（分）
  status: RefundStatus // 退款状态
  third_refund_no?: string // 工行退款流水号
  operator_id: string // 操作人ID
  operator_name?: string // 操作人姓名
  refund_reason?: string // 退款原因
  submitted_at?: string // 发起时间
  success_at?: string // 成功时间
  failed_at?: string // 失败时间
  created_at: string // 创建时间
}

/**
 * 退款订单列表响应
 */
export interface RefundListResponse {
  items: RefundListItem[]
  total: number
  page: number
  page_size: number
}

/**
 * 退款订单详情
 */
export interface RefundDetail {
  id: string
  out_refund_no: string
  payment_order_id: string
  payment_order_out_trade_no?: string
  payment_order_amount?: number
  refund_amount: number
  real_refund_amount?: number
  status: RefundStatus
  third_refund_no?: string
  icbc_refund_response?: Record<string, any>
  operator_id: string
  operator_name?: string
  refund_reason?: string
  submitted_at?: string
  success_at?: string
  failed_at?: string
  created_at: string
  updated_at: string
}

/**
 * 创建退款请求
 */
export interface CreateRefundRequest {
  payment_order_id: string // 支付订单ID
  refund_amount: number // 退款金额（分）
  refund_reason?: string // 退款原因
}

/**
 * 创建退款响应
 */
export interface CreateRefundResponse {
  id: string
  out_refund_no: string
  payment_order_id: string
  refund_amount: number
  status: RefundStatus
  created_at: string
}

/**
 * 支付订单的退款记录
 */
export interface OrderRefundRecord {
  id: string
  out_refund_no: string
  refund_amount: number
  real_refund_amount?: number
  status: RefundStatus
  operator_name?: string
  refund_reason?: string
  created_at: string
  success_at?: string
}

/**
 * 订单退款记录响应
 */
export interface OrderRefundsResponse {
  items: OrderRefundRecord[]
}
```

- [ ] **Step 2: 更新 PaymentOrderResponse 接口**

找到 `PaymentOrderResponse` 接口定义，添加退款统计字段：

```typescript
export interface PaymentOrderResponse {
  // ... 现有字段 ...
  refunded_amount?: number // 已退款金额（分）
  refund_count?: number // 退款次数
}
```

- [ ] **Step 3: 验证类型**

```bash
cd frontend
npx vue-tsc --noEmit | head -20
```

预期：无类型错误

- [ ] **Step 4: 提交**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: 添加退款相关类型定义"
```

---

## Task 7: 退款管理页面

**Files:**
- Create: `frontend/src/views/admin/RefundManagement.vue`

- [ ] **Step 1: 创建退款管理页面**

创建 `frontend/src/views/admin/RefundManagement.vue` 文件：

```vue
<template>
  <div class="refund-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>退款管理</h3>
          <el-button type="primary" @click="showCreateDialog = true">
            发起退款
          </el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterStatus"
          placeholder="退款状态"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="已创建" value="refund_created" />
          <el-option label="处理中" value="refund_processing" />
          <el-option label="退款成功" value="refund_success" />
          <el-option label="退款失败" value="refund_failed" />
          <el-option label="已取消" value="refund_cancelled" />
        </el-select>

        <el-input
          v-model="filterOutTradeNo"
          placeholder="商户订单号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-input
          v-model="filterOutRefundNo"
          placeholder="退款流水号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-button type="primary" @click="loadRefunds">查询</el-button>
        <el-button @click="handleResetFilter">重置</el-button>
      </div>

      <!-- 退款表格 -->
      <el-table
        :data="refunds"
        v-loading="loading"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="out_refund_no" label="退款流水号" width="200" />
        <el-table-column prop="payment_order_out_trade_no" label="商户订单号" width="200">
          <template #default="{ row }">
            {{ row.payment_order_out_trade_no || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="refund_amount" label="退款金额（元）" width="120">
          <template #default="{ row }">
            ¥{{ (row.refund_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="real_refund_amount" label="实际退款（元）" width="120">
          <template #default="{ row }">
            {{ row.real_refund_amount ? '¥' + (row.real_refund_amount / 100).toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'refund_processing'"
              type="warning"
              link
              @click="handleQueryStatus(row)"
            >
              查询状态
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 发起退款对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="发起退款"
      width="500px"
    >
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="支付订单ID">
          <el-input
            v-model="createForm.payment_order_id"
            placeholder="请输入支付订单ID"
          />
        </el-form-item>
        <el-form-item label="退款金额（元）">
          <el-input-number
            v-model="refundAmountYuan"
            :min="0.01"
            :precision="2"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="退款原因">
          <el-input
            v-model="createForm.refund_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入退款原因（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateRefund" :loading="creating">
          确认退款
        </el-button>
      </template>
    </el-dialog>

    <!-- 退款详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="退款详情"
      width="700px"
    >
      <div v-if="selectedRefund" class="refund-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="退款ID" :span="2">
            {{ selectedRefund.id }}
          </el-descriptions-item>
          <el-descriptions-item label="退款流水号" :span="2">
            {{ selectedRefund.out_refund_no }}
          </el-descriptions-item>
          <el-descriptions-item label="商户订单号" :span="2">
            {{ selectedRefund.payment_order_out_trade_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款金额">
            ¥{{ (selectedRefund.refund_amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="实际退款金额">
            {{ selectedRefund.real_refund_amount ? '¥' + (selectedRefund.real_refund_amount / 100).toFixed(2) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedRefund.status)">
              {{ getStatusText(selectedRefund.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="工行流水号">
            {{ selectedRefund.third_refund_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作人" :span="2">
            {{ selectedRefund.operator_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款原因" :span="2">
            {{ selectedRefund.refund_reason || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发起时间">
            {{ formatDateTime(selectedRefund.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="成功时间">
            {{ formatDateTime(selectedRefund.success_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(selectedRefund.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 工行响应数据 -->
        <div v-if="selectedRefund.icbc_refund_response" class="response-section">
          <h4>工行响应数据</h4>
          <pre class="json-data">{{ JSON.stringify(selectedRefund.icbc_refund_response, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="selectedRefund?.status === 'refund_processing'"
          type="warning"
          @click="handleQueryStatusFromDetail"
        >
          查询状态
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import apiClient from '@/services/apiClient'
import type { RefundListItem, RefundDetail, RefundStatus } from '@/types'
import { RefundStatusText, RefundStatusType } from '@/types'

// 退款列表数据
const refunds = ref<RefundListItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选器
const filterStatus = ref<string | undefined>(undefined)
const filterOutTradeNo = ref<string | undefined>(undefined)
const filterOutRefundNo = ref<string | undefined>(undefined)

// 创建退款表单
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  payment_order_id: '',
  refund_amount: 0,
  refund_reason: ''
})
const refundAmountYuan = computed({
  get: () => createForm.value.refund_amount / 100,
  set: (val: number) => {
    createForm.value.refund_amount = Math.round(val * 100)
  }
})

// 详情对话框
const detailDialogVisible = ref(false)
const selectedRefund = ref<RefundDetail | null>(null)

/**
 * 获取状态标签类型
 */
function getStatusType(status: RefundStatus): string {
  return RefundStatusType[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: RefundStatus): string {
  return RefundStatusText[status] || status
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string | undefined): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 加载退款列表
 */
async function loadRefunds() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    if (filterOutTradeNo.value) {
      params.out_trade_no = filterOutTradeNo.value
    }
    if (filterOutRefundNo.value) {
      params.out_refund_no = filterOutRefundNo.value
    }

    const response = await apiClient.get('/admin/payment/refunds', { params })
    refunds.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载退款列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadRefunds()
}

/**
 * 重置筛选
 */
function handleResetFilter() {
  filterStatus.value = undefined
  filterOutTradeNo.value = undefined
  filterOutRefundNo.value = undefined
  currentPage.value = 1
  loadRefunds()
}

/**
 * 页码变化
 */
function handlePageChange() {
  loadRefunds()
}

/**
 * 每页数量变化
 */
function handleSizeChange() {
  currentPage.value = 1
  loadRefunds()
}

/**
 * 查看详情
 */
async function handleViewDetail(row: RefundListItem) {
  try {
    const response = await apiClient.get(`/admin/payment/refunds/${row.id}`)
    selectedRefund.value = response.data
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取退款详情失败')
  }
}

/**
 * 发起退款
 */
async function handleCreateRefund() {
  if (!createForm.value.payment_order_id) {
    ElMessage.warning('请输入支付订单ID')
    return
  }
  if (createForm.value.refund_amount <= 0) {
    ElMessage.warning('请输入退款金额')
    return
  }

  creating.value = true
  try {
    await apiClient.post('/admin/payment/refunds/create', {
      payment_order_id: createForm.value.payment_order_id,
      refund_amount: createForm.value.refund_amount,
      refund_reason: createForm.value.refund_reason
    })
    ElMessage.success('退款发起成功')
    showCreateDialog.value = false
    createForm.value = {
      payment_order_id: '',
      refund_amount: 0,
      refund_reason: ''
    }
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发起退款失败')
  } finally {
    creating.value = false
  }
}

/**
 * 查询退款状态
 */
async function handleQueryStatus(row: RefundListItem) {
  try {
    await apiClient.post(`/admin/payment/refunds/${row.id}/query`)
    ElMessage.success('状态查询成功')
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询退款状态失败')
  }
}

/**
 * 从详情对话框查询状态
 */
async function handleQueryStatusFromDetail() {
  if (!selectedRefund.value) return
  try {
    await apiClient.post(`/admin/payment/refunds/${selectedRefund.value.id}/query`)
    ElMessage.success('状态查询成功')
    // 刷新详情
    await handleViewDetail(selectedRefund.value as any)
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询退款状态失败')
  }
}

onMounted(() => {
  loadRefunds()
})
</script>

<style scoped>
.refund-management-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.refund-detail {
  padding: 8px 0;
}

.response-section {
  margin-top: 20px;
}

.response-section h4 {
  margin-bottom: 8px;
  color: #303133;
}

.json-data {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

- [ ] **Step 2: 验证语法**

```bash
cd frontend
npx vue-tsc --noEmit 2>&1 | grep -i refund || echo "No refund errors"
```

预期：无退款相关类型错误

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/admin/RefundManagement.vue
git commit -m "feat: 创建退款管理页面"
```

---

## Task 8: 支付订单页面增强

**Files:**
- Modify: `frontend/src/views/admin/PaymentOrdersView.vue:48-94` (表格列)
- Modify: `frontend/src/views/admin/PaymentOrdersView.vue:87-93` (操作列)
- Modify: `frontend/src/views/admin/PaymentOrdersView.vue:109-181` (详情对话框)

- [ ] **Step 1: 添加退款统计列**

在表格中，"支付时间"列后添加退款相关列：

```vue
        <el-table-column prop="refunded_amount" label="已退款金额（元）" width="120">
          <template #default="{ row }">
            ¥{{ (row.refunded_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="refund_count" label="退款次数" width="100" />
```

- [ ] **Step 2: 添加退款操作按钮**

在操作列中，添加退款相关按钮：

```vue
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'paid' && row.refunded_amount < row.amount"
              type="warning"
              link
              @click="handleCreateRefund(row)"
            >
              退款
            </el-button>
            <el-button
              v-if="row.refund_count > 0"
              type="info"
              link
              @click="handleViewRefunds(row)"
            >
              查看退款({{ row.refund_count }})
            </el-button>
          </template>
        </el-table-column>
```

- [ ] **Step 3: 添加退款记录对话框**

在详情对话框之后，添加退款记录对话框：

```vue
    <!-- 退款记录对话框 -->
    <el-dialog
      v-model="refundListDialogVisible"
      title="退款记录"
      width="800px"
    >
      <el-table
        :data="orderRefunds"
        v-loading="refundListLoading"
        style="width: 100%"
      >
        <el-table-column prop="out_refund_no" label="退款流水号" width="200" />
        <el-table-column prop="refund_amount" label="退款金额（元）" width="100">
          <template #default="{ row }">
            ¥{{ (row.refund_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getRefundStatusType(row.status)">
              {{ getRefundStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="refund_reason" label="退款原因" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="refundListDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
```

- [ ] **Step 4: 添加发起退款对话框**

添加发起退款对话框：

```vue
    <!-- 发起退款对话框 -->
    <el-dialog
      v-model="createRefundDialogVisible"
      title="发起退款"
      width="500px"
    >
      <div v-if="selectedOrderForRefund">
        <el-descriptions :column="2" border style="margin-bottom: 16px">
          <el-descriptions-item label="商户订单号" :span="2">
            {{ selectedOrderForRefund.out_trade_no }}
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">
            ¥{{ (selectedOrderForRefund.amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="已退款金额">
            ¥{{ (selectedOrderForRefund.refunded_amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="可退金额" :span="2">
            ¥{{ ((selectedOrderForRefund.amount - selectedOrderForRefund.refunded_amount) / 100).toFixed(2) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-form :model="refundForm" label-width="120px">
          <el-form-item label="退款金额（元）">
            <el-input-number
              v-model="refundAmountYuan"
              :min="0.01"
              :max="maxRefundAmountYuan"
              :precision="2"
              style="width: 200px"
            />
            <span style="margin-left: 8px; color: #909399;">
              最大可退: ¥{{ maxRefundAmountYuan.toFixed(2) }}
            </span>
          </el-form-item>
          <el-form-item label="退款原因">
            <el-input
              v-model="refundForm.refund_reason"
              type="textarea"
              :rows="3"
              placeholder="请输入退款原因（可选）"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="createRefundDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRefund" :loading="refunding">
          确认退款
        </el-button>
      </template>
    </el-dialog>
```

- [ ] **Step 5: 添加 script 逻辑**

在 script 部分，添加退款相关的变量和方法：

```typescript
// 退款相关
const refundListDialogVisible = ref(false)
const refundListLoading = ref(false)
const orderRefunds = ref<any[]>([])

const createRefundDialogVisible = ref(false)
const selectedOrderForRefund = ref<any>(null)
const refunding = ref(false)
const refundForm = ref({
  refund_amount: 0,
  refund_reason: ''
})

const refundAmountYuan = computed({
  get: () => refundForm.value.refund_amount / 100,
  set: (val: number) => {
    refundForm.value.refund_amount = Math.round(val * 100)
  }
})

const maxRefundAmountYuan = computed(() => {
  if (!selectedOrderForRefund.value) return 0
  return (selectedOrderForRefund.value.amount - selectedOrderForRefund.value.refunded_amount) / 100
})

/**
 * 获取退款状态标签类型
 */
function getRefundStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    refund_created: 'info',
    refund_processing: 'warning',
    refund_success: 'success',
    refund_failed: 'danger',
    refund_cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取退款状态文本
 */
function getRefundStatusText(status: string): string {
  const textMap: Record<string, string> = {
    refund_created: '已创建',
    refund_processing: '处理中',
    refund_success: '退款成功',
    refund_failed: '退款失败',
    refund_cancelled: '已取消'
  }
  return textMap[status] || status
}

/**
 * 发起退款
 */
function handleCreateRefund(row: any) {
  selectedOrderForRefund.value = row
  refundForm.value = {
    refund_amount: row.amount - row.refunded_amount,  // 默认全额退款剩余部分
    refund_reason: ''
  }
  createRefundDialogVisible.value = true
}

/**
 * 确认退款
 */
async function handleConfirmRefund() {
  if (!selectedOrderForRefund.value) return
  if (refundForm.value.refund_amount <= 0) {
    ElMessage.warning('请输入退款金额')
    return
  }

  refunding.value = true
  try {
    await apiClient.post('/admin/payment/refunds/create', {
      payment_order_id: selectedOrderForRefund.value.id,
      refund_amount: refundForm.value.refund_amount,
      refund_reason: refundForm.value.refund_reason
    })
    ElMessage.success('退款发起成功')
    createRefundDialogVisible.value = false
    loadOrders()  // 刷新订单列表
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发起退款失败')
  } finally {
    refunding.value = false
  }
}

/**
 * 查看退款记录
 */
async function handleViewRefunds(row: any) {
  refundListLoading.value = true
  refundListDialogVisible.value = true
  try {
    const response = await apiClient.get(`/admin/payment/orders/${row.id}/refunds`)
    orderRefunds.value = response.data.items || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取退款记录失败')
  } finally {
    refundListLoading.value = false
  }
}
```

- [ ] **Step 6: 验证语法**

```bash
cd frontend
npx vue-tsc --noEmit 2>&1 | grep -i "error" | head -10
```

预期：无错误

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/admin/PaymentOrdersView.vue
git commit -m "feat: 支付订单页面添加退款功能"
```

---

## Task 9: 路由配置

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加退款管理路由**

在管理后台路由的 children 数组中添加：

```typescript
{
  path: 'refunds',
  name: 'AdminRefunds',
  component: () => import('@/views/admin/RefundManagement.vue'),
  meta: { requiresAuth: true, requiresAdmin: true, title: '退款管理' }
}
```

- [ ] **Step 2: 验证路由**

```bash
cd frontend
npx vue-tsc --noEmit 2>&1 | grep -i "error" | head -5
```

预期：无路由相关错误

- [ ] **Step 3: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: 添加退款管理路由"
```

---

## Task 10: 管理后台菜单

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 添加退款管理菜单项**

在支付管理菜单组中添加"退款管理"菜单项。找到支付管理相关的菜单配置，添加：

```typescript
{
  index: '/admin/refunds',
  title: '退款管理',
  icon: 'Money', // 或其他合适的图标
}
```

- [ ] **Step 2: 验证菜单**

访问管理后台，确认侧边栏显示"退款管理"菜单项。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/layouts/AdminLayout.vue
git commit -m "feat: 添加退款管理菜单"
```

---

## Task 11: 单元测试

**Files:**
- Create: `backend/tests/unit/test_refund_service.py`

- [ ] **Step 1: 创建退款服务测试**

创建 `backend/tests/unit/test_refund_service.py` 文件：

```python
# -*- coding: utf-8 -*-
"""退款服务单元测试"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.src.services.refund_service import RefundService
from backend.src.db_models import RefundStatus, PaymentOrderStatus, PaymentRefundModel, PaymentOrderModel


class TestRefundService:
    """退款服务测试"""

    @pytest.fixture
    def db(self):
        """模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def icbc_client(self):
        """模拟工行客户端"""
        return Mock()

    @pytest.fixture
    def refund_service(self, db, icbc_client):
        """退款服务实例"""
        return RefundService(db, icbc_client)

    def test_generate_refund_no(self, refund_service):
        """测试退款流水号生成"""
        refund_no = refund_service._generate_refund_no()
        assert refund_no.startswith("REF")
        assert len(refund_no) == 23  # REF(3) + 时间戳(14) + 随机数(8)

    def test_can_refund_success(self, refund_service):
        """测试可以退款 - 成功场景"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000  # 100元
        payment_order.refunded_amount = 3000  # 已退30元

        result = refund_service._can_refund(payment_order, 2000)  # 再退20元
        assert result is True

    def test_can_refund_wrong_status(self, refund_service):
        """测试可以退款 - 状态错误"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.created
        payment_order.amount = 10000
        payment_order.refunded_amount = 0

        result = refund_service._can_refund(payment_order, 1000)
        assert result is False

    def test_can_refund_exceeds_amount(self, refund_service):
        """测试可以退款 - 超过可退金额"""
        payment_order = Mock()
        payment_order.status = PaymentOrderStatus.paid
        payment_order.amount = 10000
        payment_order.refunded_amount = 8000  # 已退80元

        result = refund_service._can_refund(payment_order, 3000)  # 尝试退30元
        assert result is False
```

- [ ] **Step 2: 运行测试**

```bash
cd backend
pytest tests/unit/test_refund_service.py -v
```

预期：测试通过

- [ ] **Step 3: 提交**

```bash
git add backend/tests/unit/test_refund_service.py
git commit -m "test: 添加退款服务单元测试"
```

---

## Task 12: 集成测试

**Files:**
- Create: `backend/tests/integration/test_refund_flow.py`

- [ ] **Step 1: 创建集成测试**

创建 `backend/tests/integration/test_refund_flow.py` 文件：

```python
# -*- coding: utf-8 -*-
"""退款流程集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport

from backend.src.main import app


@pytest.mark.asyncio
class TestRefundFlow:
    """退款流程集成测试"""

    async def test_create_refund_unauthorized(self):
        """测试未授权创建退款"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/payment/refunds/create", json={
                "payment_order_id": "test-id",
                "refund_amount": 100
            })
            assert response.status_code == 401

    # 注意：其他集成测试需要有效的认证token和测试数据
    # 建议在实际环境中手动测试
```

- [ ] **Step 2: 提交**

```bash
git add backend/tests/integration/test_refund_flow.py
git commit -m "test: 添加退款流程集成测试"
```

---

## 验收标准

### 功能验收

- [ ] 退款管理页面可以正常访问和显示
- [ ] 可以发起退款，退款订单创建成功
- [ ] 部分退款功能正常（如100元订单退30元）
- [ ] 多次退款功能正常（如剩余70元可以继续退）
- [ ] 退款金额超过可退金额时被正确拒绝
- [ ] 退款状态查询功能正常
- [ ] 支付订单页面显示退款统计信息
- [ ] 可以从支付订单页面发起退款
- [ ] 可以查看订单的所有退款记录

### 数据库验收

- [ ] `payment_refunds` 表创建成功，包含所有字段
- [ ] `payment_orders` 表的 `refunded_amount` 和 `refund_count` 字段添加成功
- [ ] 退款记录正确关联到支付订单

### API验收

- [ ] GET `/admin/payment/refunds` - 退款列表
- [ ] GET `/admin/payment/refunds/{id}` - 退款详情
- [ ] POST `/admin/payment/refunds/create` - 发起退款
- [ ] POST `/admin/payment/refunds/{id}/query` - 查询退款状态
- [ ] GET `/admin/payment/orders/{id}/refunds` - 订单退款记录

### 测试验收

- [ ] 单元测试通过（至少5个测试用例）
- [ ] 集成测试通过

---

## 回滚计划

如果出现问题，可以通过以下命令回滚：

```bash
# 回滚数据库迁移
alembic downgrade -1

# 回滚代码（回到实现前的commit）
git reset --hard <commit-before-implementation>
```

---

## 注意事项

1. **工行接口签名**：确保签名方法与支付接口保持一致，使用相同的 `_build_sign_str` 方法
2. **金额单位**：所有金额使用"分"作为单位，前端显示时转换为"元"
3. **状态映射**：工行 `pay_status=0` 表示退款成功，不是失败
4. **幂等性**：退款流水号必须唯一，避免重复退款
5. **事务处理**：退款创建和支付订单更新需要在同一事务中
