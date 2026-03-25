# 聊天界面模型选择器改进设计

**日期**: 2026-03-25
**状态**: 已批准

## 概述

本设计描述聊天界面模型选择器的四个改进：
1. 移除默认模型的"（默认）"标识
2. 会话恢复时记住用户的模型选择
3. 下拉框打开时滚动到当前选择的模型
4. 标题生成使用会话的模型并扣减积分

## 需求

### 1. 移除"（默认）"标识
- **问题**: 当前显示 `deepseek-chat（默认）`，标识冗余
- **目标**: 默认模型不显示特殊标识

### 2. 会话恢复模型选择
- **问题**: 切换会话后，模型选择器重置为工具默认模型
- **目标**: 恢复会话时，使用数据库存储的 `model_provider` 和 `model_name`

### 3. 下拉框滚动定位
- **问题**: 打开下拉框时，滚动条在顶部，当前选择的模型可能不可见
- **目标**: 打开下拉框时，确保当前选择的模型在可见区域内

### 4. 标题生成使用会话模型
- **问题**: 标题生成使用环境变量配置，无法扣积分
- **目标**: 使用会话的模型生成标题，并正确扣减积分

## 设计

### 需求 1: 移除"（默认）"标识

**文件**: `frontend/src/components/ModelSelector.vue`

**改动**:
```diff
- return model ? `${model.name}（默认）` : defaultModel.value
+ return model ? model.name : defaultModel.value
```

### 需求 2: 会话恢复模型选择

**数据模型**:
- `SessionModel` 已有 `model_provider` 和 `model_name` 字段
- 后端 API `GET /api/v1/sessions/{session_id}` 需返回这些字段

**前端改动**:

1. `frontend/src/services/apiClient.ts`
   - 确保 `getSessionDetail()` 返回类型包含 `model_provider` 和 `model_name`

2. `frontend/src/stores/sessionStore.ts`
   - 在 `restoreSession()` 中恢复模型选择：
   ```typescript
   if (response.model_provider && response.model_name) {
     currentModel.value = `${response.model_provider}:${response.model_name}`
   }
   ```

### 需求 3: 下拉框滚动定位

**文件**: `frontend/src/components/ModelSelector.vue`

**实现**:
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

### 需求 4: 标题生成使用会话模型

**架构变化**:
- `TitleGenerator` 不再从环境变量读取配置
- 改为接收 `model_config` 参数（provider + model_name）
- 通过 `ModelProviderService` 获取加密的 API Key

**流程**:
```
第一轮对话完成
  ↓
调用 TitleGenerator.generate_title(message, response, model_provider, model_name)
  ↓
从 ModelProviderService 获取 API Key（解密）
  ↓
调用 AI API 生成标题
  ↓
记录 token 消耗
  ↓
通过 PointService 扣减积分
  ↓
返回标题
```

**涉及文件**:
- `backend/src/services/title_generator.py` - 修改为使用数据库配置
- `backend/src/interfaces/routers/tools/chat.py` - 传入模型配置，扣减积分
- `backend/src/interfaces/dependencies.py` - 更新依赖注入

## 测试

### 前端测试
1. 新会话：默认模型显示正确，无"（默认）"标识
2. 切换模型：选择后立即生效
3. 切换会话：模型选择器显示该会话的模型
4. 下拉框：打开时滚动到选中项

### 后端测试
1. 标题生成使用会话模型
2. 标题生成正确扣减积分
3. 无可用模型时的降级处理

## 实施顺序

1. 需求 1（最简单）
2. 需求 3（独立改动）
3. 需求 2（前后端配合）
4. 需求 4（最复杂，需谨慎）
