"""AI女神约拍神器 - FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .routers import photoshoot, user, billing

app = FastAPI(
    title="AI女神约拍神器",
    description="AI女神约拍神器 - H5智能影楼API",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册路由
app.include_router(photoshoot.router, prefix="/api/photoshoot", tags=["约拍"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(billing.router, prefix="/api/billing", tags=["计费"])

@app.get("/")
async def root():
    return {"message": "AI女神约拍神器 API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
