# 模型汇率批量设置功能设计

## 日期
2026-03-24

## 概述

创建统一的模型汇率批量设置功能，解决当前每个模型需要单独设置汇率的繁琐问题。

## 需求背景

当前系统在 `AdminModelProvidersPage.vue` 中设置模型汇率时，需要：
1. 点击供应商的"模型"按钮
2. 在弹出的对话框中选择具体模型
3. 切换到"积分汇率" tab
4. 创建/更新汇率配置

这个过程对每个模型都要重复一次，非常繁琐。

## 功能目标

1. 提供独立的批量设置页面，一次性配置所有模型的汇率
2. 简化现有的模型配置对话框，合并为单表单
3. 只支持分别设置输入/输出汇率，移除统一汇率选项
4. 只保存被修改过的项

## 使用场景

### 批量设置页面
适用于：
- 初次配置系统汇率
- 大规模调整汇率（如供应商价格变更）
- 快速查看和比较所有模型的汇率配置

### 单个模型配置对话框
适用于：
- 针对特定模型的精细调整
- 修改模型基本信息时顺便调整汇率
- 新增模型时的初始配置

## 设计方案

### 1. 批量设置页面

#### 路由和菜单
- 路由: `/admin/model-rates`
- 菜单位置: 管理后台 → 模型汇率配置

#### 页面布局

```
┌────────────────────────────────────────────────────────────────────┐
│ 模型汇率配置                                           [保存] [重置] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ DeepSeek (3 个模型) ─────────────────────────────────────[展开]┐│
│ │  模型名称           │ 输入汇率     │ 输出汇率     │ 状态        ││
│ │  deepseek-chat      │ [ 2000    ] │ [ 1000    ] │ [✓]         ││
│ │  deepseek-coder     │ [ 2000    ] │ [ 1000    ] │ [✓]         ││
│ │  deepseek-reasoner  │ [ 1500    ] │ [  750    ] │ [✓]         ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ ┌─ Kimi (2 个模型) ─────────────────────────────────────────[折叠]┐│
│ │  moonshot-v1-8k    │ [ 1000    ] │ [  500    ] │ [✓]         ││
│ │  moonshot-v1-32k   │ [  500    ] │ [  250    ] │ [✓]         ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

#### 数据结构

```typescript
// 批量设置页面的表单项（与现有 ModelPointRateItem 保持字段名一致）
interface ModelRateFormItem {
  model_config_id: string
  model_name: string
  model_code: string
  provider_id: string
  provider_name: string
  tokens_per_point_input: number | null   // 输入汇率，与现有类型一致
  tokens_per_point_output: number | null  // 输出汇率，与现有类型一致
  is_enabled: boolean                     // 是否启用汇率配置
  has_existing_config: boolean            // 是否已有汇率配置
  rate_id: string | null                  // 现有汇率配置的 ID（如果有）
  _modified: boolean                      // 内部标记，是否被修改
  _original?: Partial<ModelRateFormItem>  // 原始值用于对比
}

// 分组数据结构
interface GroupedRates {
  [provider_id: string]: {
    provider_name: string
    models: ModelRateFormItem[]
  }
}

// 批量更新请求项
interface BatchRateUpdateItem {
  model_config_id: string
  tokens_per_point_input: number
  tokens_per_point_output: number
  is_enabled: boolean
}
```

#### 核心功能

1. **加载数据**: 获取所有已启用供应商的已启用模型
2. **分组展示**: 按供应商分组，使用 `el-collapse` 折叠面板
3. **内联编辑**: 输入/输出汇率使用 `el-input-number` 直接编辑
4. **变更追踪**: 通过 `_modified` 标记识别被修改的项
5. **批量保存**: 只提交被修改的项到后端
6. **重置功能**: 恢复所有修改为原始值

### 2. 改造模型配置对话框

#### 简化前后对比

**简化前（两个 tab）:**
```
[基本配置] [积分汇率]
```

**简化后（单表单）:**
```
┌────────────────────────────────────────────────────────┐
│ 模型配置                                                │
├────────────────────────────────────────────────────────┤
│ 模型代码: [deepseek-chat               ]               │
│ 模型名称: [DeepSeek 聊天                  ]            │
│ 支持能力: [☑对话] [☐图片生成] [☐音频生成] [☐代码]    │
│ ────────────────────────────────────────────────────── │
│ 输入汇率: [2000        ] tokens / 积分                 │
│ 输出汇率: [1000        ] tokens / 积分                 │
│ ────────────────────────────────────────────────────── │
│ 启用汇率配置: [✓]                                       │
│ 启用模型: [✓]                                           │
├────────────────────────────────────────────────────────┤
│                                    [取消] [保存]       │
└────────────────────────────────────────────────────────┘
```

#### 表单结构

```typescript
interface ModelConfigForm {
  model_code: string
  model_name: string
  capabilities: string[]
  input_rate: number | null
  output_rate: number | null
  rate_enabled: boolean
  model_enabled: boolean
}
```

### 3. 后端 API

#### 新增获取所有模型汇率状态接口

```python
@router.get("/model-rates/status", response_model=ModelRatesStatusResponse)
async def get_model_rates_status(
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """获取所有已启用模型的汇率配置状态"""

class ModelRateStatusItem(BaseModel):
    model_config_id: str
    provider_id: str
    provider_name: str
    model_code: str
    model_name: str
    is_model_enabled: bool
    rate_config: RateConfigInfo | None

class RateConfigInfo(BaseModel):
    id: str
    tokens_per_point_input: int
    tokens_per_point_output: int
    is_enabled: bool

class ModelRatesStatusResponse(BaseModel):
    models: List[ModelRateStatusItem]
```

**查询逻辑**:
1. 查询所有 `is_enabled=True` 的供应商
2. 查询这些供应商下所有 `is_enabled=True` 的模型
3. 左连接查询每个模型的汇率配置（如果存在）
4. 返回组合数据

#### 新增批量更新接口

```python
@router.post("/model-rates/batch-update", response_model=BatchUpdateRateResponse)
async def batch_update_rates(
    request: BatchUpdateRateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """批量更新模型汇率配置

    事务处理：
    - 全部成功或全部回滚，不提供部分成功
    - 使用数据库事务确保原子性
    - 并发冲突时返回 409 错误

    更新逻辑：
    - 如果模型已有汇率配置，更新现有记录
    - 如果模型没有汇率配置，创建新记录（separate_io 固定为 True）
    """

class BatchUpdateRateRequest(BaseModel):
    updates: List[RateUpdateItem]

class RateUpdateItem(BaseModel):
    model_config_id: str
    tokens_per_point_input: int
    tokens_per_point_output: int
    is_enabled: bool = True

class BatchUpdateRateResponse(BaseModel):
    updated: int  # 成功更新的数量
```

#### 数据库模型调整

`ModelPointRateModel` 保持兼容，但使用方式变化：
- `separate_io` 字段：新创建的记录固定为 `True`
- `tokens_per_point` 字段：保留但不使用（兼容旧数据）
- `tokens_per_point_input` 和 `tokens_per_point_output`：主要使用的字段

#### 数据迁移说明

对于现有的 `separate_io=False` 的记录：
- 不需要强制迁移
- 读取时如果 `separate_io=False`，使用 `tokens_per_point` 作为输入和输出的值
- 用户更新汇率时，自动转换为 `separate_io=True` 并设置独立的输入/输出值

### 4. 前端组件结构

#### 新建文件

```
frontend/src/views/admin/
└── ModelRatesPage.vue         # 批量设置页面

frontend/src/components/admin/
└── ModelRateCollapse.vue      # 折叠面板子组件（可选）
```

#### 修改文件

```
frontend/src/views/admin/
└── AdminModelProvidersPage.vue  # 简化模型配置对话框

frontend/src/services/apiClient.ts
└── batchUpdateModelRates()       # 新增 API 方法

frontend/src/types/index.ts
└── 相关类型定义
```

### 5. 路由配置

```typescript
// frontend/src/router/index.ts
{
  path: '/admin/model-rates',
  name: 'AdminModelRates',
  component: () => import('@/views/admin/ModelRatesPage.vue'),
  meta: { requiresAdmin: true, title: '模型汇率配置' }
}
```

### 5.1 菜单配置

需要在管理后台布局中添加菜单项。根据现有的管理后台菜单结构（通常在 `AdminLayout.vue` 或相关配置中）：

```typescript
// 管理后台菜单配置（示例）
const adminMenuItems = [
  // ... 现有菜单项
  {
    path: '/admin/model-rates',
    title: '模型汇率配置',
    icon: 'Money', // 或其他合适的图标
    order: 5       // 菜单排序
  }
]
```

### 6. 用户交互流程

#### 批量设置页面

1. 打开页面，自动加载数据
2. 默认展开第一个供应商的面板
3. 修改汇率时，自动标记为已修改
4. 点击"保存"时，只提交被修改的项
5. 成功后显示提示：已更新 N 个模型的汇率配置
6. 点击"重置"，恢复所有修改为原始值

#### 模型配置对话框

1. 点击模型的"配置"按钮
2. 在单表单中修改信息
3. 点击"保存"：
   - 更新模型基本信息
   - 如果汇率配置不存在，自动创建
   - 如果汇率配置已存在，更新汇率值
4. 成功后刷新列表

### 7. 验证规则

1. 输入/输出汇率必须为正整数
2. 输入汇率不能为空（如果启用汇率配置）
3. 输出汇率不能为空（如果启用汇率配置）
4. 批量保存时，跳过验证失败的项并记录错误

### 8. 错误处理

1. 网络错误：显示通用错误提示
2. 验证错误：高亮显示错误字段
3. 部分成功：显示成功/失败数量

## 验收标准

### 批量设置页面
1. [ ] 页面能够正确加载和显示所有已启用供应商的已启用模型
2. [ ] 按供应商分组展示，折叠面板正常展开/折叠
3. [ ] 默认展开第一个供应商的面板
4. [ ] 修改汇率后，字段显示修改标记（如变色或图标）
5. [ ] 保存时只提交被修改的项
6. [ ] 保存成功后显示提示："已更新 N 个模型的汇率配置"
7. [ ] 重置功能能够恢复所有修改为原始值
8. [ ] 没有汇率配置的模型显示空值或占位符

### 模型配置对话框
1. [ ] 打开模型配置对话框，确认只有单表单（无 tab 切换）
2. [ ] 确认"统一汇率"选项已移除
3. [ ] 确认输入/输出汇率字段独立显示
4. [ ] 新模型保存时自动创建汇率配置
5. [ ] 已有汇率配置的模型保存时更新汇率值
6. [ ] 汇率配置的启用/禁用状态正常工作

### 错误处理和验证
1. [ ] 输入/输出汇率必须为正整数，否则显示验证错误
2. [ ] 启用汇率配置时，输入/输出汇率不能为空
3. [ ] 网络错误时显示通用错误提示
4. [ ] 批量保存时，任何错误都导致全部回滚

## 实施顺序

1. **后端**：新增获取所有模型汇率状态的接口 (`GET /admin/model-rates/status`)
2. **后端**：新增批量更新接口 (`POST /admin/model-rates/batch-update`)
3. **前端**：创建批量设置页面 (`ModelRatesPage.vue`)
4. **前端**：添加路由和菜单配置
5. **前端**：改造模型配置对话框，简化为单表单
6. **测试**：端到端测试
