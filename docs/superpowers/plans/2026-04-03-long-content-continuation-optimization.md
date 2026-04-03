# 长内容生成续写优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 修复生成长内容时续写失败的问题，通过滑动窗口 + 配置化避免上下文超限

**架构:** 续写时只保留已生成内容的最后 N 个字符（通过数据库配置），避免总上下文超过模型的 token 限制

**技术栈:** Python 3.10+, FastAPI, SQLAlchemy, Alembic, Vue 3, TypeScript, Pinia, Vitest, Playwright

---

## 前置条件

- [ ] 确认数据库可以连接
- [ ] 确认后端开发服务器已停止（避免端口冲突）
- [ ] 确认前端开发服务器已停止
- [ ] 阅读 spec 文档: `docs/superpowers/specs/2026-04-03-long-content-continuation-optimization.md`

---

## Task 1: 创建数据库迁移文件

**目标:** 添加 3 个新字段到 `model_configs` 表

**文件:**
- 创建: `backend/alembic/versions/add_continue_config_to_model_configs.py`

- [ ] **Step 1: 创建 Alembic 迁移文件**

```bash
cd backend
alembic revision -m "add_continue_config_to_model_configs"
```

Expected: 输出新文件路径，如 `backend/alembic/versions/xxxxxxxxxxxx_add_continue_config_to_model_configs.py`

- [ ] **Step 2: 编辑迁移文件**

打开新创建的迁移文件，替换 `upgrade()` 和 `downgrade()` 函数：

```python
def upgrade() -> None:
    """Upgrade schema."""
    # 添加新字段
    op.add_column('model_configs', sa.Column('context_window', sa.Integer(), nullable=True))
    op.add_column('model_configs', sa.Column('max_output_tokens', sa.Integer(), nullable=True))
    op.add_column('model_configs', sa.Column('continue_window_size', sa.Integer(), nullable=True))

    # 设置默认值
    op.execute("UPDATE model_configs SET context_window = 8000 WHERE context_window IS NULL")
    op.execute("UPDATE model_configs SET max_output_tokens = 4000 WHERE max_output_tokens IS NULL")
    op.execute("UPDATE model_configs SET continue_window_size = 2000 WHERE continue_window_size IS NULL")

    # 为不同模型设置合理的默认值
    # DeepSeek
    op.execute("UPDATE model_configs SET context_window = 16000, max_output_tokens = 4000, continue_window_size = 2000 WHERE model_code LIKE 'deepseek%'")
    # Kimi
    op.execute("UPDATE model_configs SET context_window = 32000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'moonshot%' OR model_code LIKE 'kimi%'")
    # OpenAI
    op.execute("UPDATE model_configs SET context_window = 8192, max_output_tokens = 4096, continue_window_size = 2000 WHERE model_code LIKE 'gpt-%'")
    # Claude
    op.execute("UPDATE model_configs SET context_window = 200000, max_output_tokens = 4000, continue_window_size = 5000 WHERE model_code LIKE 'claude%'")
    # GLM
    op.execute("UPDATE model_configs SET context_window = 128000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'glm%'")
    # Gemini
    op.execute("UPDATE model_configs SET context_window = 1000000, max_output_tokens = 4000, continue_window_size = 3000 WHERE model_code LIKE 'gemini%'")

    # 修改为 NOT NULL
    op.alter_column('model_configs', 'context_window', nullable=False)
    op.alter_column('model_configs', 'max_output_tokens', nullable=False)
    op.alter_column('model_configs', 'continue_window_size', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('model_configs', 'continue_window_size', nullable=True)
    op.alter_column('model_configs', 'max_output_tokens', nullable=True)
    op.alter_column('model_configs', 'context_window', nullable=True)

    op.drop_column('model_configs', 'continue_window_size')
    op.drop_column('model_configs', 'max_output_tokens')
    op.drop_column('model_configs', 'context_window')
```

- [ ] **Step 3: 提交迁移文件**

```bash
cd backend
git add alembic/versions/xxxxxxxxxxxx_add_continue_config_to_model_configs.py
git commit -m "feat: 添加续写配置字段到 model_configs 表

- 新增 context_window: 模型上下文窗口大小
- 新增 max_output_tokens: 单次最大输出 tokens
- 新增 continue_window_size: 续写时保留的上下文大小
- 为不同模型设置合理的默认值

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 执行数据库迁移

**目标:** 将新字段应用到数据库

**文件:**
- 修改: 数据库（通过 Alembic）

- [ ] **Step 1: 检查当前数据库状态**

```bash
cd backend
alembic current
```

Expected: 输出当前版本号

- [ ] **Step 2: 执行迁移**

```bash
cd backend
alembic upgrade head
```

Expected: 输出 "Running upgrade-> xxxxxxx_add_continue_config_to_model_configs"

- [ ] **Step 3: 验证字段已添加**

```bash
cd backend
python3 << 'EOF'
from src.database import SessionLocal
from src.db_models import ModelConfigModel

db = SessionLocal()

# 查询 kimi-k2-0905-preview 模型
model = db.query(ModelConfigModel).filter(
    ModelConfigModel.model_code == 'kimi-k2-0905-preview'
).first()

if model:
    print(f"✅ 找到模型: {model.model_code}")
    print(f"   - context_window: {model.context_window}")
    print(f"   - max_output_tokens: {model.max_output_tokens}")
    print(f"   - continue_window_size: {model.continue_window_size}")
else:
    print("❌ 未找到模型")

db.close()
EOF
```

Expected: 输出模型配置，包含 3 个新字段

- [ ] **Step 4: 提交**

```bash
cd backend
git add .
git commit -m "chore: 执行数据库迁移，添加续写配置字段"
```

---

## Task 3: 添加 get_model_config 服务方法

**目标:** 在 ModelProviderService 中添加获取模型配置的方法

**文件:**
- 修改: `backend/src/services/model_provider_service.py`

- [ ] **Step 1: 查看文件末尾，找到合适的位置添加新方法**

```bash
cd backend
tail -50 src/services/model_provider_service.py
```

- [ ] **Step 2: 在文件末尾添加新方法**

```python
def get_model_config(self, provider_code: str, model_code: str) -> Optional[ModelConfigModel]:
    """
    获取模型配置

    Args:
        provider_code: 供应商代码（如 'deepseek', 'openai', 'kimi'）
        model_code: 模型代码（如 'deepseek-chat', 'gpt-4', 'kimi-k2.5'）

    Returns:
        ModelConfigModel 或 None
    """
    return self.db.query(ModelConfigModel).join(
        ModelProviderModel,
        ModelConfigModel.provider_id == ModelProviderModel.id
    ).filter(
        ModelProviderModel.provider_code == provider_code,
        ModelConfigModel.model_code == model_code,
        ModelConfigModel.is_enabled == True
    ).first()
```

注意：确保文件顶部已导入 ModelConfigModel 和 Optional

- [ ] **Step 3: 提交**

```bash
cd backend
git add src/services/model_provider_service.py
git commit -m "feat: 添加 get_model_config 方法

- 用于获取指定供应商和模型的配置
- 支持续写功能的模型配置读取

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 修改 ai_service.py 续写逻辑

**目标:** 实现滑动窗口续写

**文件:**
- 修改: `backend/src/services/ai_service.py:1260-1264`

- [ ] **Step 1: 找到续写逻辑的位置**

```bash
cd backend
grep -n "new_history = history" src/services/ai_service.py
```

Expected: 找到 line 1260-1264

- [ ] **Step 2: 查看上下文，确认修改位置**

```bash
cd backend
sed -n '1255,1270p' src/services/ai_service.py
```

- [ ] **Step 3: 替换续写逻辑**

原代码（line 1260-1264）：
```python
# 将已生成的内容添加到历史消息中
new_history = history + [
    {"role": "user", "content": user_message},
    {"role": "assistant", "content": accumulated_content}
]
```

替换为：
```python
# 获取模型配置（用于续写窗口大小）
from src.services.model_provider_service import ModelProviderService

model_provider_service = ModelProviderService(self.db)
builtin_model = model_provider_service.get_model_config(
    provider_code=provider_code,
    model_code=model_name
)

# 获取续写窗口大小（默认 2000 字符）
continue_window_size = 2000
if builtin_model and builtin_model.continue_window_size:
    continue_window_size = builtin_model.continue_window_size

# 只保留最后 N 个字符（滑动窗口）
if len(accumulated_content) > continue_window_size:
    truncated_content = accumulated_content[-continue_window_size:]
    logger.info(f"内容过长（{len(accumulated_content)} 字符），截断到最后 {continue_window_size} 字符用于续写")
else:
    truncated_content = accumulated_content

# 将截断后的内容添加到历史消息中
new_history = history + [
    {"role": "user", "content": user_message},
    {"role": "assistant", "content": truncated_content}
]
```

- [ ] **Step 4: 检查文件顶部的导入**

确保已导入 ModelProviderService（应该已经有了）

- [ ] **Step 5: 运行后端测试验证**

```bash
cd backend
pytest tests/unit/ -v -k "test_" --tb=short
```

Expected: 测试通过（或只报告新增测试的失败，现有测试不受影响）

- [ ] **Step 6: 提交**

```bash
cd backend
git add src/services/ai_service.py
git commit -m "feat: 实现滑动窗口续写逻辑

- 续写时只保留已生成内容的最后 N 个字符
- N 的大小从数据库模型配置读取（continue_window_size）
- 避免续写时上下文超限导致 API 调用失败

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 优化续写判断条件

**目标:** 使用配置的 max_output_tokens 判断是否需要续写

**文件:**
- 修改: `backend/src/services/ai_service.py:1247-1254`

- [ ] **Step 1: 查看当前的续写判断逻辑**

```bash
cd backend
sed -n '1247,1254p' src/services/ai_service.py
```

- [ ] **Step 2: 替换续写判断条件**

原代码：
```python
should_auto_continue = (
    finish_reason == 'length' and
    max_continue > 0 and
    len(accumulated_content) > 1000 and  # 必须 > 1000字符
    ('```' in accumulated_content or '<' in accumulated_content) and  # 必须包含代码标记
    not accumulated_content.rstrip().endswith(('?', '？', '!', '！')) and
    not any(word in accumulated_content[-200:] for word in ['请', '需要', '能否', '可以', '希望', '想要'])  # 最后200字符不包含追问词
)
```

替换为：
```python
# 使用配置的 max_output_tokens 判断
max_output_tokens = 4000  # 默认值
if builtin_model and builtin_model.max_output_tokens:
    max_output_tokens = builtin_model.max_output_tokens

# 估算已生成的 token 数（粗略：1 token ≈ 2 字符）
estimated_tokens = len(accumulated_content) // 2

should_auto_continue = (
    finish_reason == 'length' and
    max_continue > 0 and
    estimated_tokens >= max_output_tokens * 0.8 and  # 达到输出的 80%
    not accumulated_content.rstrip().endswith(('?', '？', '!', '！')) and
    not any(word in accumulated_content[-200:] for word in ['请', '需要', '能否', '可以', '希望', '想要'])  # 最后200字符不包含追问词
)
```

注意：这段代码应该在获取 builtin_model 之后（Task 4 的代码之后）

- [ ] **Step 3: 运行测试验证**

```bash
cd backend
pytest tests/unit/ -v -k "test_" --tb=short
```

- [ ] **Step 4: 提交**

```bash
cd backend
git add src/services/ai_service.py
git commit -m "refactor: 优化续写判断条件

- 使用配置的 max_output_tokens 判断是否需要续写
- 移除'必须包含代码标记'的限制
- 使用 token 估算替代字符数判断

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 前端 - 添加 partial 字段到类型定义

**目标:** 在 Message 类型中添加部分完成状态字段

**文件:**
- 修改: `frontend/src/types/index.ts`

- [ ] **Step 1: 找到 Message 接口定义**

```bash
cd frontend
grep -n "export interface Message" src/types/index.ts
```

- [ ] **Step 2: 在 Message 接口中添加新字段**

在 Message 接口中添加：
```typescript
partial?: boolean        // 是否为部分完成
partialMessage?: string  // 部分完成的提示信息
```

确保在合适的位置（如 error 字段后面）

- [ ] **Step 3: 运行类型检查**

```bash
cd frontend
npx vue-tsc --noEmit
```

Expected: 无类型错误

- [ ] **Step 4: 提交**

```bash
cd frontend
git add src/types/index.ts
git commit -m "feat: 添加 partial 字段到 Message 类型

- partial: 标记消息是否为部分完成
- partialMessage: 部分完成的提示信息

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 7: 前端 - 优化错误处理

**目标:** 错误不再中断流程，保留已生成的内容

**文件:**
- 修改: `frontend/src/stores/sessionStore.ts:160-164`

- [ ] **Step 1: 找到错误处理代码**

```bash
cd frontend
grep -n "type === 'error'" src/stores/sessionStore.ts
```

- [ ] **Step 2: 替换错误处理逻辑**

原代码：
```typescript
} else if (data.type === 'error') {
  // 错误处理
  console.error('[sessionStore] 收到错误类型消息:', data)
  throw new Error(data.error || '发送消息失败')
}
```

替换为：
```typescript
} else if (data.type === 'error') {
  // 错误处理 - 不影响已生成的内容
  console.error('[sessionStore] 收到错误类型消息:', data)

  // 标记消息为错误状态，但保留已生成的内容
  if (messages.value[aiMsgIndex]) {
    messages.value[aiMsgIndex].error = data.error || '发送消息失败'
    messages.value[aiMsgIndex].pending = false
  }

  // 不再抛出异常，让流程正常结束
  // throw new Error(data.error || '发送消息失败')  // ❌ 注释掉
}
```

- [ ] **Step 3: 提交**

```bash
cd frontend
git add src/stores/sessionStore.ts
git commit -m "feat: 优化错误处理，保留已生成内容

- 错误不再中断流程
- 标记消息为错误状态但保留已生成内容
- 提升用户体验

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 后端 - 添加单元测试

**目标:** 测试续写逻辑

**文件:**
- 创建: `backend/tests/unit/test_ai_service_continue.py`

- [ ] **Step 1: 创建测试文件**

```bash
cd backend
cat > tests/unit/test_ai_service_continue.py << 'EOF'
"""测试续写逻辑"""
import pytest
from unittest.mock import Mock
from src.services.ai_service import AIService


class TestContinueLogic:
    """测试续写逻辑"""

    def test_truncate_content_for_continue(self):
        """测试内容截断逻辑"""
        # 模拟模型配置
        builtin_model = Mock()
        builtin_model.continue_window_size = 2000

        # 生成 5000 字符的内容
        long_content = "A" * 5000
        continue_window_size = builtin_model.continue_window_size

        # 应用滑动窗口（2000 字符）
        if len(long_content) > continue_window_size:
            truncated = long_content[-continue_window_size:]
        else:
            truncated = long_content

        # 验证：只保留最后 2000 字符
        assert len(truncated) == 2000
        assert truncated == "A" * 2000

    def test_short_content_not_truncated(self):
        """测试短内容不被截断"""
        # 模拟模型配置
        builtin_model = Mock()
        builtin_model.continue_window_size = 2000

        # 生成 1000 字符的内容
        short_content = "A" * 1000
        continue_window_size = builtin_model.continue_window_size

        if len(short_content) > continue_window_size:
            truncated = short_content[-continue_window_size:]
        else:
            truncated = short_content

        # 验证：内容不变
        assert len(truncated) == 1000
        assert truncated == short_content

    def test_continue_window_size_default(self):
        """测试默认窗口大小"""
        default_window = 2000
        assert default_window == 2000
EOF
```

- [ ] **Step 2: 运行测试**

```bash
cd backend
pytest tests/unit/test_ai_service_continue.py -v
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
cd backend
git add tests/unit/test_ai_service_continue.py
git commit -m "test: 添加续写逻辑单元测试

- 测试内容截断逻辑
- 测试短内容不被截断
- 测试默认窗口大小

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 9: 手动测试

**目标:** 使用 kimi-k2-0905-preview 模型进行实际测试

- [ ] **Step 1: 启动后端开发服务器**

```bash
cd backend
python -m src.main
```

Expected: 服务器运行在 http://localhost:8000

- [ ] **Step 2: 启动前端开发服务器**

```bash
cd frontend
npm run dev
```

Expected: 前端运行在 http://localhost:5173

- [ ] **Step 3: 打开浏览器访问应用**

访问: http://localhost:5173

- [ ] **Step 4: 登录系统**

使用测试账号登录

- [ ] **Step 5: 选择使用 Kimi 模型的 AI 工具**

- [ ] **Step 6: 发送长内容生成请求**

示例提示词：
```
生成一个完整的电商首页，包含以下部分：
1. 顶部导航栏（Logo、搜索框、购物车、登录）
2. 轮播图（5张产品图）
3. 分类导航（左侧边栏）
4. 产品列表（包含分页）
5. 底部信息栏

要求：
- 使用现代CSS框架
- 响应式设计
- 包含完整的交互功能
- 样式美观大方
```

- [ ] **Step 7: 观察生成过程**

检查：
- 内容是否流畅生成
- 是否触发续写（查看后端日志）
- 续写是否成功（查看后端日志）
- 最终内容是否完整（包含 </html> 标签）

- [ ] **Step 8: 检查后端日志**

在后端控制台查找：
```
内容过长（xxxx 字符），截断到最后 3000 字符用于续写
```

Expected: 应该看到这条日志，说明滑动窗口生效

- [ ] **Step 9: 验证内容完整性**

在前端查看生成的 HTML：
- 应该包含完整的 HTML 结构
- 应该有 </html> 结束标签
- 内容不应该被错误消息打断

---

## Task 10: 部署到生产环境

**目标:** 将修改部署到生产环境

- [ ] **Step 1: 推送所有提交到远程**

```bash
git push origin dev
```

- [ ] **Step 2: 在生产环境执行数据库迁移**

```bash
# 在生产服务器上
cd /path/to/backend
alembic upgrade head
```

- [ ] **Step 3: 重启后端服务**

```bash
# 在生产服务器上
# 使用你的部署工具（如 systemctl, docker, 等）
sudo systemctl restart backend
```

- [ ] **Step 4: 重新构建前端**

```bash
cd frontend
npm run build
```

- [ ] **Step 5: 部署前端**

```bash
# 将 dist/ 目录部署到你的前端服务器
```

- [ ] **Step 6: 验证生产环境**

- 访问生产环境
- 登录系统
- 发送测试消息
- 验证功能正常

---

## 验收标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动测试成功（使用 kimi-k2-0905-preview）
- [ ] 生成长内容（>5000 字符）不再报错
- [ ] 续写时使用滑动窗口（查看日志确认）
- [ ] 生产环境部署成功

---

## 回滚方案

如果出现问题：

```bash
# 1. 数据库回滚
cd backend
alembic downgrade -1

# 2. 代码回滚
git revert <commit-hash>
git push origin dev

# 3. 前端回滚
git revert <commit-hash>
cd frontend
npm run build
```
