# 通用元数据驱动模型 (Data Models)

> **设计准则**: 极简宿主，全量配置。

---

## 1. 核心模型定义

### 1.1 Agent 配置文件模型 (AgentConfig)
定义一个 AI 能力的元数据。

```python
class AgentConfig(BaseModel):
    agent_id: str = Field(..., description="Agent 唯一标识符")
    name: str = Field(..., description="功能名称")
    description: Optional[str] = Field(None, description="功能描述（用于导航展示）")
    icon: Optional[str] = Field(None, description="图标标识（可选，用于导航展示）")
    system_prompt: str = Field(..., description="预设的系统提示词全文")
    welcome_message: Optional[str] = Field(
        None, 
        description="初始欢迎语提示（可选，用于引导 AI 生成欢迎语）"
    )
    capabilities: List[str] = Field(
        default_factory=list, 
        description="能力清单，如 ['preview_html', 'preview_svg', 'export_text']（后续迭代使用）"
    )
    ui_settings: dict = Field(
        default_factory=dict, 
        description="前端渲染配置，如布局方式、是否默认开启预览区"
    )
```

**ui_settings 结构示例**：
```python
ui_settings = {
    "show_preview": True,  # 是否开启侧边预览栏
    "preview_types": ["markdown", "html", "svg"]  # 支持的预览类型（可选）
}
```

**业务规则**：
- `welcome_message` 是可选的提示词，用于引导 AI 生成欢迎语
- 如果未设置 `welcome_message`，系统会使用默认提示（如"请向用户打招呼并介绍你的功能"）
- 会话创建时，系统会将 `system_prompt` 注入 AI，并触发一次对话生成欢迎语

### 1.2 成果物模型 (Artifact)
从 AI 回复的 Markdown 代码块中提取的成果物。

```python
class Artifact(BaseModel):
    type: str = Field(..., description="成果物类型，由代码块语言标识决定（如 'markdown', 'html', 'svg'）")
    content: str = Field(..., description="代码块中的原始内容")
    language: str = Field(..., description="代码块的语言标识")
    timestamp: datetime = Field(default_factory=datetime.now, description="成果物生成时间")
```

**类型映射规则**：
- `language="markdown"` → `type="markdown"`
- `language="html"` → `type="html"`
- `language="svg"` → `type="svg"`
- `language="javascript"` 或 `language="js"` → `type="javascript"`
- 其他语言 → `type="code"`（纯代码预览）

### 1.3 消息模型 (Message)
会话中的单条消息记录。

```python
class Message(BaseModel):
    role: str = Field(..., description="消息角色：'user' 或 'assistant'")
    content: str = Field(..., description="消息内容（Markdown 格式）")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="该消息中包含的成果物（从代码块中提取）"
    )
```

### 1.4 通用会话模型 (AgentSession)
支持断点续聊的核心存储模型。

```python
class AgentSession(BaseModel):
    session_id: UUID4 = Field(..., description="会话唯一标识")
    agent_id: str = Field(..., description="关联的 Agent 类型")
    messages: List[Message] = Field(default_factory=list, description="完整的消息历史")
    
    # 动态存储 Agent 产生的业务结果（从所有消息中提取的成果物快照）
    artifacts: List[Artifact] = Field(
        default_factory=list, 
        description="会话中产生的所有成果物快照"
    )
    
    created_at: datetime = Field(default_factory=datetime.now, description="会话创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="会话最后更新时间")
```

**业务规则**：
- `artifacts` 列表是会话中所有消息的成果物汇总，便于快速查询
- 每个 `Message` 对象也包含自己的 `artifacts`，便于前端按消息展示预览按钮

---

## 2. 存储结构实现

### 2.1 静态配置目录
所有 Agent 的定义以 YAML 格式存储在此目录，实现“加一行即可上线新 Agent”。

```text
configs/
└── agents/
    ├── prompt_wizard.yaml      # 提示词向导 Agent
    ├── code_generator.yaml     # 编程助手 Agent
    └── default_chat.yaml       # 通用对话 Agent
```

**配置加载规则**：
- **加载时机**：后端启动时一次性加载所有 Agent 配置（简单可靠）
- **配置文件格式**：YAML（易读易维护，支持多行字符串）
- **热更新**：MVP 阶段不支持，需要重启服务才能加载新配置
- **加载失败处理**：启动时检测，加载失败的 Agent 不显示在 `GET /agents` 列表中，记录错误日志，不影响其他 Agent 的正常使用
- **后续迭代**：可考虑支持配置热更新（如通过管理接口触发重新加载）

### 2.2 运行态数据目录 (storage/)
```text
storage/
└── sessions/
    └── {session_id}.json       # 序列化后的 AgentSession 对象
```

---

## 3. 设计备注

### 3.1 核心设计原则
1. **无状态转换逻辑**: 后端不维护 Agent 的步骤机。步骤的流转逻辑（如第一步到第二步）完全封装在 `system_prompt` 中。后端仅作为“状态解析器”和“存储器”。
2. **代码块识别**: 后端从 AI 回复的 Markdown 文本中识别代码块，提取成果物。只有代码块中的内容才被视为可预览的成果物。
3. **会话持久化**: MVP 阶段使用本地文件存储，每个会话保存为独立的 JSON 文件。前端负责会话恢复逻辑。

### 3.2 可扩展性
- 如果未来需要支持文件上传、RAG（知识库），仅需在 `AgentConfig` 的 `capabilities` 中增加对应能力，并在后端通用逻辑中统一处理。
- 成果物类型可以根据代码块语言标识动态扩展，无需修改核心模型。

### 3.3 MVP 阶段简化
- **会话恢复**：MVP 阶段前端自行实现（如使用 LocalStorage），后端不需要相关接口
- **成果物存储**：后端存储在 `AgentSession.artifacts` 中，与消息历史一起持久化（用于后端日志和调试）
- **前端会话管理**：前端自行管理会话状态，刷新后从本地存储恢复
- **后续迭代**：如需跨设备同步，需要实现 `GET /sessions/{session_id}` 接口，并可能需要更细粒度的会话管理（如会话列表、会话搜索、会话过期等）

---

**文档版本**: v2.2  
**更新说明**: 
- v1.0: 初始版本，成果物使用字典结构
- v2.0: 明确 Artifact 模型结构，补充 Message 模型，更新 AgentConfig 和 AgentSession 模型定义
- v2.1: 根据需求更新，明确 MVP 阶段前端自行实现会话恢复，后端不需要相关接口
- v2.2: 明确 Agent 配置加载规则（启动时加载、YAML 格式、不支持热更新），补充错误处理边界情况
