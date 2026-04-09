# AGENTS.md - Project Context

## 1. Project Overview (项目概览)

* **Name**: Anima Isle (言屿)
* **Goal**: 一个基于 AI 的情感陪伴与视觉化治愈 App。通过三轮对话引导用户倾诉情绪，利用 AI 将情绪转译为“视觉图像+三行诗”的船票资产，并提供共感地图社交功能。
* **State**: MVP 开发阶段 (后端逻辑已完成 98%，进入联调与前端开发阶段)。
* **Core Value**: 情绪转译、视觉治愈、共感社交。
* 



## 2. Tech Stack (技术栈)

* **Language**: Python 3.9+
* **Web Framework**: FastAPI (Async Mode)
* **Database (Relational)**: Aliyun RDS MySQL 8.0 (用于存储用户、会话、票据、日志)
* **Database (Vector)**: Zilliz Cloud (Milvus 托管版) - Dimension: 1024, Metric: Cosine
* **AI Services (Model)**: Aliyun DashScope
* LLM: `qwen-turbo` (通义千问)
* Embedding: `text-embedding-v4`


* **Key Libraries**:
* ORM: `SQLAlchemy` (1.4/2.0 style)
* Schema: `Pydantic` v2
* Auth: `python-jose` (JWT), `passlib[bcrypt]`
* Network: `httpx` (异步请求), `tenacity` (重试机制)
* Migration: `Alembic`

## 3. Coding Conventions (代码规范)

* **Naming**:
* Variables/Functions: `snake_case` (e.g., `user_id`, `get_current_user`)
* Classes/Models: `PascalCase` (e.g., `ChatSession`, `UserDTO`)
* Constants: `UPPER_CASE` (e.g., `ACCESS_TOKEN_EXPIRE_MINUTES`)


* **Async/Await**: 所有 I/O 密集型操作（数据库查询、AI API 调用、微信接口）必须使用 `async/await`，禁止在 Router 中使用阻塞代码。
* **Type Hinting**: **强制使用**。Pydantic 模型需配置 `model_config = ConfigDict(from_attributes=True)` 以兼容 ORM。
* **Error Handling**:
* 业务层错误抛出 `HTTPException`。
* AI/外部接口错误需捕获并记录日志 (`logging.error`)，且必须有兜底逻辑 (Fallback)，不能导致服务 500 崩溃。


* **Security**:
* 密码必须 Hash 存储。
* 敏感配置 (API Keys, DB URL) 必须从环境变量 (`.env`) 读取。

* **Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutionssimple and focused.**

- Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability. Don't add docstrings, comments, or type annotations to code you didn't change. Only add comments where the logic isn't self-evident.

- Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use feature flags or backwards-compatibility shims when you can just change the code.

- Don't create helpers, utilities, or abstractions for one-time operations. Don't design for hypothetical future requirements. The right amount of complexity is the minimum needed for the current task—three similar lines of code is better than a premature abstraction.

- Avoid backwards-compatibility hacks like renaming unused _vars, re-exporting types, adding // removed comments for removed code, etc. If you are certain that something is unused, you can delete it completely.

- After each completed modification round, create a commit before moving on to the next requested change whenever the current repository layout allows it.

- After each completed modification round, push the resulting commit to GitHub whenever the current repository has a configured remote that matches the intended project repository. When pushing from this local machine, prefer the user's local HTTP proxy at `http://127.0.0.1:22307`.

## 4. Architecture & Structure (架构与目录)

* `app/`: 核心应用源码
* `main.py`: 应用入口，包含生命周期管理 (`lifespan`) 和全局中间件。
* `database.py`: 数据库连接池配置 (MySQL)。
* `deps.py`: 依赖注入 (Token 校验、获取当前用户)。
* `models.py`: SQLAlchemy 数据库表定义 (User, Ticket, ChatSession, AIChatLog)。
* `schemas.py`: Pydantic 数据交互模型 (Request/Response)。
* `crud.py`: 数据库原子操作层 (只负责 SQL 读写，不含业务逻辑)。
* `routers/`: 业务路由层 (Controller)
* `auth.py`: 登录与鉴权 (Email/WeChat)。
* `user.py`: 用户信息与偏好设置。
* `chat.py`: **[核心]** 三轮对话状态机、AI 生成、Reroll 逻辑。
* `ticket.py`: 记忆航线列表、详情、**烟雾测试接口**。
* `square.py`: 共感地图、智能 Tag 推荐、社交互动。


* `utils/`: 工具箱
* `ai_engine.py`: 封装 DashScope 调用 (Retry, Risk Check, Tag Gen)。
* `search_engine.py`: 封装 Zilliz 搜索 (含风格过滤、兜底图)。
* `wechat.py`: 封装微信 `code2session`。
* `security.py`: JWT 生成与哈希工具。




* `data/`: 静态资源 (e.g., `questions.json`)。
* `alembic/`: 数据库迁移脚本。

## 5. Business Logic & Constraints (业务逻辑与约束)

* **Chat FSM (聊天状态机)**:
* 会话严格遵循 `Step 0 (Start)` -> `Step 1 (Q1 Answered)` -> `Step 2 (Generated)` -> `Step 3 (Finished)` 的流转。
* 用户必须回答完 Q1 才能回答 Q2。


* **Stateless Reroll (无状态重随)**:
* 用户的 Embedding 向量缓存于 MySQL `ChatSession.last_embedding_vector`。
* 切换风格时，直接读取缓存向量去 Zilliz 检索，**不重复调用 Embedding API**。


* **Privacy First (隐私优先)**:
* 生成的 Ticket 默认为私密 (`is_public=False`)。
* 只有调用 `/square/publish` 接口并选定 Tag 后，才变为公开。


* 
**Smoke Test (烟雾测试)**:


* 前端“兑换实体船票”是假按钮。
* 点击后后端调用 `/tickets/{uid}/print_intent`，仅记录 `is_printed_intent=True`，用于统计商业意向。


* **Data Tracking (数据埋点)**:
* 必须记录 AI 的原始输入输出到 `AIChatLog` 表 (冷热分离) 。


* 前端事件通过 `/log/event` 上报，后端通过 `BackgroundTasks` 异步写入。
* 
`server_auto_save`: 生成结果确认时必须强制入库 。




* 
**Risk Control (风控)**:


* AI 检测到 `UNSAFE` 内容时，必须触发熔断，返回特定状态码，前端跳转心理援助页。



## 6. Known Quirks (已知怪癖/注意事项)

* **MySQL Compatibility**:
* 所有带 `index=True` 或 `unique=True` 的 `String` 字段，在 `models.py` 中必须指定长度 (e.g., `String(64)`)，否则 MySQL 会报错 `CompileError`。



* **WeChat Login**:
* `auth.py` 中的 `credential` 字段在微信登录模式下代表 `code`，需要通过后端换取 `openid`。


* **Startup Sequence**:
* 必须在 `main.py` 的 `lifespan` 中调用 `chat.load_questions_from_json()`，否则问题库为空。

* **Backend Environment**:
* 启动后端时必须使用项目自带的虚拟环境 `backend/.venv`，不要在系统 Python 上额外安装任何依赖。


## 7. Frontend Engineering Guidelines 

**Tech Stack**: UniApp (Vue 3 `<script setup>`) + Vite + Pinia + uView-Plus + SCSS.

### 7.1 Design System & Tokens (设计系统与变量)
> 严禁在组件中写死 (Hardcode) 颜色值、间距或字体大小。必须使用全局 Design Tokens。
- **Colors**: 必须使用 `uni.scss` 中定义的变量，例如 `$u-primary`, `$color-text-main`, `$color-bg-warm`。**绝对禁止**在业务组件中出现 `#FF8F1F` 这样的魔法色值。
- **Typography & Spacing**: 间距必须使用标准倍数 (如 `$spacing-sm`, `$spacing-md`)，字体大小使用 `$font-size-base` 等。
- **Border Radius**: 统一使用 `$border-radius-lg` 等变量，保证全站圆角一致。

### 7.2 Figma to Code & Layout (UI 还原与布局)
> 将 Figma 的 Auto Layout 严格翻译为代码。
- **Responsive Unit**: 优先使用 UniApp 的响应式单位 `rpx` (750rpx = 屏幕宽度)，确保在不同尺寸手机上等比缩放。
- **Flexbox First**: 所有的布局必须优先使用 Flexbox (`display: flex`, `justify-content`, `align-items`, `gap`)。
- **No Absolute Positioning**: 除非是弹窗 (Modal)、悬浮球 (FAB) 或覆盖层 (Overlay)，否则**严禁**使用 `position: absolute` 或固定 `height` 来强行对齐元素。
- **Semantic Tags**: 在 UniApp 中，必须使用 `<view>`, `<text>`, `<image>`，**绝对禁止**使用 HTML 标签 `<div>`, `<span>`, `<img>`，以确保微信小程序兼容性。

### 7.3 Interaction & State Management (交互与边界状态)
> 永远不要只设计“理想路径 (Happy Path)”，必须处理所有的 UI 状态。
- **Interactive States**: 所有可点击的元素（按钮、卡片）必须包含 `hover-class` (UniApp 特性) 或 `:active` 伪类，提供点击时的视觉反馈 (如透明度变 0.8 或背景变暗)。
- **Async Feedback**: 任何发起网络请求的按钮，必须有 `loading` 状态，并且在加载时必须设为 `disabled`，防止用户连点。
- **Empty & Error States**: 任何列表 (List/Waterfall) 在数据为空时，必须渲染一个通用的 `<EmptyState>` 组件；接口请求失败时，要有优雅的错误提示，而不是白屏。

### 7.4 Componentization & Clean Code (组件化与整洁代码)
> 保持代码轻量和高内聚。
- **One Component Per File**: 单个 `.vue` 文件如果超过 300 行，或者内部包含独立的 UI 块（如复杂的聊天气泡），必须抽离为单独的组件放到 `src/components/` 中。
- **Props Definition**: 使用 `defineProps` 时必须写明类型 (Type) 和默认值 (Default)。
- **Data Fetching**: 所有的 API 请求必须写在 `src/api/` 目录下，页面中只允许调用封装好的 API 函数。
