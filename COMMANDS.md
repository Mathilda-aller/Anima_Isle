# Common Commands

## Frontend

### Environment file

小程序和其他非 H5 端不会走 Vite 的 `/api` 代理，必须配置真实后端域名。

```bash
cd /root/Anima_Isle_Root/frontend
cp .env.example .env.local
```

`.env.local` 示例：

```bash
VITE_API_BASE_URL=https://your-api-domain.example.com
```

### Start H5 dev server

```bash
cd /root/Anima_Isle_Root/frontend
npm run dev:h5 -- --host 0.0.0.0 --port 5173
```

说明：

```text
H5 默认走 /api 代理到 http://localhost:8000
所以本地联调 H5 时不需要额外配置 VITE_API_BASE_URL
```

### Start WeChat Mini Program dev

```bash
cd /root/Anima_Isle_Root/frontend
VITE_API_BASE_URL=https://your-api-domain.example.com npm run dev:mp-weixin
```

说明：

```text
1. 小程序端的流式接口走真实 HTTPS 域名，不走 /api 代理
2. 这个域名必须能从微信开发者工具访问到
3. 需要在微信公众平台或开发者工具里配置 request 合法域名
4. 如果你本机后端在 8000 端口，需要再通过 ngrok / frp / cloudflared 之类工具映射成 HTTPS 地址
```

### Typical mini program local-debug flow

```text
1. 本地启动后端： http://127.0.0.1:8000
2. 用隧道工具把本地 8000 映射成公网 HTTPS，例如 https://anima-dev.example.ngrok.app
3. 在 frontend/.env.local 中写入：
   VITE_API_BASE_URL=https://anima-dev.example.ngrok.app
4. 启动小程序开发命令： npm run dev:mp-weixin
5. 在微信开发者工具中确保该 HTTPS 域名已加入 request 合法域名
```

### WeChat mini program end-to-end debug guide

按这个顺序做，最不容易漏步骤：

```text
Step 1. 启动本地后端
- 进入 /root/Anima_Isle_Root/backend
- 执行 ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
- 确认浏览器或 curl 能访问 http://127.0.0.1:8000/

Step 2. 把本地 8000 暴露成 HTTPS 地址
- 任选一种隧道工具：ngrok / cloudflared / frp
- 目标是拿到一个公网 HTTPS 地址，并转发到本地 8000
- 例如：
  ngrok http 8000
  或
  cloudflared tunnel --url http://127.0.0.1:8000

Step 3. 记录你的 HTTPS 域名
- 例如拿到：
  https://anima-dev.ngrok-free.app
- 后面所有小程序请求都要走这个地址

Step 4. 配置前端环境变量
- 进入 /root/Anima_Isle_Root/frontend
- 如果还没有环境文件，先执行：
  cp .env.example .env.local
- 打开 .env.local，写入：
  VITE_API_BASE_URL=https://anima-dev.ngrok-free.app

Step 5. 启动小程序前端
- 在 /root/Anima_Isle_Root/frontend 执行：
  npm run dev:mp-weixin
- 如果你刚改过 .env.local，务必重启这个命令，确保变量生效

Step 6. 在微信开发者工具中导入项目
- 打开微信开发者工具
- 导入 frontend 目录生成的小程序项目
- 使用你的小程序 AppID，或者测试号/体验号环境

Step 7. 配置 request 合法域名
- 在微信公众平台后台，把你的 HTTPS 域名加入 request 合法域名
- 如果只是本地临时联调，也可以先在开发者工具里关闭“校验合法域名”
- 但真机调试或后续提测前，还是建议把合法域名配上

Step 8. 验证普通接口是否通
- 先登录、拉用户信息、开始聊天
- 如果这些普通接口都不通，先不要测流式
- 先检查：
  1. HTTPS 地址是否还有效
  2. .env.local 是否写对
  3. 小程序 dev 命令是否在修改环境变量后重启过

Step 9. 验证流式接口是否通
- 进入生成页，提交第二轮回答
- 预期行为是：
  1. 页面先收到风险事件
  2. 共情文案逐段出现
  3. 随后图片和三行诗完成
- 如果这里直接报错，而不是慢慢出字，优先检查后端是否支持 /chat/reply/stream

Step 10. 如果流式失败，重点排查这 5 件事
- 后端是否已经启动，并且外网 HTTPS 隧道仍在线
- VITE_API_BASE_URL 是否指向最新的 HTTPS 域名
- 微信开发者工具是否放行了 request 合法域名
- 小程序端是否确实走了 /chat/reply/stream，而不是旧 /chat/reply
- 当前环境是否支持 chunk 流返回
```

### Tunnel examples

#### ngrok

```bash
ngrok http 8000
```

拿到类似：

```text
https://anima-dev.ngrok-free.app -> http://localhost:8000
```

#### cloudflared

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

拿到类似：

```text
https://random-name.trycloudflare.com -> http://127.0.0.1:8000
```

### Mini program debug checklist

```text
1. 后端已启动
2. HTTPS 隧道在线
3. .env.local 已配置 VITE_API_BASE_URL
4. npm run dev:mp-weixin 已在改完环境变量后重启
5. 微信开发者工具已放行或配置 request 合法域名
6. 提交第二轮回答时，请求命中 /chat/reply/stream
```

### Type check

```bash
cd /root/Anima_Isle_Root/frontend
npm run type-check
```

### Build H5

```bash
cd /root/Anima_Isle_Root/frontend
npm run build:h5
```

## Backend

### Start API server

必须走项目虚拟环境，不要在系统 Python 上额外安装依赖。

```bash
cd /root/Anima_Isle_Root/backend
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
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

## Useful Checks

### See frontend process

```bash
ps -ef | rg "npm run dev:h5"
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
