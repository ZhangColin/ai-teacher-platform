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
# 复制 .env.example 为 .env，并填入您的 API 密钥
cp .env.example .env

# 重要：需要配置以下环境变量
# - DATABASE_URL: MySQL 数据库连接字符串
# - JWT_SECRET_KEY: JWT 签名密钥
# - API_KEY_ENCRYPTION_KEY: API Key 加密密钥（用于加密数据库中的敏感信息）
# 生成加密密钥: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#
# 可选：配置 AI 服务商 API Key（如果不在管理后台配置）
# - OPENAI_API_KEY, DEEPSEEK_API_KEY, KIMI_API_KEY, GLM_API_KEY

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

## ⚙️ 模型供应商配置

平台支持通过管理后台配置多个 AI 模型供应商，无需修改环境变量。

### 配置方式

1. **登录管理后台**：使用管理员账号登录
2. **进入模型供应商配置**：点击侧边栏 "配置管理" > "模型供应商"
3. **添加供应商**：
   - 填写供应商代码（如：openai, deepseek）
   - 填写供应商名称
   - 填写 API 密钥（将自动加密存储）
   - 填写 API 地址（如：https://api.openai.com/v1）
   - 设置是否启用、是否为默认供应商
4. **添加模型**：点击供应商的"模型"按钮，添加该供应商支持的模型
   - 填写模型代码（如：gpt-4, deepseek-chat）
   - 填写模型名称
   - 填写支持能力（逗号分隔，如：chat,code,image）

### 配置优先级

1. **数据库配置**（优先）：从管理后台配置的模型供应商和模型
2. **环境变量**（回退）：如果数据库中没有配置，自动回退到环境变量

### API Key 加密

所有存储在数据库中的 API Key 都使用 Fernet 对称加密算法加密，确保敏感信息安全。

## 📝 常见问题

1. **样式显示异常**：请检查 `frontend/tailwind.config.js` 是否正确配置了 `@tailwindcss/typography` 插件，并重启前端服务。
2. **代码无法预览**：系统内置了代码清洗正则，通常能自动去除 Markdown 标记。如果遇到极其特殊的格式，请检查 `ChatLayout.vue` 中的 `cleanCode` 函数。