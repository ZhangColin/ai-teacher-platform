# 模型汇率批量设置功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 创建统一的模型汇率批量设置页面，简化模型配置对话框，支持分别设置输入/输出汇率。

**架构:** 后端新增两个 API 接口（获取状态、批量更新），前端创建批量设置页面并改造现有配置对话框。

**技术栈:** FastAPI (后端), Vue 3 + TypeScript + Element Plus (前端)

---

## 文件结构

### 新建文件
- `backend/src/models.py` - 添加新的 Pydantic 模型
- `backend/src/interfaces/routers/admin/model_rates.py` - 新的汇率管理路由
- `frontend/src/views/admin/ModelRatesPage.vue` - 批量设置页面
- `frontend/src/components/admin/ModelRateCollapse.vue` - 折叠面板子组件

### 修改文件
- `backend/src/main.py` - 注册新路由
- `frontend/src/router/index.ts` - 添加新路由
- `frontend/src/services/apiClient.ts` - 添加新的 API 方法
- `frontend/src/types/index.ts` - 添加新的类型定义
- `frontend/src/views/admin/AdminModelProvidersPage.vue` - 简化模型配置对话框

---

## Task 1: 后端 - 添加 Pydantic 模型

**Files:**
- Modify: `backend/src/models.py`

- [ ] **Step 1: 添加新的 Pydantic 模型到 models.py**

在文件末尾添加以下模型定义（在 `class UserInfo` 之后）：

```python
# ==================== 模型汇率批量设置 ====================

class RateConfigInfo(BaseModel):
    """汇率配置信息"""
    id: str
    tokens_per_point_input: int | None
    tokens_per_point_output: int | None
    is_enabled: bool


class ModelRateStatusItem(BaseModel):
    """模型汇率状态项"""
    model_config_id: str
    provider_id: str
    provider_code: str
    provider_name: str
    model_code: str
    model_name: str
    is_model_enabled: bool
    rate_config: RateConfigInfo | None


class ModelRatesStatusResponse(BaseModel):
    """模型汇率状态响应"""
    models: List[ModelRateStatusItem]


class RateUpdateItem(BaseModel):
    """汇率更新项"""
    model_config_id: str
    tokens_per_point_input: int
    tokens_per_point_output: int
    is_enabled: bool = True


class BatchUpdateRateRequest(BaseModel):
    """批量更新汇率请求"""
    updates: List[RateUpdateItem]


class BatchUpdateRateResponse(BaseModel):
    """批量更新汇率响应"""
    updated: int
```

- [ ] **Step 2: 验证代码语法**

Run: `cd backend && python -c "from src.models import ModelRatesStatusResponse, BatchUpdateRateRequest; print('Import success')"`
Expected: "Import success"

- [ ] **Step 3: 提交**

```bash
git add backend/src/models.py
git commit -m "feat: 添加模型汇率批量设置的 Pydantic 模型"
```

---

## Task 2: 后端 - 扩展汇率管理路由

**Files:**
- Modify: `backend/src/interfaces/routers/admin/point_rates.py`

**说明**: 在现有的 `point_rates.py` 文件中添加新的端点，而不是创建新文件。

- [ ] **Step 1: 在现有文件中添加新的导入**

在文件开头的导入部分添加：

```python
from src.models import (
    # ... 现有导入 ...
    ModelRatesStatusResponse,
    ModelRateStatusItem,
    RateConfigInfo,
    BatchUpdateRateRequest,
    BatchUpdateRateResponse,
)
from src.db_models import ModelConfigModel, ModelProviderModel
```

- [ ] **Step 2: 在现有路由器中添加新的端点**

在文件末尾（最后一个路由函数之后）添加以下代码：

```python
@router.get("/status", response_model=ModelRatesStatusResponse)
async def get_model_rates_status(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有已启用模型的汇率配置状态"""
async def get_model_rates_status(
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """获取所有已启用模型的汇率配置状态"""
    # 查询所有已启用的供应商
    enabled_providers = db.query(ModelProviderModel).filter(
        ModelProviderModel.is_enabled == True
    ).all()

    if not enabled_providers:
        return ModelRatesStatusResponse(models=[])

    provider_ids = [p.id for p in enabled_providers]

    # 查询这些供应商下所有已启用的模型
    models = db.query(ModelConfigModel).filter(
        ModelConfigModel.provider_id.in_(provider_ids),
        ModelConfigModel.is_enabled == True
    ).all()

    if not models:
        return ModelRatesStatusResponse(models=[])

    # 获取所有模型ID
    model_ids = [m.id for m in models]

    # 查询所有汇率配置
    rate_configs = db.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id.in_(model_ids)
    ).all()

    # 创建汇率配置字典
    rate_dict = {r.model_config_id: r for r in rate_configs}

    # 构建响应
    result_items = []
    for model in models:
        # 获取供应商信息
        provider = next((p for p in enabled_providers if p.id == model.provider_id), None)
        if not provider:
            continue

        # 获取汇率配置
        rate_config = rate_dict.get(model.id)

        rate_info = None
        if rate_config:
            rate_info = RateConfigInfo(
                id=str(rate_config.id),
                tokens_per_point_input=rate_config.tokens_per_point_input,
                tokens_per_point_output=rate_config.tokens_per_point_output,
                is_enabled=rate_config.is_enabled,
            )

        item = ModelRateStatusItem(
            model_config_id=str(model.id),
            provider_id=str(provider.id),
            provider_code=provider.provider_code,
            provider_name=provider.provider_name,
            model_code=model.model_code,
            model_name=model.model_name,
            is_model_enabled=model.is_enabled,
            rate_config=rate_info,
        )
        result_items.append(item)

    return ModelRatesStatusResponse(models=result_items)


@router.post("/batch-update", response_model=BatchUpdateRateResponse)
async def batch_update_rates(
    request: BatchUpdateRateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)] = None,
    db: Session = Depends(get_db)
):
    """批量更新模型汇率配置

    事务处理：全部成功或全部回滚
    更新逻辑：已有配置则更新，无配置则创建
    """
    try:
        updated_count = 0

        for update_item in request.updates:
            # 查找现有汇率配置
            existing_rate = db.query(ModelPointRateModel).filter(
                ModelPointRateModel.model_config_id == update_item.model_config_id
            ).first()

            if existing_rate:
                # 更新现有配置
                existing_rate.tokens_per_point_input = update_item.tokens_per_point_input
                existing_rate.tokens_per_point_output = update_item.tokens_per_point_output
                existing_rate.separate_io = True  # 固定为 True
                existing_rate.is_enabled = update_item.is_enabled
            else:
                # 创建新配置
                new_rate = ModelPointRateModel(
                    model_config_id=update_item.model_config_id,
                    tokens_per_point=1000,  # 保留但不使用
                    separate_io=True,
                    tokens_per_point_input=update_item.tokens_per_point_input,
                    tokens_per_point_output=update_item.tokens_per_point_output,
                    is_enabled=update_item.is_enabled,
                )
                db.add(new_rate)

            updated_count += 1

        db.commit()
        logger.info(f"批量更新模型汇率成功 - 更新数量: {updated_count}")

        return BatchUpdateRateResponse(updated=updated_count)

    except Exception as e:
        db.rollback()
        logger.error(f"批量更新模型汇率失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: 验证代码语法**

Run: `cd backend && python -c "from src.interfaces.routers.admin.model_rates import router; print('Import success')"`
Expected: "Import success"

- [ ] **Step 3: 提交**

```bash
git add backend/src/interfaces/routers/admin/point_rates.py
git commit -m "feat: 在 point_rates.py 中添加批量设置端点"
```

---

## Task 3: 后端 - 编写集成测试

**Files:**
- Create: `backend/tests/integration/test_model_rates_api.py`

- [ ] **Step 1: 创建测试文件**

```python
# -*- coding: utf-8 -*-
"""模型汇率批量设置 API 集成测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.database import get_db
from src.services.auth_service import create_access_token
from src.db_models import UserModel, ModelProviderModel, ModelConfigModel, ModelPointRateModel


client = TestClient(app)


@pytest.fixture
def admin_db_session(db_session: Session):
    """创建测试管理员和测试数据

    注意：使用 db_session fixture 而不是 test_db
    db_session 应该在 conftest.py 中定义，提供测试用的数据库会话
    """
    # 创建测试管理员
    admin = UserModel(
        username="admin_test",
        nickname="测试管理员",
        password_hash="$2b$12$test_hash",
        is_admin=True,
        enterprise_id="test-enterprise-id"
    )
    db_session.add(admin)
    db_session.commit()

    # 创建测试供应商
    provider = ModelProviderModel(
        provider_code="test_provider",
        provider_name="测试供应商",
        base_url="https://api.test.com",
        is_enabled=True,
    )
    test_db.add(provider)
    test_db.commit()

    # 创建测试模型
    model = ModelConfigModel(
        provider_id=provider.id,
        model_code="test-model",
        model_name="测试模型",
        capabilities="chat",
        is_enabled=True,
    )
    test_db.add(model)
    test_db.commit()

    yield test_db

    # 清理
    test_db.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == model.id
    ).delete()
    test_db.query(ModelConfigModel).filter(ModelConfigModel.id == model.id).delete()
    test_db.query(ModelProviderModel).filter(ModelProviderModel.id == provider.id).delete()
    test_db.query(UserModel).filter(UserModel.user_id == admin.user_id).delete()
    test_db.commit()


def test_get_model_rates_status(admin_db_session):
    """测试获取模型汇率状态"""
    # 获取管理员 token
    admin = admin_db_session.query(UserModel).filter(UserModel.username == "admin_test").first()
    token = create_access_token(admin.user_id)

    response = client.get(
        "/api/v1/admin/point-rates/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0

    # 验证第一个模型的数据结构
    model = data["models"][0]
    assert "model_config_id" in model
    assert "provider_code" in model
    assert "model_code" in model
    assert "rate_config" in model


def test_batch_update_rates_create(admin_db):
    """测试批量创建汇率配置"""
    admin = admin_db_session.query(UserModel).filter(UserModel.username == "admin_test").first()
    token = create_access_token(admin.user_id)

    # 获取模型ID
    model = admin_db_session.query(ModelConfigModel).filter(ModelConfigModel.model_code == "test-model").first()

    response = client.post(
        "/api/v1/admin/point-rates/batch-update",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "updates": [
                {
                    "model_config_id": str(model.id),
                    "tokens_per_point_input": 2000,
                    "tokens_per_point_output": 1000,
                    "is_enabled": True
                }
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 1

    # 验证数据库中的记录
    rate = admin_db_session.query(ModelPointRateModel).filter(
        ModelPointRateModel.model_config_id == model.id
    ).first()
    assert rate is not None
    assert rate.tokens_per_point_input == 2000
    assert rate.tokens_per_point_output == 1000
    assert rate.separate_io == True


def test_batch_update_rates_update(admin_db):
    """测试批量更新汇率配置"""
    admin = admin_db_session.query(UserModel).filter(UserModel.username == "admin_test").first()
    token = create_access_token(admin.user_id)

    model = admin_db_session.query(ModelConfigModel).filter(ModelConfigModel.model_code == "test-model").first()

    # 先创建配置
    rate = ModelPointRateModel(
        model_config_id=model.id,
        tokens_per_point=1000,
        separate_io=True,
        tokens_per_point_input=2000,
        tokens_per_point_output=1000,
        is_enabled=True,
    )
    admin_db.add(rate)
    admin_db.commit()

    # 更新配置
    response = client.post(
        "/api/v1/admin/point-rates/batch-update",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "updates": [
                {
                    "model_config_id": str(model.id),
                    "tokens_per_point_input": 3000,
                    "tokens_per_point_output": 1500,
                    "is_enabled": False
                }
            ]
        }
    )

    assert response.status_code == 200

    # 验证更新
    admin_db.refresh(rate)
    assert rate.tokens_per_point_input == 3000
    assert rate.tokens_per_point_output == 1500
    assert rate.is_enabled == False
```

- [ ] **Step 2: 运行测试验证**

Run: `cd backend && pytest tests/integration/test_model_rates_api.py -v`
Expected: PASS (3 passed)

- [ ] **Step 3: 提交**

```bash
git add backend/tests/integration/test_model_rates_api.py
git commit -m "test: 添加模型汇率批量设置 API 集成测试"
```

---

## Task 5: 前端 - 添加类型定义

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 添加新的类型定义**

在 `ModelPointRateItem` 接口之后添加：

```typescript
// ==================== 模型汇率批量设置 ====================

export interface RateConfigInfo {
  id: string
  tokens_per_point_input: number | null
  tokens_per_point_output: number | null
  is_enabled: boolean
}

export interface ModelRateStatusItem {
  model_config_id: string
  provider_id: string
  provider_code: string
  provider_name: string
  model_code: string
  model_name: string
  is_model_enabled: boolean
  rate_config: RateConfigInfo | null
}

export interface ModelRateFormItem {
  model_config_id: string
  model_name: string
  model_code: string
  provider_id: string
  provider_code: string
  provider_name: string
  tokens_per_point_input?: number
  tokens_per_point_output?: number
  is_enabled: boolean
  has_existing_config: boolean
  rate_id?: string
  _modified: boolean
  _original?: Partial<ModelRateFormItem>
}

export interface GroupedRates {
  [provider_id: string]: {
    provider_name: string
    provider_code: string
    models: ModelRateFormItem[]
  }
}

export interface BatchRateUpdateItem {
  model_config_id: string
  tokens_per_point_input: number
  tokens_per_point_output: number
  is_enabled: boolean
}

export interface BatchUpdateRateRequest {
  updates: BatchRateUpdateItem[]
}

export interface BatchUpdateRateResponse {
  updated: number
}
```

- [ ] **Step 2: 验证类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: 提交**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: 添加模型汇率批量设置类型定义"
```

---

## Task 6: 前端 - 添加 API 方法

**Files:**
- Modify: `frontend/src/services/apiClient.ts`

- [ ] **Step 1: 添加新的 API 方法**

在 ApiService 类中添加以下方法（在现有的汇率相关方法之后）：

```typescript
  /**
   * 获取所有模型的汇率配置状态
   */
  static async getModelRatesStatus(): Promise<ModelRateStatusItem[]> {
    const response = await apiClient.get<{ models: ModelRateStatusItem[] }>('/admin/point-rates/status')
    return response.models
  }

  /**
   * 批量更新模型汇率配置
   */
  static async batchUpdateModelRates(request: BatchUpdateRateRequest): Promise<BatchUpdateRateResponse> {
    const response = await apiClient.post<BatchUpdateRateResponse>('/admin/point-rates/batch-update', request)
    return response
  }
```

- [ ] **Step 2: 验证类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: 提交**

```bash
git add frontend/src/services/apiClient.ts
git commit -m "feat: 添加模型汇率批量设置 API 方法"
```

---

## Task 7: 前端 - 创建折叠面板子组件

**Files:**
- Create: `frontend/src/components/admin/ModelRateCollapse.vue`

- [ ] **Step 1: 创建折叠面板组件**

```vue
<template>
  <div class="model-rate-collapse">
    <el-collapse v-model="activeProviderIds" @change="handleCollapseChange">
      <el-collapse-item
        v-for="(group, providerId) in groupedRates"
        :key="providerId"
        :name="providerId"
      >
        <template #title>
          <div class="provider-header">
            <span class="provider-name">{{ group.provider_name }} ({{ group.models.length }} 个模型)</span>
            <span class="provider-code">{{ group.provider_code }}</span>
          </div>
        </template>

        <el-table :data="group.models" size="small" class="rate-table">
          <el-table-column prop="model_name" label="模型名称" width="180" />
          <el-table-column prop="model_code" label="代码" width="150" />

          <el-table-column label="输入汇率" width="160">
            <template #default="{ row }">
              <el-input-number
                v-model="row.tokens_per_point_input"
                :min="1"
                :disabled="!row.is_enabled"
                size="small"
                @change="handleRateChange(row)"
              />
              <span class="unit">tokens/积分</span>
            </template>
          </el-table-column>

          <el-table-column label="输出汇率" width="160">
            <template #default="{ row }">
              <el-input-number
                v-model="row.tokens_per_point_output"
                :min="1"
                :disabled="!row.is_enabled"
                size="small"
                @change="handleRateChange(row)"
              />
              <span class="unit">tokens/积分</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_enabled" @change="handleRateChange(row)" />
            </template>
          </el-table-column>

          <el-table-column label="配置状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.has_existing_config" type="success" size="small">已配置</el-tag>
              <el-tag v-else type="info" size="small">未配置</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { GroupedRates, ModelRateFormItem } from '@/types'

interface Props {
  groupedRates: GroupedRates
  modelValue: ModelRateFormItem[]
}

interface Emits {
  (e: 'update:modelValue', value: ModelRateFormItem[]): void
  (e: 'change', item: ModelRateFormItem): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeProviderIds = ref<string[]>([])

// 默认展开第一个供应商
watch(() => props.groupedRates, (newRates) => {
  const keys = Object.keys(newRates)
  if (keys.length > 0 && activeProviderIds.value.length === 0) {
    activeProviderIds.value = [keys[0]]
  }
}, { immediate: true })

const handleCollapseChange = () => {
  // 折叠面板变化时的处理
}

const handleRateChange = (row: ModelRateFormItem) => {
  // 标记为已修改
  if (!row._original) {
    row._original = {
      tokens_per_point_input: undefined,
      tokens_per_point_output: undefined,
      is_enabled: false
    }
  }

  // 检查是否真的有变化
  const hasChanged =
    row._original.tokens_per_point_input !== row.tokens_per_point_input ||
    row._original.tokens_per_point_output !== row.tokens_per_point_output ||
    row._original.is_enabled !== row.is_enabled

  row._modified = hasChanged
  emit('change', row)
}
</script>

<style scoped>
.model-rate-collapse {
  padding: 10px 0;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.provider-name {
  font-weight: 500;
}

.provider-code {
  color: #999;
  font-size: 12px;
}

.rate-table {
  margin-top: 10px;
}

.unit {
  margin-left: 5px;
  font-size: 12px;
  color: #999;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/admin/ModelRateCollapse.vue
git commit -m "feat: 创建模型汇率折叠面板组件"
```

---

## Task 8: 前端 - 创建批量设置页面

**Files:**
- Create: `frontend/src/views/admin/ModelRatesPage.vue`

- [ ] **Step 1: 创建批量设置页面**

```vue
<template>
  <div class="model-rates-page">
    <div class="page-header">
      <h1>模型汇率配置</h1>
      <div class="header-actions">
        <el-button @click="handleReset" :disabled="!hasChanges">重置</el-button>
        <el-button type="primary" @click="handleSave" :disabled="!hasChanges" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    >
      在此页面可以批量设置所有已启用模型的输入/输出汇率。只有被修改的模型会被保存。
    </el-alert>

    <el-card v-loading="loading">
      <ModelRateCollapse
        v-if="!loading && Object.keys(groupedRates).length > 0"
        :grouped-rates="groupedRates"
        @change="handleItemChange"
      />
      <el-empty v-else-if="!loading" description="暂无已启用的模型" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ApiService } from '@/services/apiClient'
import type { GroupedRates, ModelRateFormItem, BatchUpdateRateRequest } from '@/types'
import ModelRateCollapse from '@/components/admin/ModelRateCollapse.vue'

const loading = ref(false)
const saving = ref(false)
const rateItems = ref<ModelRateFormItem[]>([])
const originalItems = ref<ModelRateFormItem[]>([])

// 分组数据
const groupedRates = computed<GroupedRates>(() => {
  const groups: GroupedRates = {}

  rateItems.value.forEach(item => {
    if (!groups[item.provider_id]) {
      groups[item.provider_id] = {
        provider_name: item.provider_name,
        provider_code: item.provider_code,
        models: []
      }
    }
    groups[item.provider_id].models.push(item)
  })

  return groups
})

// 是否有变化
const hasChanges = computed(() => {
  return rateItems.value.some(item => item._modified)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const data = await ApiService.getModelRatesStatus()

    rateItems.value = data.map(item => {
      const formItem: ModelRateFormItem = {
        model_config_id: item.model_config_id,
        model_name: item.model_name,
        model_code: item.model_code,
        provider_id: item.provider_id,
        provider_code: item.provider_code,
        provider_name: item.provider_name,
        tokens_per_point_input: item.rate_config?.tokens_per_point_input ?? undefined,
        tokens_per_point_output: item.rate_config?.tokens_per_point_output ?? undefined,
        is_enabled: item.rate_config?.is_enabled ?? true,
        has_existing_config: item.rate_config !== null,
        rate_id: item.rate_config?.id,
        _modified: false,
        _original: item.rate_config ? {
          tokens_per_point_input: item.rate_config.tokens_per_point_input,
          tokens_per_point_output: item.rate_config.tokens_per_point_output,
          is_enabled: item.rate_config.is_enabled
        } : undefined
      }
      return formItem
    })

    // 保存原始数据副本
    originalItems.value = JSON.parse(JSON.stringify(rateItems.value))
  } catch (error) {
    console.error('加载模型汇率数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 处理单项变化
const handleItemChange = (item: ModelRateFormItem) => {
  // 变化标记已在组件中处理
}

// 重置
const handleReset = () => {
  rateItems.value = JSON.parse(JSON.stringify(originalItems.value))
  ElMessage.info('已重置所有修改')
}

// 保存
const handleSave = async () => {
  // 验证：启用的模型必须有汇率值
  const modifiedItems = rateItems.value.filter(item => item._modified)

  for (const item of modifiedItems) {
    if (item.is_enabled) {
      if (!item.tokens_per_point_input || !item.tokens_per_point_output) {
        ElMessage.error(`模型 ${item.model_name} 启用时必须设置输入和输出汇率`)
        return
      }
    }
  }

  saving.value = true
  try {
    const request: BatchUpdateRateRequest = {
      updates: modifiedItems.map(item => ({
        model_config_id: item.model_config_id,
        tokens_per_point_input: item.tokens_per_point_input!,
        tokens_per_point_output: item.tokens_per_point_output!,
        is_enabled: item.is_enabled
      }))
    }

    const response = await ApiService.batchUpdateModelRates(request)
    ElMessage.success(`已成功更新 ${response.updated} 个模型的汇率配置`)

    // 重新加载数据
    await loadData()
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.model-rates-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/admin/ModelRatesPage.vue
git commit -m "feat: 创建模型汇率批量设置页面"
```

---

## Task 9: 前端 - 添加路由配置

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加路由**

找到管理后台路由配置，添加新路由：

```typescript
{
  path: 'model-rates',
  name: 'AdminModelRates',
  component: () => import('@/views/admin/ModelRatesPage.vue'),
  meta: { requiresAdmin: true, title: '模型汇率配置' }
}
```

应该放在其他管理后台路由附近（如 `model-providers` 附近）。

- [ ] **Step 2: 验证类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat: 添加模型汇率批量设置页面路由"
```

---

## Task 10: 前端 - 改造模型配置对话框

**Files:**
- Modify: `frontend/src/views/admin/AdminModelProvidersPage.vue`

- [ ] **Step 1: 简化模型配置对话框**

找到模型配置对话框部分（约在第 107-237 行），将两个 tab 的对话框简化为单表单。

将整个对话框部分替换为：

```vue
    <!-- 模型配置对话框（简化为单表单） -->
    <el-dialog
      v-model="modelDialogVisible"
      title="模型配置"
      width="600px"
    >
      <el-form :model="modelForm" label-width="100px">
        <el-form-item label="模型代码">
          <el-input v-model="modelForm.model_code" disabled />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.model_name" />
        </el-form-item>
        <el-form-item label="支持能力">
          <el-checkbox-group v-model="modelForm.capabilitiesArray">
            <el-checkbox label="chat">对话</el-checkbox>
            <el-checkbox label="image">图片生成</el-checkbox>
            <el-checkbox label="audio">音频生成</el-checkbox>
            <el-checkbox label="video">视频生成</el-checkbox>
            <el-checkbox label="code">代码</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-divider content-position="left">积分汇率配置</el-divider>

        <el-form-item label="启用汇率">
          <el-switch v-model="pointRateForm.rate_enabled" />
        </el-form-item>
        <el-form-item label="输入汇率">
          <el-input-number
            v-model="pointRateForm.input_rate"
            :min="1"
            :disabled="!pointRateForm.rate_enabled"
            style="width: 200px"
          />
          <span style="margin-left: 10px">tokens / 积分</span>
        </el-form-item>
        <el-form-item label="输出汇率">
          <el-input-number
            v-model="pointRateForm.output_rate"
            :min="1"
            :disabled="!pointRateForm.rate_enabled"
            style="width: 200px"
          />
          <span style="margin-left: 10px">tokens / 积分</span>
        </el-form-item>

        <el-form-item label="启用模型">
          <el-switch v-model="modelForm.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveModel" :loading="modelSaving">保存</el-button>
      </template>
    </el-dialog>
```

- [ ] **Step 2: 修改表单数据结构**

找到 script 部分的表单定义（约在第 276-303 行），修改为：

```typescript
// 模型表单
const modelsDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const editingModel = ref<ModelConfigListItem | null>(null)
const modelSaving = ref(false)
const modelForm = ref<{
  model_code: string
  model_name: string
  capabilitiesArray: string[]
  is_enabled: boolean
}>({
  model_code: '',
  model_name: '',
  capabilitiesArray: ['chat'],
  is_enabled: true
})

// 汇率表单（简化）
const existingRate = ref<ModelPointRateItem | null>(null)
const pointRateForm = ref<{
  rate_enabled: boolean
  input_rate: number | null
  output_rate: number | null
}>({
  rate_enabled: true,
  input_rate: null,
  output_rate: null
})
```

- [ ] **Step 3: 修改 showEditModelDialog 函数**

找到 showEditModelDialog 函数（约在第 390-424 行），替换为：

```typescript
// 显示编辑模型对话框
const showEditModelDialog = (model: ModelConfigListItem) => {
  editingModel.value = model
  modelForm.value = {
    model_code: model.model_code,
    model_name: model.model_name,
    capabilitiesArray: model.capabilities,
    is_enabled: model.is_enabled
  }

  // 加载汇率配置
  const rate = getModelPointRate(model.id)
  if (rate) {
    existingRate.value = rate
    pointRateForm.value = {
      rate_enabled: rate.is_enabled,
      input_rate: rate.tokens_per_point_input || null,
      output_rate: rate.tokens_per_point_output || null
    }
  } else {
    existingRate.value = null
    pointRateForm.value = {
      rate_enabled: true,
      input_rate: null,
      output_rate: null
    }
  }

  modelDialogVisible.value = true
}
```

- [ ] **Step 4: 添加新的保存函数**

替换原有的汇率保存函数，添加统一的模型保存函数：

```typescript
// 保存模型配置（包含汇率）
const handleSaveModel = async () => {
  if (!editingModel.value) return

  // 验证汇率
  if (pointRateForm.value.rate_enabled) {
    if (!pointRateForm.value.input_rate || !pointRateForm.value.output_rate) {
      ElMessage.error('启用汇率时，必须设置输入和输出汇率')
      return
    }
  }

  modelSaving.value = true
  try {
    // 1. 更新模型基本信息
    await ApiService.updateModelConfig(editingModel.value.id, {
      model_name: modelForm.value.model_name,
      capabilities: modelForm.value.capabilitiesArray.join(','),
      is_enabled: modelForm.value.is_enabled
    })

    // 2. 处理汇率配置
    if (pointRateForm.value.rate_enabled && pointRateForm.value.input_rate && pointRateForm.value.output_rate) {
      if (existingRate.value) {
        // 更新现有汇率
        await ApiService.updateModelPointRate(existingRate.value.id, {
          separate_io: true,
          tokens_per_point_input: pointRateForm.value.input_rate,
          tokens_per_point_output: pointRateForm.value.output_rate,
          is_enabled: true
        })
      } else {
        // 创建新汇率
        const newRate = await ApiService.createModelPointRate({
          model_config_id: editingModel.value.id,
          tokens_per_point: 1000,
          separate_io: true,
          tokens_per_point_input: pointRateForm.value.input_rate,
          tokens_per_point_output: pointRateForm.value.output_rate
        })
        pointRates.value.push(newRate)
        existingRate.value = newRate
      }
    } else if (existingRate.value) {
      // 禁用汇率配置
      await ApiService.updateModelPointRate(existingRate.value.id, {
        is_enabled: false
      })
    }

    ElMessage.success('保存成功')
    modelDialogVisible.value = false

    // 刷新数据
    await loadPointRates()
    if (currentProvider.value) {
      const response = await ApiService.getProviderModels(currentProvider.value.id, true)
      models.value = response.models
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    modelSaving.value = false
  }
}
```

- [ ] **Step 5: 删除旧的汇率处理函数**

删除以下旧函数（如果存在）：
- `handleCreatePointRate`
- `handleUpdatePointRate`
- `handleDeletePointRate`
- `watch` 对 `separate_io` 的监听

- [ ] **Step 6: 验证类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/admin/AdminModelProvidersPage.vue
git commit -m "refactor: 简化模型配置对话框为单表单"
```

---

## Task 11: 前端 - 添加菜单项

**Files:**
- Modify: `frontend/src/layouts/AdminLayout.vue`

- [ ] **Step 1: 添加图标导入**

在文件开头的 import 部分添加 `Coin` 图标：

```typescript
import { Setting, User, House, Coin } from '@element-plus/icons-vue'
```

注意：保留其他已有的图标导入，只添加 `Coin`。

- [ ] **Step 2: 在菜单配置中添加菜单项**

找到菜单配置数组（约在第 63-71 行），在"模型供应商管理"菜单项之后添加：

```typescript
{
  path: '/admin/model-rates',
  title: '模型汇率配置',
  icon: Coin
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/layouts/AdminLayout.vue
git commit -m "feat: 添加模型汇率配置菜单项"
```

---

## Task 12: E2E 测试

**Files:**
- Create: `frontend/tests/e2e/model-rates.spec.ts`

- [ ] **Step 1: 创建 E2E 测试**

```typescript
import { test, expect } from '@playwright/test'

test.describe('模型汇率批量设置', () => {
  test.beforeEach(async ({ page }) => {
    // 登录为管理员
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/')
  })

  test('应该显示模型汇率配置页面', async ({ page }) => {
    await page.goto('/admin/model-rates')

    // 验证页面标题
    await expect(page.locator('h1')).toContainText('模型汇率配置')

    // 验证保存和重置按钮存在
    await expect(page.locator('button:has-text("保存")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()
  })

  test('应该按供应商分组显示模型', async ({ page }) => {
    await page.goto('/admin/model-rates')

    // 等待数据加载
    await page.waitForSelector('.el-collapse-item', { timeout: 5000 })

    // 验证折叠面板存在
    const collapseItems = page.locator('.el-collapse-item')
    await expect(collapseItems.first()).toBeVisible()

    // 验证第一个面板默认展开
    const firstItem = collapseItems.first()
    await expect(firstItem.locator('.el-collapse-item__wrap')).toHaveClass(/is-active/)
  })

  test('应该能够修改汇率并保存', async ({ page }) => {
    await page.goto('/admin/model-rates')

    // 等待数据加载
    await page.waitForSelector('.el-collapse-item', { timeout: 5000 })

    // 找到第一个输入框并修改
    const firstInput = page.locator('.el-input-number').first()
    await firstInput.click()
    await firstInput.fill('3000')

    // 验证保存按钮可用
    const saveButton = page.locator('button:has-text("保存")')
    await expect(saveButton).not.toBeDisabled()

    // 点击保存
    await saveButton.click()

    // 验证成功提示
    await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })
  })

  test('应该能够重置修改', async ({ page }) => {
    await page.goto('/admin/model-rates')

    // 等待数据加载
    await page.waitForSelector('.el-collapse-item', { timeout: 5000 })

    // 修改值
    const firstInput = page.locator('.el-input-number').first()
    const originalValue = await firstInput.inputValue()
    await firstInput.click()
    await firstInput.fill('3000')

    // 点击重置
    await page.locator('button:has-text("重置")').click()

    // 验证值恢复
    await expect(page.locator('.el-message--info')).toBeVisible()
  })
})

test.describe('模型配置对话框简化', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/')
  })

  test('应该显示单表单配置对话框', async ({ page }) => {
    await page.goto('/admin/model-providers')

    // 点击第一个供应商的模型按钮
    await page.click('text=模型')

    // 等待模型列表加载
    await page.waitForSelector('.el-dialog')

    // 点击第一个模型的配置按钮
    await page.click('text=配置')

    // 验证对话框显示
    await expect(page.locator('.el-dialog')).toBeVisible()

    // 验证没有 tab（旧版本有两个 tab）
    await expect(page.locator('.el-tabs')).not.toBeVisible()

    // 验证输入/输出汇率字段独立显示
    await expect(page.locator('text=输入汇率')).toBeVisible()
    await expect(page.locator('text=输出汇率')).toBeVisible()

    // 验证没有"统一汇率"选项
    await expect(page.locator('text=统一汇率')).not.toBeVisible()
  })
})
```

- [ ] **Step 2: 运行 E2E 测试**

Run: `cd frontend && npm run test:e2e tests/e2e/model-rates.spec.ts --project=chromium`
Expected: PASS (5 tests)

- [ ] **Step 3: 提交**

```bash
git add frontend/tests/e2e/model-rates.spec.ts
git commit -m "test: 添加模型汇率批量设置 E2E 测试"
```

---

## Task 13: 验收测试

**Files:**
- (无需修改文件)

- [ ] **Step 1: 运行后端测试**

Run: `cd backend && pytest tests/integration/test_model_rates_api.py -v`
Expected: PASS (3 passed)

- [ ] **Step 2: 运行前端类型检查**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: No type errors

- [ ] **Step 3: 运行 E2E 测试**

Run: `cd frontend && npm run test:e2e tests/e2e/model-rates.spec.ts --project=chromium`
Expected: PASS (5 tests)

- [ ] **Step 4: 手动验证**

1. 启动后端: `cd backend && python -m src.main`
2. 启动前端: `cd frontend && npm run dev`
3. 登录为管理员，访问 `/admin/model-rates`
4. 验证所有验收标准（见设计文档第 340-364 行）

- [ ] **Step 5: 最终提交**

```bash
git commit --allow-empty -m "feat: 完成模型汇率批量设置功能

- 新增获取所有模型汇率状态的 API
- 新增批量更新模型汇率的 API
- 创建模型汇率批量设置页面
- 简化模型配置对话框为单表单
- 添加 E2E 测试"
```

---

## 验收标准

### 批量设置页面
- [ ] 页面能够正确加载和显示所有已启用供应商的已启用模型
- [ ] 按供应商分组展示，折叠面板正常展开/折叠
- [ ] 默认展开第一个供应商的面板
- [ ] 修改汇率后，字段显示修改标记（如变色或图标）
- [ ] 保存时只提交被修改的项
- [ ] 保存成功后显示提示："已更新 N 个模型的汇率配置"
- [ ] 重置功能能够恢复所有修改为原始值
- [ ] 没有汇率配置的模型显示空值或占位符

### 模型配置对话框
- [ ] 打开模型配置对话框，确认只有单表单（无 tab 切换）
- [ ] 确认"统一汇率"选项已移除
- [ ] 确认输入/输出汇率字段独立显示
- [ ] 新模型保存时自动创建汇率配置
- [ ] 已有汇率配置的模型保存时更新汇率值
- [ ] 汇率配置的启用/禁用状态正常工作

### 错误处理和验证
- [ ] 输入/输出汇率必须为正整数，否则显示验证错误
- [ ] 启用汇率配置时，输入/输出汇率不能为空
- [ ] 网络错误时显示通用错误提示
- [ ] 批量保存时，任何错误都导致全部回滚
