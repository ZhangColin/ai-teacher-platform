# AI 智能备课平台 (AI Teacher Platform)

这是一个基于大语言模型（Kimi/DeepSeek）的垂直领域教学辅助平台。它允许教师通过自然语言对话，自动生成交互式 HTML5 课件、SVG 可视化图表以及标准化的 Markdown 教学设计，并支持实时预览与导出。

## ✨ 核心功能

* **智能意图路由 (Intent Routing)**：自动识别用户需求是“制作交互课件(Code)”、“绘制图表(Visual)”还是“编写教案(Plan)”。
* **所见即所得 (Live Preview)**：
* **交互课件**：自动渲染 HTML5/JS 物理、数学仿真动画，支持安全沙箱运行。
* **矢量绘图**：自动渲染 SVG 结构示意图（如生物细胞、化学分子）。
* **教学文档**：Markdown 格式的教案自动排版渲染。


* **上下文记忆 (Context Memory)**：支持多轮对话，可对生成的课件进行持续修改（如“把小球颜色改成红色”）。
* **本地化导出**：支持一键下载生成的 HTML 源码或 Markdown 文档。
* **分屏生产力 UI**：左侧指令交互，右侧实时演示。

## 🛠 技术栈

### Backend (后端)

**Python版本（原始）：**
* **Core**: Python 3.10+
* **Framework**: FastAPI
* **LLM Integration**: OpenAI SDK (兼容 Kimi / DeepSeek API)
* **Data Validation**: Pydantic Schema

**Java版本（迁移完成）：**
* **Core**: Java 17+
* **Framework**: Spring Boot 3.2.0
* **Reactive**: Spring WebFlux (响应式编程)
* **ORM**: Spring Data JPA + MyBatis-Plus
* **Security**: Spring Security + JWT
* **AI Framework**: LangChain4j 0.29.1
* **Testing**: JUnit 5 + Mockito

**双后端架构：**
- Python后端（FastAPI）：8000端口 - 稳定版本
- Java后端（Spring Boot）：8080端口 - 新迁移版本

两个后端使用相同的数据库，数据完全兼容。

### Frontend (前端)

* **Framework**: Vue 3 (Composition API)
* **Language**: TypeScript
* **Build Tool**: Vite
* **Styling**: Tailwind CSS v3 (+ Typography Plugin)
* **Markdown**: markdown-it

## 🚀 快速启动指南

### 1. 环境准备

确保本地已安装 Node.js (v18+) 和 Python (3.10+)。

### 2. 启动后端服务

```bash
cd backend

# 1. 创建并激活虚拟环境 (推荐)
python -m venv venv
# Mac/Linux:
source venv/bin/activate
# Windows:
# .\venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
# 复制 .env.example 为 .env，并填入您的 KIMI_API_KEY
cp .env.example .env

# 4. 启动 API 服务 (运行在 http://localhost:8000)
python main.py

```

### 3. 启动前端服务

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev

```

### 4. 访问平台

打开浏览器访问：http://localhost:5173

## 📂 目录结构

```text
ai-teacher-platform/
├── backend/
│   ├── main.py           # FastAPI 入口与业务逻辑
│   ├── schemas.py        # Pydantic 数据模型定义
│   ├── prompts.py        # System Prompts 与路由逻辑
│   ├── .env              # 配置文件 (API Keys)
│   └── requirements.txt  # Python 依赖
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatLayout.vue    # 主布局与聊天逻辑
│   │   │   ├── CodePreview.vue   # HTML/SVG 渲染与清洗组件
│   │   │   └── MarkdownViewer.vue# 教案渲染组件
│   │   ├── types.ts              # TypeScript 类型定义
│   │   └── ...
│   ├── tailwind.config.js
│   └── vite.config.ts
└── README.md

```

## 📝 常见问题

1. **样式显示异常**：请检查 `frontend/tailwind.config.js` 是否正确配置了 `@tailwindcss/typography` 插件，并重启前端服务。
2. **代码无法预览**：系统内置了代码清洗正则，通常能自动去除 Markdown 标记。如果遇到极其特殊的格式，请检查 `ChatLayout.vue` 中的 `cleanCode` 函数。