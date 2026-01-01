# 数据模型定义 (Data Models)

> **设计哲学**: 领域驱动设计（DDD），优先设计富含业务行为的领域实体，而非贫血数据对象。

---

## 1. 领域模型概览

### 1.1 限界上下文识别
- **Agent 管理上下文**: 负责 Agent 配置的加载、验证和管理
- **会话管理上下文**: 负责会话的创建、消息的透传和 AI 服务调用
- **成果物上下文**: 负责成果物的识别、解析和展示

### 1.2 核心实体关系
```mermaid
classDiagram
    class Agent {
        +str agent_id
        +str name
        +str description
        +str system_prompt
        +UIConfig ui_config
        +load_config()
        +validate_config()
    }
    
    class AgentSession {
        +str session_id
        +str agent_id
        +datetime created_at
        +create_welcome_message()
    }
    
    class Message {
        +str role
        +str content
        +datetime timestamp
        +List~Artifact~ artifacts
    }
    
    class Artifact {
        +str type
        +str content
        +str language
        +datetime timestamp
    }
    
    Agent "1" --> "*" AgentSession : 拥有
    AgentSession "1" --> "*" Message : 包含（前端维护）
    Message "1" --> "*" Artifact : 包含
```

---

## 2. 核心领域实体

### 2.1 Agent（聚合根）
Agent 是系统的核心实体，代表一个可配置的 AI 智能体。

```python
class Agent(BaseModel):
    """Agent 配置实体（聚合根）"""
    agent_id: str = Field(..., description="Agent 唯一标识符")
    name: str = Field(..., description="功能名称")
    description: Optional[str] = Field(None, description="功能描述")
    system_prompt: str = Field(..., description="系统提示词，定义 Agent 的业务逻辑")
    ui_config: UIConfig = Field(..., description="UI 配置")
    capabilities: List[str] = Field(
        default_factory=list,
        description="Agent 能力列表（如 ['export_text', 'preview_html']）"
    )
    
    @classmethod
    def load_from_config(cls, config_path: str) -> "Agent":
        """从配置文件加载 Agent"""
        pass
    
    def validate(self) -> bool:
        """验证 Agent 配置是否完整有效"""
        pass
```

**业务规则**：
- Agent 配置必须包含 `agent_id`、`name`、`system_prompt`、`ui_config`
- 如果配置加载失败，该 Agent 不应出现在系统中

---

### 2.2 AgentSession（聚合根）
AgentSession 代表一个用户与特定 Agent 的对话会话。

```python
class AgentSession(BaseModel):
    """Agent 会话实体（聚合根）"""
    session_id: str = Field(..., description="会话 UUID")
    agent_id: str = Field(..., description="关联的 Agent 标识")
    created_at: datetime = Field(default_factory=datetime.now, description="会话创建时间")
    
    def create_welcome_message(self, agent: Agent) -> Message:
        """创建欢迎消息（自动触发 AI 生成）"""
        pass
```

**业务规则**：
- 每个 Agent 拥有独立的会话空间，互不干扰
- 会话创建时自动触发欢迎语生成
- MVP 阶段：会话历史由前端维护，后端不存储

---

### 2.3 Message（实体）
Message 代表会话中的一条消息，可以是用户消息或 AI 回复。

```python
class Message(BaseModel):
    """消息实体"""
    role: Literal["user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容（Markdown 格式）")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="消息中包含的成果物列表"
    )
    
    def extract_artifacts(self) -> List[Artifact]:
        """从消息内容中提取成果物（代码块）"""
        pass
```

**业务规则**：
- MVP 阶段：消息历史由前端维护（localStorage），后端不存储
- AI 回复中的代码块会被自动解析为 Artifact
- 普通文本不触发预览，只有代码块才会被识别为成果物

---

### 2.4 Artifact（值对象）
Artifact 代表从消息中提取的可预览成果物，是一个不可变的值对象。

```python
class Artifact(BaseModel):
    """成果物值对象（不可变）"""
    type: str = Field(..., description="成果物类型（由代码块语言标识决定）")
    content: str = Field(..., description="代码块中的原始内容")
    language: str = Field(..., description="代码块的语言标识")
    timestamp: datetime = Field(default_factory=datetime.now, description="成果物生成时间")
    
    class Config:
        frozen = True  # 值对象不可变
```

**业务规则**：
- Artifact 是不可变的值对象，修改应返回新对象
- 类型由代码块的语言标识决定（markdown → markdown, html → html）
- 只有代码块格式的内容才会被识别为成果物

---

## 3. 值对象与配置

### 3.1 UIConfig（值对象）
UI 配置信息，决定前端如何展示 Agent。

```python
class UIConfig(BaseModel):
    """UI 配置值对象"""
    show_preview: bool = Field(..., description="是否开启侧边预览栏")
    preview_types: List[str] = Field(
        default_factory=list,
        description="支持的预览类型列表（如 ['markdown', 'html', 'svg']）"
    )
    
    class Config:
        frozen = True
```

---

## 4. 数据存储（MVP 阶段）

### 4.1 Agent 配置存储
- **存储位置**: `configs/agents/` 目录
- **存储格式**: YAML 配置文件
- **文件命名**: `{agent_id}.yaml`

**配置文件示例** (`configs/agents/prompt_wizard.yaml`):
```yaml
agent_id: prompt_wizard
name: AI 提示词向导
description: 通过六步引导法，帮助您打造专家级提示词
system_prompt: |
  ## 核心使命
  你是一名深谙大模型底层的"提示词"架构师...
ui_config:
  show_preview: true
  preview_types:
    - markdown
capabilities:
  - export_text
```

### 4.2 会话数据存储
- **MVP 阶段**: 后端仅维护内存中的会话标识，不持久化消息历史
- **前端职责**: 前端负责会话数据的本地存储（localStorage）和恢复
- **未来扩展**: 如需跨设备同步，后端可扩展持久化存储

---

## 5. 领域服务（可选）

### 5.1 ArtifactParser（领域服务）
负责从消息内容中解析成果物。

```python
class ArtifactParser:
    """成果物解析服务"""
    
    @staticmethod
    def parse_from_markdown(content: str) -> List[Artifact]:
        """从 Markdown 文本中提取代码块，生成成果物列表"""
        pass
    
    @staticmethod
    def extract_code_blocks(content: str) -> List[CodeBlock]:
        """提取所有代码块"""
        pass
```

---

## 6. 演进式设计说明

### 6.1 当前迭代设计
- **简单设计**: Agent 配置使用文件存储，会话消息历史由前端维护
- **清晰边界**: 明确区分 Agent、Session、Message、Artifact 的职责
- **可扩展性**: 保持代码整洁，便于未来重构

### 6.2 未来扩展方向
- **会话持久化**: 如需跨设备同步，可扩展数据库存储
- **多租户支持**: 可扩展用户体系，支持多用户隔离
- **成果物管理**: 可扩展成果物的版本管理、分类、搜索等功能

---

**文档版本**: v1.0  
**最后更新**: 2026-01-01  
**设计依据**: 
- `docs/requirements/product_spec.md`
- `docs/requirements/ai_prompt_wizard_spec.md`
- `docs/requirements/ui_interaction_guide.md`
- `docs/requirements/acceptance_scenarios.md`

