"""SQLAlchemy ORM 数据模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, Index, Integer, Boolean, JSON
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from .database import Base
import enum


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


class PaymentOrderStatus(enum.Enum):
    """支付订单状态枚举"""
    created = "created"
    processing = "processing"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"
    timeout = "timeout"


class RefundStatus(str, enum.Enum):
    """退款状态枚举"""
    refund_created = "refund_created"      # 退款已创建
    refund_processing = "refund_processing" # 退款处理中
    refund_success = "refund_success"       # 退款成功
    refund_failed = "refund_failed"         # 退款失败
    refund_cancelled = "refund_cancelled"   # 退款取消


class EnterpriseModel(Base):
    """企业数据库模型"""
    __tablename__ = "enterprises"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment='企业名称')
    code = Column(String(50), unique=True, nullable=False, index=True, comment='企业代码')
    status = Column(Enum(EnterpriseStatus), nullable=False, default=EnterpriseStatus.active, comment='企业状态')

    # 积分余额
    balance_gratis = Column(Integer, nullable=False, default=0, comment='赠送积分余额（非负）')
    balance_paid = Column(Integer, nullable=False, default=0, comment='充值积分余额（非负）')
    debt_points = Column(Integer, nullable=False, default=0, comment='负债积分（透支金额，非负）')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    @property
    def total_points(self):
        """总积分 = 赠送积分 + 充值积分 - 负债积分"""
        return self.balance_gratis + self.balance_paid - self.debt_points

    # 关系
    users = relationship("UserModel", back_populates="enterprise")


class UserModel(Base):
    """用户数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "users"

    user_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(11), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    is_admin = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment='用户是否激活')
    # 企业关联
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True, comment='所属企业ID')
    is_enterprise_admin = Column(Boolean, nullable=False, default=False, index=True, comment='是否企业管理员')
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")
    enterprise = relationship("EnterpriseModel", back_populates="users")


class MessageRole(enum.Enum):
    """消息角色枚举"""
    user = "user"
    assistant = "assistant"


class SessionModel(Base):
    """会话数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "sessions"

    session_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, index=True)

    # 模型选择相关字段（新增）
    model_provider = Column(String(50), nullable=True, comment="AI服务提供商（deepseek/openai/kimi/glm）")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称（如deepseek-chat/gpt-4）")

    # Token统计相关字段（新增）
    total_tokens = Column(Integer, nullable=False, default=0, comment="会话总token消耗")
    total_prompt_tokens = Column(Integer, nullable=False, default=0, comment="会话总prompt token消耗")
    total_completion_tokens = Column(Integer, nullable=False, default=0, comment="会话总completion token消耗")

    # 关系
    user = relationship("UserModel", back_populates="sessions")
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")

    # 联合索引
    __table_args__ = (
        Index("idx_user_tool", "user_id", "tool_id"),
    )


class MessageModel(Base):
    """消息数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "messages"

    message_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 多模态支持字段
    media_content = Column(Text, nullable=True, comment="多模态内容JSON字符串")

    # 模型和Token相关字段（新增）
    model_provider = Column(String(50), nullable=True, comment="AI服务提供商")
    model_name = Column(String(100), nullable=True, comment="使用的模型名称")
    prompt_tokens = Column(Integer, nullable=True, comment="用户消息的token消耗")
    completion_tokens = Column(Integer, nullable=True, comment="AI回复的token消耗")
    total_tokens = Column(Integer, nullable=True, comment="本条消息的总token消耗")

    # 关系
    session = relationship("SessionModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")


class ArtifactModel(Base):
    """成果物数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "artifacts"
    
    artifact_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(CHAR(36), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # 关系
    message = relationship("MessageModel", back_populates="artifacts")


class CommonToolType(enum.Enum):
    """常用工具类型枚举"""
    built_in = "built_in"
    html = "html"


class ToolCategoryModel(Base):
    """工具分类数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "tool_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    tools = relationship("CommonToolModel", back_populates="category", cascade="all, delete-orphan")


class CommonToolModel(Base):
    """常用工具数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "common_tools"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey("tool_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    type = Column(Enum(CommonToolType), nullable=False)
    icon = Column(String(50), nullable=True)
    html_path = Column(String(255), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    category = relationship("ToolCategoryModel", back_populates="tools")
    
    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_common_tool_category_order", "category_id", "order"),
    )


class WorkCategoryModel(Base):
    """作品分类数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "work_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    works = relationship("WorkModel", back_populates="category", cascade="all, delete-orphan")


class WorkModel(Base):
    """作品数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "works"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey("work_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    icon = Column(String(50), nullable=True)
    html_path = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    category = relationship("WorkCategoryModel", back_populates="works")
    
    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_work_category_order", "category_id", "order"),
    )


class CourseCategoryModel(Base):
    """文档目录数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "course_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    parent_id = Column(String(36), ForeignKey("course_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    children = relationship("CourseCategoryModel", back_populates="parent", remote_side="CourseCategoryModel.id")
    parent = relationship("CourseCategoryModel", back_populates="children", remote_side="CourseCategoryModel.parent_id")
    documents = relationship("CourseDocumentModel", back_populates="category", cascade="all, delete-orphan")
    
    # 联合索引（按父目录和排序查询）
    __table_args__ = (
        Index("idx_course_category_parent_order", "parent_id", "order"),
    )


class CourseDocumentModel(Base):
    """文档数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "course_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    summary = Column(String(500), nullable=False)
    file_path = Column(String(255), nullable=False)
    category_id = Column(String(36), ForeignKey("course_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    category = relationship("CourseCategoryModel", back_populates="documents")

    # 联合索引（按分类和排序查询）
    __table_args__ = (
        Index("idx_course_document_category_order", "category_id", "order"),
    )


class PointTransactionModel(Base):
    """积分交易记录数据库模型"""
    __tablename__ = "point_transactions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    operator_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=True, comment='操作人')

    type = Column(Enum(PointTransactionType), nullable=False, comment='交易类型')
    source_type = Column(Enum(PointSourceType), nullable=False, comment='来源类型')

    amount = Column(Integer, nullable=False, comment='积分金额（正数）')
    balance_before = Column(Integer, nullable=False, comment='变动前总积分')
    payment_id = Column(CHAR(36), nullable=True, comment='关联的支付订单ID')
    payment_amount = Column(Integer, nullable=True, comment='充值金额（分）')
    balance_after = Column(Integer, nullable=False, comment='变动后总积分')

    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 关系
    enterprise = relationship("EnterpriseModel")


class AIConsumptionModel(Base):
    """AI消费记录数据库模型"""
    __tablename__ = "ai_consumptions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enterprise_id = Column(CHAR(36), ForeignKey("enterprises.id"), nullable=False, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False, index=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id"), nullable=False, index=True)
    message_id = Column(CHAR(36), ForeignKey("messages.message_id"), nullable=False, index=True)

    # 模型信息
    model_provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)

    # Token消耗
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    # 积分扣减
    gratis_points_used = Column(Integer, nullable=False, default=0)
    paid_points_used = Column(Integer, nullable=False, default=0)
    total_points = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 联合索引
    __table_args__ = (
        Index("idx_ai_consumption_enterprise_date", "enterprise_id", "created_at"),
        Index("idx_ai_consumption_user_date", "user_id", "created_at"),
    )


class NavigationModuleType(enum.Enum):
    """导航模块类型枚举"""
    ai_tools = "ai_tools"
    page = "page"


class AIToolType(enum.Enum):
    """AI工具类型枚举"""
    normal = "normal"
    media = "media"


class NavigationModuleModel(Base):
    """导航模块数据库模型"""
    __tablename__ = "navigation_modules"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    type = Column(Enum(NavigationModuleType), nullable=False)
    config_source = Column(String(100), nullable=True)
    page_path = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系：关联到分类和工具
    categories = relationship("AIToolCategoryModel",
                             back_populates="navigation_module",
                             cascade="all, delete-orphan",
                             foreign_keys="AIToolCategoryModel.navigation_module_id")

    tools = relationship("AIToolModel",
                        back_populates="navigation_module",
                        cascade="all, delete-orphan",
                        foreign_keys="AIToolModel.navigation_module_id")

    # 联合索引
    __table_args__ = (
        Index("idx_navigation_module_order", "order"),
    )


class AIToolCategoryModel(Base):
    """AI工具分类数据库模型"""
    __tablename__ = "ai_tool_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    navigation_module = relationship("NavigationModuleModel", back_populates="categories")
    tools = relationship("AIToolModel", back_populates="category")


class AIToolModel(Base):
    """AI工具数据库模型"""
    __tablename__ = "ai_tools"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String(50), unique=True, nullable=False, index=True)
    navigation_module_id = Column(CHAR(36),
                                  ForeignKey("navigation_modules.id", ondelete="CASCADE"),
                                  nullable=False, index=True)
    category_id = Column(CHAR(36), ForeignKey("ai_tool_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    type = Column(Enum(AIToolType), nullable=False, default=AIToolType.normal)
    content_type = Column(String(20), nullable=True)
    media_type = Column(String(20), nullable=True)
    required_capability = Column(String(50), nullable=True, comment='所需的 AI 能力（如 chat, image, audio, video, code）')
    model = Column(String(100), nullable=True)
    welcome_message = Column(Text, nullable=True)
    visible = Column(Boolean, nullable=False, default=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    navigation_module = relationship("NavigationModuleModel", back_populates="tools")
    category = relationship("AIToolCategoryModel", back_populates="tools")

    # 联合索引
    __table_args__ = (
        Index("idx_ai_tool_navigation_module_order", "navigation_module_id", "order"),
        Index("idx_ai_tool_category_order", "category_id", "order"),
    )


class TokenUsageLogModel(Base):
    """Token使用日志数据库模型（SQLAlchemy ORM）"""
    __tablename__ = "token_usage_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(CHAR(36), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False, index=True)

    # 模型信息
    model_provider = Column(String(50), nullable=False, comment="AI服务提供商")
    model_name = Column(String(100), nullable=False, comment="模型名称")

    # Token消耗
    prompt_tokens = Column(Integer, nullable=False, comment="Prompt token数")
    completion_tokens = Column(Integer, nullable=False, comment="Completion token数")
    total_tokens = Column(Integer, nullable=False, comment="总token数")

    created_at = Column(DateTime, nullable=False, default=datetime.now, index=True)

    # 联合索引
    __table_args__ = (
        Index("idx_token_user_date", "user_id", "created_at"),
        Index("idx_token_session", "session_id"),
        Index("idx_token_provider", "model_provider"),
    )


class ModelProviderModel(Base):
    """模型供应商配置数据库模型"""
    __tablename__ = "model_providers"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = Column(String(50), unique=True, nullable=False, index=True, comment='供应商代码')
    provider_name = Column(String(100), nullable=False, comment='供应商名称')
    api_key_encrypted = Column(Text, nullable=False, comment='加密后的API密钥')
    base_url = Column(String(500), nullable=True, comment='API地址')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    is_default = Column(Boolean, nullable=False, default=False, comment='是否为默认供应商')
    order = Column(Integer, nullable=False, default=0, index=True, comment='排序')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    models = relationship("ModelConfigModel", back_populates="provider", cascade="all, delete-orphan")


class ModelConfigModel(Base):
    """模型配置数据库模型"""
    __tablename__ = "model_configs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(CHAR(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_code = Column(String(50), nullable=False, comment='模型代码')
    model_name = Column(String(100), nullable=False, comment='模型名称')
    capabilities = Column(String(50), nullable=False, comment='支持的能力，逗号分隔')
    is_enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    provider = relationship("ModelProviderModel", back_populates="models")
    point_rate = relationship("ModelPointRateModel", uselist=False)

    # 联合唯一约束
    __table_args__ = (
        Index("uk_provider_model", "provider_id", "model_code", unique=True),
    )


class ModelPointRateModel(Base):
    """模型积分汇率数据库模型"""
    __tablename__ = "model_point_rates"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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


class PaymentOrderModel(Base):
    """支付订单数据库模型"""
    __tablename__ = "payment_orders"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # 订单号
    out_trade_no = Column(String(64), unique=True, nullable=False, index=True, comment='商户订单号')
    third_trade_no = Column(String(64), nullable=True, comment='工行流水号')

    # 金额
    amount = Column(Integer, nullable=False, comment='金额（分）')

    # 状态和渠道
    status = Column(Enum(PaymentOrderStatus), nullable=False, default=PaymentOrderStatus.created, index=True)
    pay_channel = Column(String(20), nullable=False, default="icbc_aggregate", comment='支付渠道')

    # 扩展字段
    business_type = Column(String(20), nullable=False, default="recharge", comment='业务类型')
    business_id = Column(String(36), nullable=True, comment='业务ID')

    # 工行返回数据
    pay_url = Column(String(512), nullable=True, comment='支付URL')
    qr_code_data = Column(String(512), nullable=True, comment='二维码数据')
    icbc_response = Column(JSON, nullable=True, comment='工行完整响应')

    # 工行业务参数
    goods_name = Column(String(40), nullable=True, comment='商品名称')
    attach = Column(String(127), nullable=True, comment='附加数据，原样返回')
    support_app_type = Column(String(10), nullable=True, comment='支持的支付方式位图')
    msg_id = Column(String(40), nullable=True, comment='消息通讯唯一编号')

    # 时间记录
    submitted_at = Column(DateTime, nullable=True, comment='发起时间')
    paid_at = Column(DateTime, nullable=True, comment='支付时间')
    expire_at = Column(DateTime, nullable=True, comment='超时时间')
    notified_at = Column(DateTime, nullable=True, comment='回调到达时间')

    # 退款统计
    refunded_amount = Column(Integer, nullable=False, default=0, comment='已退款金额（分）')
    refund_count = Column(Integer, nullable=False, default=0, comment='退款次数')

    # 回调相关
    notify_data = Column(JSON, nullable=True, comment='回调原始数据')
    notify_verify_result = Column(Boolean, nullable=True, comment='回调验签结果')

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 联合索引
    __table_args__ = (
        Index("idx_payment_user_status", "user_id", "status"),
        Index("idx_payment_created", "created_at"),
    )


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


class SystemConfigModel(Base):
    """系统配置数据库模型"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False, index=True, comment='配置键')
    value = Column(String(500), nullable=False, comment='配置值')
    description = Column(String(200), nullable=True, comment='配置描述')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

