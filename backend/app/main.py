import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 导入所有路由
from app.routers import auth, users, chat, tickets, square, tracking
from app.utils.sqlite_compat import ensure_sqlite_dev_schema_compatibility

# 1. 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 【启动时执行】
    print("🚀 Server starting up...")
    ensure_sqlite_dev_schema_compatibility()
    
    #  加载问题库 (调用 chat 模块的方法)
    chat.load_questions_from_json()
    
    yield # 分隔线：上面是启动，下面是关闭
    
    # 【关闭时执行】
    print("🛑 Server shutting down...")

# 2. 初始化 App
app = FastAPI(
    title="Anima Isle API",
    version="1.0.0",
    lifespan=lifespan 
)

# 3. CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 挂载路由
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["Chat Core"])
app.include_router(tickets.router, prefix="/tickets", tags=["Memory Lane"]) 
app.include_router(square.router, prefix="/square", tags=["Empathy Map"])
app.include_router(tracking.router, prefix="", tags=["System"])

static_image_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "image_library")
if os.path.isdir(static_image_dir):
    app.mount("/static/images", StaticFiles(directory=static_image_dir), name="static-images")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Anima Isle Backend"}
