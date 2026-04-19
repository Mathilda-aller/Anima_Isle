# linguisle.com

# 言屿 Anima Isle

一个面向情绪陪伴场景的 AI 应用。用户通过两轮倾诉或语音输入表达当下情绪，系统会结合大语言模型、语音识别、向量检索与内容生成能力，将情绪转译为“疗愈图像 + 三行诗 + 情绪船票”，并支持发布到共感地图进行轻社交互动。

## 项目状态

- 当前阶段：MVP 开发中
- 项目目标：打通“情绪倾诉 -> 内容生成 -> 船票沉淀 -> 社交发布”的完整闭环
- 部署地址：`https://linguisle.com`

## 核心能力

- AI 情绪理解：对用户输入进行情绪分类，映射到预设岛屿与强度等级
- 共情回复生成：生成温和、克制、适合产品语气的陪伴式文本
- 视觉船票生成：结合向量检索召回的图片素材与用户情绪，生成三行诗船票
- 语音输入支持：将语音输入转为文本后进入统一生成链路
- 共感地图社交：用户可将船票发布到对应岛屿，并进行查看、标签浏览与 hug 互动
- 工程兜底机制：包含风险识别、超时控制、重试、静态兜底与日志埋点

## 技术栈

### 后端

- Python 3.9+
- FastAPI
- SQLAlchemy
- Pydantic v2
- Alembic
- MySQL 8.0
- Zilliz Cloud / Milvus

### AI 能力

- DashScope
- Qwen 系列模型
- `text-embedding-v4`
- ASR 模型：`qwen3-asr-flash`

### 前端

- UniApp
- Vue 3
- Vite
- Pinia
- uView-Plus
- SCSS

## 系统架构概览

项目整体由前端应用、FastAPI 后端、关系型数据库、向量数据库和外部 AI 服务组成：

1. 前端负责用户登录、对话、船票展示、广场与地图交互
2. 后端负责认证鉴权、会话编排、AI 调度、数据持久化和业务接口
3. MySQL 用于存储用户、聊天会话、船票资产、AI 日志和埋点数据
4. Zilliz Cloud 用于存储图片素材语义向量并执行相似度检索
5. DashScope 提供情绪分类、共情回复、标签生成、三行诗生成、语音转写与向量化能力

## 生成链路

一次完整的内容生成流程如下：

1. 用户发起会话，后端返回首个问题
2. 用户完成两轮文本或语音倾诉
3. 后端进行风险识别，拦截高风险输入
4. 后端并行执行情绪分类、Embedding 生成、推荐标签生成
5. 根据情绪分类结果，在 Zilliz Cloud 中召回候选图片
6. 使用用户输入和图片描述生成三行诗
7. 将最终结果落库为船票资产，并返回给前端展示
8. 用户可选择发布到岛屿广场，进入社交互动链路

## 目录结构

```text
.
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # 路由层：auth/chat/tickets/square/users/tracking
│   │   ├── utils/           # AI、检索、安全、邮件、微信等工具模块
│   │   ├── models.py        # SQLAlchemy 数据模型
│   │   ├── schemas.py       # Pydantic 请求/响应模型
│   │   ├── crud.py          # 数据访问逻辑
│   │   └── main.py          # 应用入口
│   ├── data/                # 图片素材与元数据
│   ├── migrations/          # Alembic 迁移
│   ├── scripts/             # 初始化与数据导入脚本
│   └── tests/               # 后端测试
├── frontend/                # UniApp 前端
├── docker-compose.yml
└── README.md
```

## 主要数据实体

- `User`：用户账户、风格偏好、登录信息
- `ChatSession`：两轮倾诉的会话状态与回答内容
- `Ticket`：核心生成资产，包含图片、三行诗、情绪岛屿、标签等信息
- `AIChatLog`：记录 AI 输入输出、风险标记与耗时
- `TrackingEvent`：前端行为埋点

## 本地开发

### 1. 后端

项目后端必须使用仓库内虚拟环境 `backend/.venv`。

```bash
cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

后端默认会读取 `.env` 中的配置，请先参考 [backend/.env.example](/root/Anima_Isle_Root/backend/.env.example) 补齐环境变量。

### 2. 前端

```bash
cd frontend
npm install
npm run dev:h5
```

前端环境变量请参考 [frontend/.env.example](/root/Anima_Isle_Root/frontend/.env.example)。

## 向量库初始化

首次使用前，需要先创建 Zilliz 集合并导入图片素材元数据：

```bash
cd backend
.venv/bin/python scripts/init_zilliz.py
.venv/bin/python scripts/ingest_data.py
```

其中 `ingest_data.py` 会读取 `backend/data/image_metadata.xlsx`，为素材生成向量并写入 Zilliz Cloud。

## 测试

后端测试：

```bash
cd backend
.venv/bin/pytest
```

前端类型检查与测试：

```bash
cd frontend
npm run type-check
npm run test
```

## 已实现的工程特性

- JWT 鉴权与邮箱注册登录
- 微信登录接入
- 找回密码与验证码发送流程
- 两轮对话状态机
- SSE 流式回复接口
- AI 风险识别与高风险拦截
- 向量检索三段兜底策略
- 每日生成次数限制
- 埋点日志与 AI 耗时日志

## 适用场景

- AI 情绪陪伴应用
- LLM + 向量检索混合生成系统
- 情绪内容可视化产品
- AI 驱动的轻社交产品原型

## License

当前仓库未单独声明开源许可证。如需开源，请补充对应 License 文件。
