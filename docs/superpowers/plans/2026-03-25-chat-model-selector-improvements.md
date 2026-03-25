# 聊天界面模型选择器改进实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 改进聊天界面的模型选择器，包括移除"（默认）"标识、会话恢复时记住模型选择、下拉框滚动定位、标题生成使用会话模型并扣积分

**架构:** 前端修改 ModelSelector 组件和 sessionStore，后端修改会话 API 返回模型信息、重构 TitleGenerator 使用数据库配置

**技术栈:** Vue 3 Composition API, FastAPI, SQLAlchemy, OpenAI SDK

---

## Task 1: 移除"（默认）"标识

**文件:**
- Modify: `frontend/src/components/ModelSelector.vue:69`

- [ ] **Step 1: 修改 currentModelDisplay 计算属性**

打开 `frontend/src/components/ModelSelector.vue`，找到第 69 行：

```diff
- return model ? `${model.name}（默认）` : defaultModel.value
+ return model ? model.name : defaultModel.value
```

- [ ] **Step 2: 启动前端开发服务器验证**

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173，打开聊天界面，确认默认模型名称后没有"（默认）"标识。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/ModelSelector.vue
git commit -m "fix: 移除模型选择器中的'（默认）'标识"
```

---

## Task 2: 下拉框滚动定位

**文件:**
- Modify: `frontend/src/components/ModelSelector.vue:124-132`

- [ ] **Step 1: 添加 nextTick 导入**

在 `<script setup>` 部分的 import 语句中添加 `nextTick`：

```diff
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
+ import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
```

- [ ] **Step 2: 修改 toggleDropdown 函数**

找到 `toggleDropdown` 函数（约第 124 行），修改为：

```javascript
function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      const list = selectorRef.value?.querySelector('.model-list')
      const selected = list?.querySelector('.is-selected')
      selected?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    })
  }
}
```

- [ ] **Step 3: 启动前端验证**

打开聊天界面，点击模型选择器：
- 如果当前选择的模型在列表下方，滚动条应该自动滚动到选中项
- 选中项应该在可见区域内

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/ModelSelector.vue
git commit -m "feat: 模型选择器下拉框打开时滚动到选中项"
```

---

## Task 3: 后端返回会话模型信息

**文件:**
- Modify: `backend/src/models.py:544-551`
- Modify: `backend/src/interfaces/routers/sessions/sessions.py:64-71`

- [ ] **Step 1: 修改 SessionDetailResponse 模型**

打开 `backend/src/models.py`，找到 `SessionDetailResponse` 类（约第 544 行），添加模型字段：

```diff
class SessionDetailResponse(BaseModel):
    """会话详情响应"""
    session_id: str = Field(..., description="会话 UUID")
    tool_id: str = Field(..., description="工具唯一标识符")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")
    messages: List[Message] = Field(..., description="消息列表")
+   model_provider: Optional[str] = Field(None, description="AI服务提供商")
+   model_name: Optional[str] = Field(None, description="模型名称")
```

- [ ] **Step 2: 修改会话详情接口返回**

打开 `backend/src/interfaces/routers/sessions/sessions.py`，找到 `get_session_detail` 函数的 return 语句（约第 64 行），添加模型字段：

```diff
return SessionDetailResponse(
    session_id=session.session_id,
    tool_id=session.tool_id,
    title=session.title,
    created_at=session.created_at,
    updated_at=session.updated_at,
-   messages=message_list
+   messages=message_list,
+   model_provider=session.model_provider,
+   model_name=session.model_name
)
```

- [ ] **Step 3: 运行后端测试**

```bash
cd backend
python -m pytest tests/unit/ -v -k session
```

预期：所有测试通过

- [ ] **Step 4: 提交**

```bash
git add backend/src/models.py backend/src/interfaces/routers/sessions/sessions.py
git commit -m "feat: 会话详情接口返回模型信息"
```

---

## Task 4: 前端恢复会话模型选择

**文件:**
- Modify: `frontend/src/stores/sessionStore.ts:219-225`
- Modify: `frontend/src/services/apiClient.ts`（如需要）

- [ ] **Step 1: 验证类型定义已包含模型字段**

打开 `frontend/src/types/index.ts`，找到 `SessionDetailResponse` 接口（约第 151 行），确认已包含：

```typescript
export interface SessionDetailResponse {
  session_id: string
  tool_id: string
  title: string
  created_at: string
  updated_at: string
  messages: Message[]
  model_provider?: string  // 确认此行存在
  model_name?: string      // 确认此行存在
}
```

如果不存在，添加这两个字段。

- [ ] **Step 2: 修改 restoreSession 函数**

打开 `frontend/src/stores/sessionStore.ts`，找到 `restoreSession` 函数（约第 184 行），在设置 `messages.value` 之后（约第 219-225 行）添加模型恢复逻辑：

```diff
// 转换消息格式
messages.value = response.messages.map(msg => ({
  role: msg.role,
  content: msg.content,
  timestamp: msg.timestamp || (msg as any).created_at,
  artifacts: msg.artifacts || [],
}))

+ // 恢复模型选择
+ if (response.model_provider && response.model_name) {
+   currentModel.value = `${response.model_provider}:${response.model_name}`
+   console.log('[sessionStore] 恢复会话模型:', currentModel.value)
+ } else {
+   currentModel.value = null
+ }
```

- [ ] **Step 2: 启动前端验证**

1. 打开聊天界面，选择一个非默认模型
2. 发送一条消息
3. 刷新页面或切换到其他会话后再切换回来
4. 确认模型选择器显示之前选择的模型

- [ ] **Step 3: 提交**

```bash
git add frontend/src/stores/sessionStore.ts
git commit -m "feat: 恢复会话时恢复模型选择"
```

---

## Task 5: 重构 TitleGenerator 使用数据库配置

**文件:**
- Modify: `backend/src/services/title_generator.py`
- Modify: `backend/src/interfaces/dependencies.py`
- Modify: `backend/src/interfaces/routers/tools/chat.py`

- [ ] **Step 1: 修改 TitleGenerator 构造函数**

打开 `backend/src/services/title_generator.py`，重写整个类：

```python
"""会话标题生成服务"""
import logging
from typing import Optional, Tuple
from openai import OpenAI
from sqlalchemy.orm import Session

from src.services.model_provider_service import ModelProviderService

logger = logging.getLogger(__name__)


class TitleGenerator:
    """会话标题生成器"""

    def __init__(self, db: Session):
        """
        初始化标题生成器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.model_provider_service = ModelProviderService(db)

    def _get_ai_client(self, provider_code: str, model_name: str) -> Optional[OpenAI]:
        """
        根据供应商代码和模型名称获取 AI 客户端

        Args:
            provider_code: 供应商代码（如 deepseek, openai）
            model_name: 模型名称

        Returns:
            OpenAI 客户端，如果获取失败返回 None
        """
        try:
            # 从数据库获取供应商配置
            provider = self.model_provider_service.get_provider_by_code(provider_code)
            if not provider:
                logger.warning(f"标题生成：供应商 '{provider_code}' 不存在")
                return None

            if not provider.is_enabled:
                logger.warning(f"标题生成：供应商 '{provider_code}' 已禁用")
                return None

            # 获取解密后的 API Key
            api_key = self.model_provider_service.get_provider_api_key(provider.id)
            base_url = provider.base_url

            # 创建客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=30.0,
                max_retries=1
            )

            logger.info(f"标题生成客户端创建成功 - 服务商: {provider_code}, 模型: {model_name}")
            return client

        except Exception as e:
            logger.error(f"标题生成：获取 AI 客户端失败 - {e}")
            return None

    async def generate_title(
        self,
        user_message: str,
        ai_response: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        """
        智能生成会话标题

        Args:
            user_message: 用户消息
            ai_response: AI回复（可选）
            model_provider: 模型供应商代码（可选）
            model_name: 模型名称（可选）

        Returns:
            生成的标题（8-15个字）
        """
        user_msg = user_message.strip()

        # 如果用户消息为空，直接返回默认标题
        if not user_msg:
            return "新对话"

        # 如果没有指定模型，使用降级方案
        if not model_provider or not model_name:
            logger.warning("标题生成：未指定模型，使用降级方案")
            return self._fallback_title(user_message)

        # 获取 AI 客户端
        client = self._get_ai_client(model_provider, model_name)
        if not client:
            logger.warning("标题生成：无法获取 AI 客户端，使用降级方案")
            return self._fallback_title(user_message)

        # 策略选择：短消息需要AI回复辅助
        if len(user_msg) < 10:
            ai_preview = (ai_response[:300] if ai_response else "")
            prompt = f"""请为以下对话生成一个简洁的标题（8-15个字）。
用户消息：{user_msg}
AI回复：{ai_preview}

直接输出标题，无需标点："""
        else:
            # 长消息只用用户消息（限制500字符以控制成本）
            prompt = f"""请为以下用户提问生成一个简洁的标题（8-15个字）。
用户提问：{user_msg[:500]}

直接输出标题，无需标点："""

        try:
            logger.info(f"开始生成会话标题 - 使用模型: {model_provider}:{model_name}")

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=30,
                temperature=0.7
            )

            title = response.choices[0].message.content.strip()
            title = self._clean_title(title)

            if len(title) > 30:
                title = title[:30]

            logger.info(f"标题生成成功: {title}")
            return title if title else "新对话"

        except Exception as e:
            logger.error(f"AI生成标题失败: {e}")
            return self._fallback_title(user_message)

    def _clean_title(self, title: str) -> str:
        """清理标题，移除标点符号"""
        punctuation = '"\'。，！？、：；""''《》【】（）[]{}、，。！？；：'
        for char in punctuation:
            title = title.replace(char, '')
        return title.strip()

    def _fallback_title(self, user_message: str) -> str:
        """降级方案：使用简单截取生成标题"""
        msg = user_message.strip()
        if not msg:
            return "新对话"
        msg = msg.replace('\n', ' ').replace('\r', ' ')
        if len(msg) > 30:
            return msg[:30]
        else:
            return msg
```

- [ ] **Step 2: 修改依赖注入**

打开 `backend/src/routers/dependencies.py`，找到 `get_title_generator` 函数并修改：

```diff
- def get_title_generator() -> TitleGenerator:
-     """获取标题生成器单例"""
-     global _title_generator_instance
-     if _title_generator_instance is None:
-         _title_generator_instance = TitleGenerator()
-     return _title_generator_instance
+ def get_title_generator(db: Session = Depends(get_db)) -> TitleGenerator:
+     """获取标题生成器"""
+     return TitleGenerator(db)
```

- [ ] **Step 3: 修改 chat.py 调用标题生成**

打开 `backend/src/interfaces/routers/tools/chat.py`，找到标题生成的调用（约第 262 行），修改为传入模型参数：

```diff
# 生成标题
- title = await title_generator.generate_title(request.message, full_response)
+ title = await title_generator.generate_title(
+     user_message=request.message,
+     ai_response=full_response,
+     model_provider=model_provider,
+     model_name=model_name
+ )
```

同样修改非流式接口的标题生成调用（约第 459 行）：

```diff
# 生成标题
- title = await title_generator.generate_title(request.message, response_content)
+ title = await title_generator.generate_title(
+     user_message=request.message,
+     ai_response=response_content,
+     model_provider=model_provider,
+     model_name=model_name
+ )
```

- [ ] **Step 4: 运行后端测试**

```bash
cd backend
python -m pytest tests/unit/ -v -k title
```

预期：所有测试通过

- [ ] **Step 5: 提交**

```bash
git add backend/src/services/title_generator.py backend/src/interfaces/dependencies.py backend/src/interfaces/routers/tools/chat.py
git commit -m "refactor: 标题生成使用数据库配置的模型"
```

---

## Task 6: 标题生成扣减积分

**说明**：此任务需要在 Task 5 完成后执行。

**修改策略**：
1. 在 TitleGenerator 中添加 `generate_title_with_usage` 方法，返回 token 使用信息
2. 修改 chat.py 中的标题生成调用，使用新方法并扣减积分
3. 同时修改流式和非流式两个接口

**文件:**
- Modify: `backend/src/services/title_generator.py`
- Modify: `backend/src/interfaces/routers/tools/chat.py`

### Step 1: 添加 generate_title_with_usage 方法

打开 `backend/src/services/title_generator.py`，在 `_fallback_title` 方法之后添加新方法：

```python
async def generate_title_with_usage(
    self,
    user_message: str,
    ai_response: Optional[str] = None,
    model_provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[str, Optional[dict]]:
    """
    生成标题并返回 token 使用信息

    Returns:
        (标题, token使用信息字典) 元组
        token使用信息格式: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
    """
    user_msg = user_message.strip()
    if not user_msg:
        return ("新对话", None)

    if not model_provider or not model_name:
        logger.warning("标题生成：未指定模型，使用降级方案")
        return (self._fallback_title(user_message), None)

    client = self._get_ai_client(model_provider, model_name)
    if not client:
        logger.warning("标题生成：无法获取 AI 客户端，使用降级方案")
        return (self._fallback_title(user_message), None)

    # 构造 prompt
    if len(user_msg) < 10:
        ai_preview = (ai_response[:300] if ai_response else "")
        prompt = f"""请为以下对话生成一个简洁的标题（8-15个字）。
用户消息：{user_msg}
AI回复：{ai_preview}

直接输出标题，无需标点："""
    else:
        prompt = f"""请为以下用户提问生成一个简洁的标题（8-15个字）。
用户提问：{user_msg[:500]}

直接输出标题，无需标点："""

    try:
        logger.info(f"开始生成会话标题 - 使用模型: {model_provider}:{model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0.7
        )

        title = response.choices[0].message.content.strip()
        title = self._clean_title(title)
        if len(title) > 30:
            title = title[:30]

        # 提取 token 使用信息
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            logger.info(f"标题生成成功: {title}, tokens: {usage['total_tokens']}")
        else:
            logger.info(f"标题生成成功: {title} (无 token 信息)")

        return (title if title else "新对话", usage)

    except Exception as e:
        logger.error(f"AI生成标题失败: {e}")
        return (self._fallback_title(user_message), None)
```

### Step 2: 修改流式接口的标题生成（chat_stream）

打开 `backend/src/interfaces/routers/tools/chat.py`：

首先确认文件顶部有 `PointService` 导入（如果没有则添加）：

```python
from src.services.point_service import PointService
```

然后找到流式接口中的标题生成代码块（约第 254 行），找到这一行：

```python
title = await title_generator.generate_title(
    user_message=request.message,
    ai_response=full_response,
    model_provider=model_provider,
    model_name=model_name
)
```

替换为：

```python
# 生成标题（带 token 信息）
title, title_usage = await title_generator.generate_title_with_usage(
    user_message=request.message,
    ai_response=full_response,
    model_provider=model_provider,
    model_name=model_name
)

# 更新会话标题
session_service.update_session_title(session_id, title, user_id=current_user.user_id)
_logger.info(f"✅ 会话标题已生成并更新：{title}")

# 扣减标题生成的积分
if title_usage and title_usage.get('total_tokens', 0) > 0:
    try:
        db_title = next(get_db())
        try:
            point_service_title = PointService(db_title)
            # 计算积分
            points = point_service_title.calculate_points_from_tokens(
                provider_code=model_provider,
                model_code=model_name,
                prompt_tokens=title_usage.get('prompt_tokens', 0),
                completion_tokens=title_usage.get('completion_tokens', 0)
            )
            points = max(1, points)  # 至少扣除1积分

            # 扣减积分
            point_service_title.deduct_points(
                enterprise_id=current_user.enterprise_id,
                user_id=current_user.user_id,
                session_id=session_id,
                message_id="",  # 标题生成没有关联消息
                model_provider=model_provider,
                model_name=model_name,
                prompt_tokens=title_usage.get('prompt_tokens', 0),
                completion_tokens=title_usage.get('completion_tokens', 0),
                points=points
            )
            _logger.info(f"✅ 标题生成积分扣减完成 - 消耗:{points}")
        finally:
            db_title.close()
    except Exception as e:
        _logger.error(f"❌ 标题生成扣积分失败: {e}", exc_info=True)
```

### Step 3: 修改非流式接口的标题生成（chat_non_stream）

打开 `backend/src/interfaces/routers/tools/chat.py`，找到非流式接口 `chat_non_stream`（约第 304 行），找到标题生成代码块（约第 455 行），做与 Step 2 相同的修改。

**注意**：非流式接口中 AI 响应变量名是 `response_content` 而不是 `full_response`。

### Step 4: 运行测试

```bash
cd backend
python -m pytest tests/integration/routers/tools/test_chat.py -v
```

### Step 5: 提交

```bash
git add backend/src/services/title_generator.py backend/src/interfaces/routers/tools/chat.py
git commit -m "feat: 标题生成使用会话模型并扣减积分"
```

---

## 验收

### 前端验收
1. 打开聊天界面，确认默认模型名称后没有"（默认）"标识
2. 选择一个模型，发送消息，确认模型选择正确
3. 切换到其他会话再切换回来，确认模型选择恢复正确
4. 打开模型选择下拉框，确认滚动到选中项位置

### 后端验收
1. 发送第一条消息，确认标题生成成功
2. 检查积分记录，确认标题生成了扣积分
3. 查看会话详情 API，确认返回了 model_provider 和 model_name

### 运行完整测试
```bash
# 后端测试
cd backend && python -m pytest tests/unit/ tests/integration/ -v

# 前端测试
cd frontend && npm run test
```
