# 模型供应商配置管理系统设计

**日期：** 2026-03-20
**作者：** Claude
**状态：** 设计中

## 1. 概述

### 1.1 目标

实现类似 Dify 的模型供应商配置管理系统，允许管理员通过后台配置 AI 模型供应商和模型，而不是依赖环境变量或 YAML 配置文件。

### 1.2 核心原则

- **预定义 + 启用**：系统内置支持的供应商和模型列表，管理员配置后才能使用
- **能力驱动**：模型声明支持的能力（chat/image/audio/video），工具根据需要的能力选择模型
- **管理员配置**：只有管理员可以配置模型供应商
- **有限支持**：模型数量有限，每个单独实现对接

## 2. 数据库设计

### 2.1 model_providers 表（模型供应商配置）

```sql
CREATE TABLE model_providers (
    id CHAR(36) PRIMARY KEY,
    provider_code VARCHAR(50) NOT NULL UNIQUE COMMENT '供应商代码（内置）',
    provider_name VARCHAR(100) NOT NULL COMMENT '供应商名称',
    api_key VARCHAR(500) NOT NULL COMMENT 'API密钥',
    base_url VARCHAR(500) COMMENT 'API地址',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW()
);
```

### 2.2 model_configs 表（模型配置）

```sql
CREATE TABLE model_configs (
    id CHAR(36) PRIMARY KEY,
    provider_id CHAR(36) NOT NULL COMMENT '关联供应商',
    model_code VARCHAR(50) NOT NULL COMMENT '模型代码（内置）',
    model_name VARCHAR(100) NOT NULL COMMENT '模型名称',
    capabilities JSON NOT NULL COMMENT '支持的能力 ["chat","image","audio","video"]',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(),
    FOREIGN KEY (provider_id) REFERENCES model_providers(id)
);
```

## 3. 内置模型定义

### 3.1 内置供应商

`backend/src/services/builtin_models.py`：

```python
BUILTIN_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
    },
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "default_base_url": "https://api.moonshot.cn/v1",
    },
    "glm": {
        "name": "智谱 AI",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
}
```

### 3.2 内置模型

```python
BUILTIN_MODELS = {
    "deepseek": {
        "deepseek-chat": {"name": "DeepSeek Chat", "capabilities": ["chat"]},
        "deepseek-coder": {"name": "DeepSeek Coder", "capabilities": ["chat"]},
    },
    "openai": {
        "gpt-4": {"name": "GPT-4", "capabilities": ["chat"]},
        "gpt-4o": {"name": "GPT-4o", "capabilities": ["chat", "image"]},
    },
    "kimi": {
        "moonshot-v1-8k": {"name": "Moonshot v1 8K", "capabilities": ["chat"]},
    },
    "glm": {
        "glm-4": {"name": "GLM-4", "capabilities": ["chat"]},
        "glm-4-voice": {"name": "GLM-4 Voice", "capabilities": ["audio"]},
        "cogview-4": {"name": "CogView-4", "capabilities": ["image"]},
        "cogvideox": {"name": "CogVideoX", "capabilities": ["video"]},
    },
}
```

## 4. API 设计

### 4.1 管理 API（`/api/v1/admin/models`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/builtin-providers` | 获取内置供应商列表 |
| GET | `/builtin-models` | 获取内置模型列表 |
| GET | `/providers` | 获取已配置的供应商列表 |
| POST | `/providers` | 创建供应商配置 |
| PUT | `/providers/{id}` | 更新供应商配置 |
| DELETE | `/providers/{id}` | 删除供应商配置 |
| GET | `/providers/{id}/models` | 获取供应商下的已配置模型 |
| POST | `/providers/{id}/models` | 为供应商添加模型配置 |
| PUT | `/models/{id}` | 更新模型配置 |
| DELETE | `/models/{id}` | 删除模型配置 |

### 4.2 公开 API（`/api/v1/models`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/available?capability=chat` | 获取指定能力的可用模型列表 |

## 5. 前端页面设计

### 5.1 新增页面

- `frontend/src/views/admin/AdminModelProvidersPage.vue` - 模型供应商配置页面

### 5.2 导航菜单

```
管理后台 > 配置管理 > 模型供应商
```

### 5.3 页面功能

1. 供应商列表展示（API Key、Base URL、启用状态、模型数量）
2. 新建/编辑供应商（选择内置供应商、填入 API Key）
3. 为供应商添加模型（选择内置模型、勾选支持的能力）
4. 模型列表管理（编辑/删除模型配置）

## 6. AI 服务改动

### 6.1 AIService 修改

`AIService._get_ai_client()` 方法从数据库读取配置：

```python
def _get_ai_client(self, model_config: Optional[str] = None):
    # 解析模型配置
    if model_config and ":" in model_config:
        provider, model_name = model_config.split(":", 1)
    else:
        provider, model_name = self._get_default_model()

    # 从数据库获取供应商配置
    provider_config = self._get_provider_config(provider)
    if not provider_config or not provider_config.is_enabled:
        return None, "mock-model"

    # 创建客户端
    client = OpenAI(
        api_key=provider_config.api_key,
        base_url=provider_config.base_url,
        timeout=120,
        max_retries=2
    )

    return client, model_name
```

### 6.2 新增服务

`backend/src/services/model_provider_service.py`：

```python
class ModelProviderService:
    """模型配置服务"""

    def get_provider_config(self, provider_code: str) -> Optional[ModelProvider]
    def get_model_config(self, model_code: str) -> Optional[ModelConfig]
    def get_available_models(self, capability: str) -> List[ModelInfo]
```

## 7. AI 工具配置改动

### 7.1 模型选择改为下拉框

原来的文本输入框改为下拉选择，从 `/api/v1/models/available` 加载可用模型。

### 7.2 工具类型与能力映射

| 工具类型 | 能力 |
|---------|------|
| text | chat |
| image | image |
| audio | audio |
| video | video |

## 8. 实施计划

1. 数据库迁移（新增表）
2. 后端服务层（ModelProviderService）
3. 后端 API 路由（管理 API + 公开 API）
4. 前端管理页面
5. 修改 AIService 从数据库读取配置
6. 修改 AI 工具配置页面的模型选择
7. 测试
