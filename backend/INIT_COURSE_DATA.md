# 课程文档模块 - 初始化数据说明

## 初始化步骤

### 1. 确保数据库迁移已完成

```bash
cd backend
alembic upgrade head
```

### 2. 执行初始化SQL脚本

```bash
# 方法1：使用mysql命令行
mysql -u your_username -p your_database < init_course_data.sql

# 方法2：在MySQL客户端中执行
source /path/to/init_course_data.sql;
```

### 3. 验证数据

登录数据库，验证数据是否插入成功：

```sql
-- 查看目录
SELECT * FROM course_categories ORDER BY parent_id, `order`;

-- 查看文档
SELECT * FROM course_documents ORDER BY category_id, `order`;
```

## 示例数据说明

### 目录结构

```
AI基础知识 (cat-001)
├── 什么是AI (cat-003)
└── AI的历史 (cat-004)

AI工具应用 (cat-002)
└── ChatGPT使用指南 (cat-005)
```

### 示例文档

1. **AI是什么？** (`doc-001`)
   - 所属目录：什么是AI
   - 文件路径：`backend/static/course_docs/doc-001/content.md`
   - 内容：介绍AI的基本概念和类型

2. **AI的发展历程** (`doc-002`)
   - 所属目录：AI的历史
   - 文件路径：`backend/static/course_docs/doc-002/content.md`
   - 内容：从图灵测试到ChatGPT的发展历程

3. **ChatGPT入门指南** (`doc-003`)
   - 所属目录：ChatGPT使用指南
   - 文件路径：`backend/static/course_docs/doc-003/content.md`
   - 内容：ChatGPT的使用方法和技巧

## 添加更多内容

### 通过后台管理界面

1. 访问 `/admin/course-categories` 管理目录
2. 访问 `/admin/course-documents` 管理文档
3. 上传Markdown文件创建新文档

### 手动添加

1. 在 `backend/static/course_docs/` 下创建新目录（以文档ID命名）
2. 在目录中创建 `content.md` 文件
3. 在数据库中插入对应的记录

## 注意事项

- 文档ID必须与文件系统中的目录名一致
- 文件路径格式：`course_docs/{doc_id}/content.md`
- 确保Markdown文件使用UTF-8编码
- 目录和文档的`order`字段用于排序，数值越小越靠前
- 删除目录前需确保目录下没有文档和子目录

