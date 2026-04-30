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

## Local Regression Checklist

这部分是给“本地突然开始报错、需要快速排查”的直接命令清单。

建议顺序：

```text
1. 先确认后端是不是带着代理环境启动
2. 再用无代理环境重启本地 backend
3. 跑 backend 回归测试
4. 跑 frontend 单测和 type-check
5. 最后看 backend 实时日志，确认是 AI 连接问题、Zilliz 问题，还是前端展示问题
```

### Check whether the running backend still has proxy env

```bash
ps -ef | rg 'uvicorn app.main:app --reload|uvicorn app.main:app'
```

把上面查到的 PID 代入：

```bash
tr '\0' '\n' < /proc/<PID>/environ | rg -i '^(http_proxy|https_proxy|all_proxy|HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|no_proxy|NO_PROXY)='
```

### Restart backend without proxy env

先停掉旧进程：

```bash
pkill -f 'uvicorn app.main:app --reload' || true
pkill -f 'uvicorn app.main:app' || true
```

再用项目虚拟环境、无代理方式启动：

```bash
cd backend
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy ./.venv/bin/uvicorn app.main:app --reload
```

### Run backend regression tests

这组命令会覆盖这轮已经补上的聊天生成、AI fallback、Zilliz 恢复和候选图稳定性测试：

```bash
cd backend
./.venv/bin/pytest tests/test_ai_engine_island.py tests/test_chat_island_flow.py tests/test_search_engine_island.py
```

### Run frontend regression tests

这组命令会覆盖 chat store、stream cancel、生成页状态流转、reroll 纯逻辑测试：

```bash
cd frontend
npm run test:unit
```

### Run frontend type check

```bash
cd frontend
npm run type-check
```

### Tail backend logs while reproducing a bug

如果 backend 是前台启动的，直接看当前终端输出。

如果是后台启动并把日志写到文件，可以看：

```bash
tail -f /tmp/anima_backend.log
```

重点看这些关键词：

```text
AI / DashScope:
- ai.request.connection_error
- empathy.stream.failed
- emotion_route
- suggested_tags

Risk:
- risk.model.api_failed
- risk.result

Zilliz / candidate images:
- Failed to connect to Zilliz
- vector_search
- is_fallback
```

### Probe Zilliz client directly

快速判断本地当前能不能连上向量库：

```bash
cd backend
./.venv/bin/python - <<'PY'
from app.utils import search_engine
client = search_engine._get_client()
print("CLIENT_OK", client is not None)
PY
```

### Probe embedding + candidate search directly

快速判断“AI embedding 正常，但候选图是不是还在 fallback”：

```bash
cd backend
./.venv/bin/python - <<'PY'
import asyncio
from app.utils import ai_engine, search_engine

async def main():
    text = "今天压力很大，感觉快要被ddl压垮了"
    vec = await ai_engine.get_embedding(text, trace_id="probe")
    print("EMBED_LEN", len(vec))
    result = search_engine.search_island_candidates(vec, island_target="SNOW", intensity="HIGH", top_k=3)
    for item in result:
        print({
            "image_id": item.get("image_id"),
            "image_url": item.get("image_url"),
            "distance": item.get("distance"),
            "is_fallback": item.get("is_fallback"),
        })

asyncio.run(main())
PY
```
