# Cursor Rules 目录

本目录包含项目的角色规则文件，用于在 Cursor IDE 中快速切换不同的工作角色。

## 可用角色

- **product-manager.md** - 产品经理角色
  - 适用于：需求分析、产品设计阶段
  - 核心职责：明确"要解决什么问题"，定义"用户如何使用"

- **fullstack-developer.md** - 全栈开发工程师角色
  - 适用于：代码编写、调试、重构与测试阶段
  - 核心职责：将设计文档转化为经过测试严密保护的代码

- **system-architect.md** - 系统架构师角色
  - 适用于：架构设计与技术设计阶段
  - 核心职责：将业务需求转化为技术设计，定义数据契约

- **devops-engineer.md** - DevOps 工程师角色
  - 适用于：项目部署、CI/CD 配置、服务器环境搭建
  - 核心职责：基础设施即代码、持续交付、环境一致性

## 如何使用

### 方法1：在 Cursor Settings 中切换
1. 打开 Cursor Settings（`Cmd/Ctrl + ,`）
2. 找到 "Rules and Commands" 部分
3. 在 "Rules" 中选择对应的规则文件（如 `product-manager.mdc`）

**注意**：Cursor 的规则文件必须使用 `.mdc` 扩展名，不是 `.md`。

### 方法2：通过项目规则文件
Cursor 会自动识别 `.cursor/rules/` 目录下的 `.mdc` 规则文件，你可以在 Settings 中选择使用哪个规则文件。

## 完整角色定义

每个角色的完整定义、工作方法论和检查清单，请参考：
- `docs/roles/product_manager.md`
- `docs/roles/fullstack_developer.md`
- `docs/roles/system_architect.md`
- `docs/roles/devops_engineer.md`

## 项目通用规则

项目通用的工作铁律、项目背景和技术栈配置，请参考项目根目录的 `.cursorrules` 文件。

