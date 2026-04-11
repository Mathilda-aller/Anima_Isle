# Common Commands

本仓库现在是 monorepo：

- `backend/`：FastAPI 后端
- `frontend/`：UniApp 前端

建议所有命令都从仓库根目录执行。

```bash
cd /root/Anima_Isle_Root
```

## Frontend

### Install dependencies

```bash
cd frontend
npm install
```

### Environment file

小程序和其他非 H5 端不会走 Vite 的 `/api` 代理，必须配置真实后端域名。

```bash
cd frontend
cp .env.example .env.local
```

`.env.local` 示例：

```bash
VITE_API_BASE_URL=https://your-api-domain.example.com
```

### Start H5 dev server

```bash
cd frontend
npm run dev:h5 -- --host 0.0.0.0 --port 5173
```

说明：

```text
H5 默认走 /api 代理到 http://localhost:8000
所以本地联调 H5 时不需要额外配置 VITE_API_BASE_URL
```

### Start WeChat Mini Program dev

```bash
cd frontend
VITE_API_BASE_URL=https://your-api-domain.example.com npm run dev:mp-weixin
```

说明：

```text
1. 小程序端的流式接口走真实 HTTPS 域名，不走 /api 代理
2. 这个域名必须能从微信开发者工具访问到
3. 需要在微信公众平台或开发者工具里配置 request 合法域名
4. 如果你本机后端在 8000 端口，需要再通过 ngrok / frp / cloudflared 之类工具映射成 HTTPS 地址
```

### Type check

```bash
cd frontend
npm run type-check
```

### Build H5

```bash
cd frontend
npm run build:h5
```

## Backend

### Create venv

必须使用项目自己的虚拟环境。

```bash
cd backend
python3 -m venv .venv
```

### Install dependencies

```bash
cd backend
./.venv/bin/pip install -r requirements.txt
```

### Start API server

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run migrations

```bash
cd backend
./.venv/bin/alembic upgrade head
```

### Check health

```bash
curl http://127.0.0.1:8000/
```

### Stream endpoint note

```text
/chat/reply/stream 需要登录态、session_id 和请求体，不能直接裸 curl。
流式联调建议优先通过前端生成页验证。
```

## Local Full-Stack Dev

### H5 local debug flow

```text
Step 1. 进入仓库根目录
Step 2. 启动 backend：cd backend && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Step 3. 启动 frontend：cd frontend && npm run dev:h5 -- --host 0.0.0.0 --port 5173
Step 4. 打开 http://localhost:5173
```

### WeChat mini program local debug flow

```text
1. 启动本地后端：http://127.0.0.1:8000
2. 用隧道工具把本地 8000 映射成公网 HTTPS
3. 在 frontend/.env.local 中写入：
   VITE_API_BASE_URL=https://your-tunnel-domain.example.com
4. 启动小程序命令：cd frontend && npm run dev:mp-weixin
5. 在微信开发者工具中确保该 HTTPS 域名已加入 request 合法域名
```

### Tunnel examples

#### ngrok

```bash
ngrok http 8000
```

#### cloudflared

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

## Useful Checks

### See frontend process

```bash
ps -ef | rg "npm run dev:h5|uni"
```

### See backend process

```bash
ps -ef | rg "uvicorn app.main:app"
```

### Stop a running process

先查 PID，再结束：

```bash
kill <PID>
```
