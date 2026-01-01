# 通用 Agent 交互协议 (API Interface)

> **设计哲学**: 插件化架构。后端提供宿主环境，业务逻辑由 Agent 配置（System Prompt）定义。

---

## 1. 基础信息
- **Base Path**: `/api/v1`
- **协议标准**: 消息驱动，支持可选的成果物 (Artifacts) 提取。

---

## 2. 核心接口清单

### 2.1 获取 Agent 列表
获取所有已配置的 Agent 列表，用于前端导航展示。

- **Endpoint**: `GET /agents`
- **Description**: 返回所有已配置的 Agent 列表。
- **Response Structure**:
```python
class AgentListItem(BaseModel):
    agent_id: str = Field(..., description="Agent 唯一标识符")
    name: str = Field(..., description="功能名称")
    description: Optional[str] = Field(None, description="功能描述")
    icon: Optional[str] = Field(None, description="图标标识（可选）")

class AgentListResponse(BaseModel):
    agents: List[AgentListItem] = Field(..., description="Agent 列表")
```

---

### 2.2 开启 Agent 会话
根据 Agent 唯一标识初始化一个交互环境，并自动触发 AI 生成欢迎语。

- **Endpoint**: `POST /agents/{agent_id}/sessions`
- **Description**: 激活特定 Agent 并创建会话。系统会自动调用一次 AI（用户不可见），将 AI 生成的欢迎语作为第一条消息返回。
- **Response Structure**:
```python
class SessionInitResponse(BaseModel):
    session_id: str = Field(..., description="会话 UUID")
    welcome_message: str = Field(..., description="AI 生成的欢迎语（第一条消息）")
    ui_config: dict = Field(..., description="UI 配置，如是否开启预览、预览类型等")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="欢迎语中可能包含的成果物（如代码块）"
    )
```

**业务规则**：
- 会话创建后，系统自动调用 AI，传入 Agent 的 `system_prompt`，生成欢迎语
- 如果欢迎语中包含代码块，后端需要解析并返回 `artifacts` 列表
- 前端收到响应后，直接展示 `welcome_message` 和 `artifacts`，无需再次调用 AI

---

### 2.3 通用对话交互
这是系统最核心的接口，负责透传消息并解析 AI 返回的结构化状态。

- **Endpoint**: `POST /sessions/{session_id}/chat`
- **Request Body**:
```python
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的消息")
```

- **Response Structure**:
```python
class ChatResponse(BaseModel):
    reply: str = Field(..., description="AI 的文本回复内容（完整 Markdown 文本）")
    artifacts: List[Artifact] = Field(
        default_factory=list, 
        description="从回复中解析出的成果物列表（代码块内容）"
    )
```

**业务规则**：
- 后端解析 `reply` 中的 Markdown 代码块，生成 `artifacts` 列表
- 前端展示 `reply` 的完整内容（支持 Markdown 渲染）
- 前端根据 `artifacts` 列表，在代码块上提供预览按钮
- 用户点击预览按钮后，前端根据 `artifact.type` 决定预览区的渲染方式

**响应方式**：
- **MVP 阶段**：一次性返回完整回复（简化实现，快速验证架构）
- **后续迭代**：可扩展支持流式响应（Server-Sent Events），提供实时打字效果

---

### 2.4 获取会话历史（会话恢复）【后续迭代】
用于前端刷新后恢复会话历史。**MVP 阶段不需要此接口**，前端自行实现会话恢复逻辑。

- **Endpoint**: `GET /sessions/{session_id}`
- **Description**: 获取指定会话的完整历史记录。
- **MVP 阶段状态**: ❌ **不需要实现**（前端自行实现会话恢复）
- **后续迭代**: 如需跨设备同步，需要实现此接口
- **Response Structure**:
```python
class Message(BaseModel):
    role: str = Field(..., description="消息角色：'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="消息时间戳")

class SessionHistoryResponse(BaseModel):
    session_id: str = Field(..., description="会话 UUID")
    agent_id: str = Field(..., description="关联的 Agent 类型")
    messages: List[Message] = Field(..., description="完整的消息历史")
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="会话中产生的所有成果物"
    )
```

**业务规则**：
- **MVP 阶段**：前端自行实现会话恢复（如使用 LocalStorage 存储 session_id 和消息历史）
- **后续迭代**：如需跨设备同步，需要实现此接口，前端通过此接口获取会话历史
- 后续迭代可能还需要更细粒度的会话管理（如会话列表、会话搜索等）

---

### 2.5 获取会话成果物 (只读)
用于预览窗口单独轮询或刷新后同步最新的可视化内容。

- **Endpoint**: `GET /sessions/{session_id}/artifacts`
- **Description**: 获取指定会话产生的所有成果物。
- **Response Structure**:
```python
class ArtifactsResponse(BaseModel):
    session_id: str = Field(..., description="会话 UUID")
    artifacts: List[Artifact] = Field(..., description="该会话产生的全部成果物")
```

**业务规则**：
- **MVP 阶段**：此接口不需要实现（前端自行管理成果物）
- **后续迭代**：如需跨设备同步，可能需要此接口用于预览窗口单独轮询

---

## 3. 成果物解析协议 (Artifacts Protocol)

### 3.1 代码块识别规则
系统从 AI 的 Markdown 回复中识别代码块，只有代码块中的内容才被视为可预览的成果物。

**识别规则**：
- 标准 Markdown 代码块格式：`` ```language\ncontent\n``` ``
- 代码块的语言标识（language）决定成果物类型：
  - `markdown` → Markdown 文本预览
  - `html` → HTML 页面预览
  - `svg` → SVG 图形预览
  - `javascript` / `js` → JavaScript 代码预览
  - 其他语言 → 纯文本代码预览

**成果物数据结构**：
```python
class Artifact(BaseModel):
    type: str = Field(..., description="成果物类型，由代码块语言标识决定")
    content: str = Field(..., description="代码块中的原始内容")
    language: str = Field(..., description="代码块的语言标识（如 'markdown', 'html', 'svg'）")
    timestamp: datetime = Field(..., description="成果物生成时间")
```

**示例**：
AI 回复：
```
好的，我已经为您生成了提示词：

```markdown
## [角色设定]
你是一位资深的产品经理...
```

您觉得这个提示词如何？
```

后端解析结果：
```python
artifacts = [
    Artifact(
        type="markdown",
        content="## [角色设定]\n你是一位资深的产品经理...",
        language="markdown",
        timestamp=datetime.now()
    )
]
```

### 3.2 成果物提取逻辑
- 后端解析 AI 回复的 Markdown 文本，提取所有代码块
- 每个代码块生成一个 `Artifact` 对象
- 如果 AI 回复中没有代码块，`artifacts` 列表为空
- 前端根据 `artifacts` 列表，在聊天窗口中为每个代码块提供预览按钮

---

## 4. 路由与 Agent 映射规则
- 系统通过 `agent_id` 自动定位到对应的系统提示词配置文件。
- 所有 Agent 共享同一套 `/chat` 处理逻辑。
- Agent 配置存储在 `configs/agents/` 目录，支持动态加载。

---

## 5. 错误处理

### 5.1 标准错误响应
所有接口在发生错误时，应返回统一的错误格式：

```python
class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误描述")
    details: Optional[dict] = Field(None, description="错误详情（可选）")
```

### 5.2 常见错误场景

**标准错误码**：
- `404 Not Found`: Agent 不存在、会话不存在
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: AI 服务暂时不可用

**具体错误处理**：

1. **AI 服务超时或不可用**
   - 状态码：`503 Service Unavailable`
   - 错误信息：`"AI 服务暂时不可用，请稍后重试"`
   - 处理方式：前端显示友好提示，提供重试按钮

2. **Agent 配置加载失败**
   - 状态码：`500 Internal Server Error`
   - 处理方式：启动时检测，加载失败的 Agent 不显示在 `GET /agents` 列表中，记录错误日志
   - 用户影响：该 Agent 不可用，但其他 Agent 正常使用

3. **代码块解析失败**
   - 状态码：`200 OK`（不中断对话）
   - 处理方式：静默处理，`artifacts` 列表为空，对话正常继续
   - 用户影响：该消息不显示预览按钮，但不影响对话流程

---

**文档版本**: v2.2  
**更新说明**: 
- v1.0: 初始版本，使用 `<artifact>` 标签协议
- v2.0: 改为 Markdown 代码块识别协议，补充 Agent 列表和会话恢复接口，明确 Agent 初始化流程
- v2.1: 根据需求更新，明确 MVP 阶段不需要会话恢复相关接口（前端自行实现），标记为后续迭代功能
- v2.2: 明确流式响应策略（MVP 一次性返回，后续迭代支持 SSE），补充错误处理边界情况（AI 服务异常、配置加载失败、代码块解析失败）
