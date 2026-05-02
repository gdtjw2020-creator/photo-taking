"""AI女神约拍神器 - FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# 注册路由 (API 必须在静态文件之前注册)
app.include_router(photoshoot.router, prefix="/api/photoshoot", tags=["约拍"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(billing.router, prefix="/api/billing", tags=["计费"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 静态文件服务配置
# 这里的 static_dir 指向 backend/static 目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 优先处理 assets 目录
assets_dir = os.path.join(static_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{rest_of_path:path}")
async def serve_frontend(rest_of_path: str):
    """
    SPA 路由支持：
    1. 如果请求的是文件（如 favicon.ico），则尝试返回该文件
    2. 否则统一返回 index.html，由前端 Vue Router 处理路由
    """
    # 排除 API 请求
    if rest_of_path.startswith("api/"):
        return {"detail": "Not Found"}
        
    file_path = os.path.join(static_dir, rest_of_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "AI女神约拍神器 API (Static files not found)", "version": "0.1.0"}
