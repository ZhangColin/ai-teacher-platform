# 作品展示模块 - 实施指南

**文档版本**: v1.0  
**创建日期**: 2026-01-10  
**架构师**: System Architect Team  
**目标读者**: 全栈开发工程师

---

## 📋 目录

1. [概述](#概述)
2. [实施步骤](#实施步骤)
3. [后端实现](#后端实现)
4. [前端实现](#前端实现)
5. [测试验收](#测试验收)
6. [注意事项](#注意事项)

---

## 概述

### 模块定位
作品展示模块是一个**独立的HTML作品展示平台**，用于集中展示优秀的HTML创意作品，为用户提供灵感和参考。

### 核心特点
- ✅ **功能参考**：与常用工具模块高度相似（分类+卡片+详情页+HTML沙箱）
- ✅ **独立实现**：采用独立的数据表、API、前端页面
- ✅ **代码复用**：复用现有组件和沙箱实现
- ✅ **遵循规范**：遵循现有的前后端框架和代码规范

### 设计文档依据
- API接口设计：`docs/design/api_interface.md` (v3.1, 第6章)
- 数据模型设计：`docs/design/data_models.md` (v4.1, 第2.9、2.10、3.7章)
- 需求文档：`docs/requirements/works_display_spec.md` (v1.0)

---

## 实施步骤

### 步骤总览
```
1. 数据库迁移（创建表）
2. 后端实现（API接口）
3. 前端实现（页面和组件）
4. 测试验收
```

### 时间估算
- 后端实现：1-2天
- 前端实现：2-3天
- 测试验收：1天
- **总计**：4-6天

---

## 后端实现

### 1. 数据库迁移

#### 执行迁移脚本
```bash
# 进入后端目录
cd backend

# 执行迁移脚本
mysql -u <username> -p <database_name> < migrations/create_works_tables.sql

# 验证表创建
mysql -u <username> -p <database_name> -e "SHOW TABLES LIKE 'work%';"
```

**预期输出**：
```
+-----------------------+
| Tables_in_db (work%)  |
+-----------------------+
| work_categories       |
| works                 |
+-----------------------+
```

---

### 2. 数据模型定义

在 `backend/src/db_models.py` 中添加作品展示的ORM模型：

```python
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class WorkCategory(Base):
    """作品分类表"""
    __tablename__ = "work_categories"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(50), nullable=True)
    order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    works = relationship("Work", back_populates="category")


class Work(Base):
    """作品表"""
    __tablename__ = "works"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    category_id = Column(String(36), ForeignKey("work_categories.id"), nullable=False)
    icon = Column(String(50), nullable=True)
    html_path = Column(String(255), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    visible = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    category = relationship("WorkCategory", back_populates="works")
```

---

### 3. Pydantic模型定义

在 `backend/src/models.py` 中添加API响应模型：

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============ 作品展示模块 ============

class WorkListItem(BaseModel):
    """作品列表项"""
    id: str = Field(..., description="作品ID")
    name: str = Field(..., description="作品名称")
    description: str = Field(..., description="作品描述")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")

    class Config:
        from_attributes = True


class WorkCategoryGroup(BaseModel):
    """作品分类组"""
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    icon: Optional[str] = Field(None, description="分类图标")
    order: int = Field(..., description="分类排序")
    works: List[WorkListItem] = Field(..., description="该分类下的作品列表")

    class Config:
        from_attributes = True


class WorkCategoryResponse(BaseModel):
    """作品分类响应"""
    categories: List[WorkCategoryGroup] = Field(..., description="分类列表（按order排序）")


class WorkDetail(BaseModel):
    """作品详情"""
    id: str = Field(..., description="作品ID")
    name: str = Field(..., description="作品名称")
    description: str = Field(..., description="作品描述")
    category_id: str = Field(..., description="所属分类ID")
    category_name: str = Field(..., description="所属分类名称")
    icon: Optional[str] = Field(None, description="图标标识")
    order: int = Field(..., description="排序顺序")
    html_url: str = Field(..., description="HTML文件访问URL")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
```

---

### 4. Service层实现

创建 `backend/src/services/work_service.py`：

```python
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from ..db_models import Work, WorkCategory
from ..models import WorkCategoryResponse, WorkCategoryGroup, WorkListItem, WorkDetail
from fastapi import HTTPException

class WorkService:
    """作品展示服务"""
    
    @staticmethod
    def get_categories_with_works(db: Session) -> WorkCategoryResponse:
        """获取所有可见的作品分类及其下的作品列表"""
        # 查询所有分类，按order排序
        categories = db.query(WorkCategory).order_by(WorkCategory.order).all()
        
        category_groups = []
        for category in categories:
            # 查询该分类下的可见作品，按order排序
            works = db.query(Work).filter(
                Work.category_id == category.id,
                Work.visible == True
            ).order_by(Work.order).all()
            
            # 如果该分类下没有可见作品，则不返回该分类
            if not works:
                continue
            
            # 转换为响应模型
            work_items = [
                WorkListItem(
                    id=work.id,
                    name=work.name,
                    description=work.description,
                    icon=work.icon,
                    order=work.order
                )
                for work in works
            ]
            
            category_groups.append(WorkCategoryGroup(
                id=category.id,
                name=category.name,
                icon=category.icon,
                order=category.order,
                works=work_items
            ))
        
        return WorkCategoryResponse(categories=category_groups)
    
    @staticmethod
    def get_work_detail(db: Session, work_id: str) -> WorkDetail:
        """获取单个作品的详细信息"""
        # 查询作品，关联查询分类信息
        work = db.query(Work).filter(
            Work.id == work_id,
            Work.visible == True
        ).options(joinedload(Work.category)).first()
        
        if not work:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "WORK_NOT_FOUND",
                    "error_message": "作品不存在或已下线"
                }
            )
        
        # 生成HTML访问URL
        html_url = f"/static/{work.html_path}"
        
        return WorkDetail(
            id=work.id,
            name=work.name,
            description=work.description,
            category_id=work.category_id,
            category_name=work.category.name,
            icon=work.icon,
            order=work.order,
            html_url=html_url,
            created_at=work.created_at
        )
```

---

### 5. API路由实现

在 `backend/src/main.py` 中添加作品展示的路由：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .services.work_service import WorkService
from .models import WorkCategoryResponse, WorkDetail

# 创建作品展示路由
works_router = APIRouter(prefix="/api/v1/works", tags=["works"])

@works_router.get("/categories", response_model=WorkCategoryResponse)
async def get_work_categories(db: Session = Depends(get_db)):
    """获取作品分类列表"""
    return WorkService.get_categories_with_works(db)

@works_router.get("/{work_id}", response_model=WorkDetail)
async def get_work_detail(work_id: str, db: Session = Depends(get_db)):
    """获取作品详情"""
    return WorkService.get_work_detail(db, work_id)

# 在主app中注册路由
app.include_router(works_router)
```

---

## 前端实现

### 1. 创建Store

创建 `frontend/src/stores/worksStore.ts`：

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

// 类型定义（参考commonToolsStore）
interface WorkCard {
  id: string
  name: string
  description: string
  icon?: string
  order: number
}

interface WorkCategory {
  id: string
  name: string
  icon?: string
  order: number
  works: WorkCard[]
}

interface WorkDetail {
  id: string
  name: string
  description: string
  category_id: string
  category_name: string
  icon?: string
  order: number
  html_url: string
  created_at: string
}

export const useWorksStore = defineStore('works', () => {
  const categories = ref<WorkCategory[]>([])
  const currentWork = ref<WorkDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 获取作品分类列表
  async function fetchCategories() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/v1/works/categories')
      categories.value = response.data.categories
    } catch (err: any) {
      error.value = err.response?.data?.error_message || '获取作品列表失败'
      console.error('Failed to fetch work categories:', err)
    } finally {
      loading.value = false
    }
  }
  
  // 获取作品详情
  async function fetchWorkDetail(workId: string) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/works/${workId}`)
      currentWork.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.error_message || '获取作品详情失败'
      console.error('Failed to fetch work detail:', err)
    } finally {
      loading.value = false
    }
  }
  
  return {
    categories,
    currentWork,
    loading,
    error,
    fetchCategories,
    fetchWorkDetail
  }
})
```

---

### 2. 创建页面组件

#### 作品卡片页（WorksDisplayPage.vue）

参考 `CommonToolsPage.vue` 的实现，复用 `CategoryNav` 和 `CardGrid` 组件。

创建 `frontend/src/views/WorksDisplayPage.vue`：

```vue
<template>
  <div class="works-display-page">
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">作品展示</h1>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="text-gray-500">加载中...</div>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="text-red-500 text-center">
        {{ error }}
      </div>
      
      <!-- 作品列表 -->
      <div v-else>
        <!-- 按分类展示作品 -->
        <div v-for="category in categories" :key="category.id" class="mb-12">
          <h2 class="text-2xl font-semibold mb-4 flex items-center">
            <span v-if="category.icon" class="mr-2">
              <!-- heroicons 图标 -->
            </span>
            {{ category.name }}
          </h2>
          
          <!-- 作品卡片网格 -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              v-for="work in category.works"
              :key="work.id"
              @click="navigateToWork(work.id)"
              class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-6"
            >
              <div v-if="work.icon" class="text-4xl mb-4">
                <!-- heroicons 图标 -->
              </div>
              <h3 class="text-xl font-semibold mb-2">{{ work.name }}</h3>
              <p class="text-gray-600">{{ work.description }}</p>
            </div>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="categories.length === 0" class="text-center text-gray-500 py-16">
          暂无作品
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useWorksStore } from '@/stores/worksStore'

const router = useRouter()
const worksStore = useWorksStore()
const { categories, loading, error } = storeToRefs(worksStore)

onMounted(() => {
  worksStore.fetchCategories()
})

function navigateToWork(workId: string) {
  router.push({ name: 'work-detail', params: { workId } })
}
</script>
```

#### 作品详情页（WorkDetailPage.vue）

参考 `HtmlToolView.vue` 的实现，复用HTML沙箱渲染逻辑。

创建 `frontend/src/views/WorkDetailPage.vue`：

```vue
<template>
  <div class="work-detail-page h-screen flex flex-col">
    <!-- 顶部工具栏 -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div class="flex items-center">
        <button @click="goBack" class="mr-4 text-gray-600 hover:text-gray-900">
          <span class="text-sm">← 返回</span>
        </button>
        <h1 class="text-lg font-semibold">{{ currentWork?.name }}</h1>
      </div>
      
      <button
        @click="toggleFullscreen"
        class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        {{ isFullscreen ? '退出全屏' : '全屏' }}
      </button>
    </div>
    
    <!-- HTML内容区域 -->
    <div class="flex-1 relative">
      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center h-full">
        <div class="text-gray-500">加载中...</div>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="flex justify-center items-center h-full">
        <div class="text-red-500">{{ error }}</div>
      </div>
      
      <!-- HTML沙箱 -->
      <iframe
        v-else-if="currentWork"
        :src="currentWork.html_url"
        sandbox="allow-scripts allow-forms allow-popups allow-same-origin"
        class="w-full h-full border-0"
        @load="onIframeLoad"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useWorksStore } from '@/stores/worksStore'

const route = useRoute()
const router = useRouter()
const worksStore = useWorksStore()
const { currentWork, loading, error } = storeToRefs(worksStore)

const isFullscreen = ref(false)

onMounted(() => {
  const workId = route.params.workId as string
  worksStore.fetchWorkDetail(workId)
})

function goBack() {
  router.push({ name: 'works-display' })
}

function toggleFullscreen() {
  if (!isFullscreen.value) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function onIframeLoad() {
  console.log('Work HTML loaded')
}
</script>
```

---

### 3. 配置路由

在 `frontend/src/router/index.ts` 中添加路由：

```typescript
{
  path: '/works',
  name: 'works-display',
  component: () => import('@/views/WorksDisplayPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/works/:workId',
  name: 'work-detail',
  component: () => import('@/views/WorkDetailPage.vue'),
  meta: { requiresAuth: true }
}
```

---

## 测试验收

### 后端测试

创建 `backend/tests/test_works_api.py`：

```python
import pytest
from fastapi.testclient import TestClient
from ..src.main import app

client = TestClient(app)

def test_get_work_categories():
    """测试获取作品分类列表"""
    response = client.get("/api/v1/works/categories")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)

def test_get_work_detail():
    """测试获取作品详情"""
    # 需要先插入测试数据
    work_id = "test-work-id"
    response = client.get(f"/api/v1/works/{work_id}")
    
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "html_url" in data
    elif response.status_code == 404:
        # 作品不存在
        assert response.json()["error_code"] == "WORK_NOT_FOUND"

def test_work_not_found():
    """测试作品不存在的情况"""
    response = client.get("/api/v1/works/non-existent-work")
    assert response.status_code == 404
    assert response.json()["error_code"] == "WORK_NOT_FOUND"
```

### 功能验收清单

参考 `docs/requirements/works_display_spec.md` 的验收标准：

#### ✅ 作品卡片页
- [ ] 用户点击顶部导航"作品展示"，正确跳转到作品卡片页
- [ ] 页面按分类展示作品，分类顺序正确
- [ ] 每个作品卡片显示：图标、名称、描述
- [ ] 分类下无作品时，该分类不显示
- [ ] 点击作品卡片，正确跳转到作品详情页

#### ✅ 作品详情页
- [ ] HTML作品在沙箱中运行，与常用工具的沙箱机制一致
- [ ] HTML页面占满作品详情页的内容区域
- [ ] "全屏"按钮功能正常，进入浏览器全屏模式
- [ ] 全屏模式下"退出全屏"按钮功能正常
- [ ] "返回"按钮正确跳转到作品卡片页
- [ ] 沙箱隔离有效，HTML代码不影响主系统

---

## 注意事项

### ⚠️ 重要约束

1. **遵循现有框架**
   - 不要重新发明轮子，复用现有组件和工具函数
   - 参考常用工具模块的实现方式
   - 保持代码风格与现有代码一致

2. **不要改坏现有功能**
   - 修改共享组件时要小心，确保不影响其他模块
   - 添加新路由时不要与现有路由冲突
   - 数据库迁移脚本要使用 `IF NOT EXISTS` 避免重复创建

3. **安全性**
   - HTML沙箱配置必须与常用工具保持一致
   - 使用 `sandbox="allow-scripts allow-forms allow-popups allow-same-origin"`
   - 不要修改沙箱安全策略

4. **独立性**
   - 作品展示模块应该独立实现，不依赖常用工具的代码
   - 可以复用通用组件，但不要耦合具体业务逻辑
   - 数据表完全独立，不共享

### 📝 代码规范

- **命名规范**：参考现有代码的命名风格
- **注释**：关键逻辑添加注释说明
- **类型安全**：TypeScript 代码要有完整的类型定义
- **错误处理**：统一的错误处理和提示

### 🔍 测试建议

1. 先测试后端API接口是否正常
2. 再测试前端页面展示是否正确
3. 最后测试全屏、返回等交互功能

### 📦 文件清单

**后端文件**（新建）：
- `backend/migrations/create_works_tables.sql` - 数据库迁移脚本
- `backend/src/services/work_service.py` - 业务逻辑服务
- `backend/tests/test_works_api.py` - API测试

**后端文件**（修改）：
- `backend/src/db_models.py` - 添加ORM模型
- `backend/src/models.py` - 添加Pydantic模型
- `backend/src/main.py` - 添加路由

**前端文件**（新建）：
- `frontend/src/stores/worksStore.ts` - 状态管理
- `frontend/src/views/WorksDisplayPage.vue` - 作品卡片页
- `frontend/src/views/WorkDetailPage.vue` - 作品详情页

**前端文件**（修改）：
- `frontend/src/router/index.ts` - 添加路由

**配置文件**（已存在，无需修改）：
- `configs/navigation.yaml` - 导航配置（已包含作品展示模块）

---

## 参考文档

- 需求文档：`docs/requirements/works_display_spec.md`
- API接口设计：`docs/design/api_interface.md` (v3.1, 第6章)
- 数据模型设计：`docs/design/data_models.md` (v4.1)
- 常用工具实现参考：`frontend/src/views/CommonToolsPage.vue`, `HtmlToolView.vue`

---

**文档结束**
