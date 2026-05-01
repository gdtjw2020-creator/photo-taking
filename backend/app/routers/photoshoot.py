from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
import httpx
from typing import Optional, List
from pydantic import BaseModel
import uuid
import os
import shutil
import asyncio
import random
from ..services.r2_service import r2_service
from ..services.ai_service import ai_service
from ..services.supabase_service import supabase_service
from ..services.image_utils import add_ai_watermark, apply_watermark_to_bytes
from ..dependencies import get_user_id, check_service_active
from ..config import CREDITS_PER_PHOTOSHOOT, AI_IMAGE_QUALITY, AI_IMAGE_SIZE
from datetime import datetime

router = APIRouter()

class PhotoshootRequest(BaseModel):
    template_id: Optional[str] = None
    image_url: Optional[str] = None # 改为可选：如果不传则为纯模板生成模式
    reference_image_urls: Optional[List[str]] = None
    image_count: Optional[int] = 1 # 默认为 1 张
    is_face_swap: bool = False     # 显式指定是否换脸
    quality: str = AI_IMAGE_QUALITY      # 读取 .env 中的质量配置 (auto, high, medium, low)
    size: str = AI_IMAGE_SIZE            # 读取 .env 中的尺寸配置

class PhotoshootResponse(BaseModel):
    task_id: str
    status: str
    message: str

class FaceSaveRequest(BaseModel):
    face_url: str
    name: Optional[str] = "未命名面部"

@router.get("/gallery")
async def get_gallery(user_id: str = Depends(get_user_id)):
    """获取用户的生成作品集 (最近 1 个月数据可通过逻辑过滤，目前返回全部)"""
    return supabase_service.get_user_gallery(user_id)

@router.get("/faces")
async def get_faces(user_id: str = Depends(get_user_id)):
    """获取用户保存的人脸档案"""
    return supabase_service.get_user_faces(user_id)

@router.get("/active_task")
async def get_active_task(user_id: str = Depends(get_user_id)):
    """获取用户当前正在进行的活跃任务"""
    return supabase_service.get_latest_active_task(user_id)

@router.post("/faces")
async def save_face(request: FaceSaveRequest, user_id: str = Depends(get_user_id)):
    """保存人脸档案"""
    face = supabase_service.save_user_face(user_id, request.face_url, request.name)
    if not face:
        raise HTTPException(status_code=500, detail="保存失败")
    return face

@router.delete("/faces/{face_id}")
async def delete_face(face_id: str, user_id: str = Depends(get_user_id)):
    """删除人脸档案"""
    success = supabase_service.delete_user_face(user_id, face_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"status": "success"}

@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
    active: bool = Depends(check_service_active)
):
    """上传照片到 R2"""
    temp_dir = "temp_uploads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    file_ext = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 上传到 R2
    today = datetime.now().strftime("%Y%m%d")
    object_name = f"photoshoots/inputs/{today}/{user_id}/{temp_filename}"
    r2_url = r2_service.upload_file(temp_path, object_name)
    
    os.remove(temp_path)
    
    if not r2_url:
        raise HTTPException(status_code=500, detail="文件上传失败")
        
    return {"url": r2_url}

@router.post("/generate", response_model=PhotoshootResponse)
async def generate_photoshoot(
    request: PhotoshootRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    active: bool = Depends(check_service_active)
):
    """开启约拍任务"""
    # 0. 确定图片生成数量
    if request.reference_image_urls:
        request.image_count = len(request.reference_image_urls)
        # 限制最多 5 张
        if request.image_count > 5:
            raise HTTPException(status_code=400, detail="最多只能上传 5 张参考图")
            
    # 1. 余额检查 (提前拦截，防止浪费 AI 资源)
    profile = supabase_service.get_user_profile(user_id)
    current_credits = profile.get("credits", 0)
    required_credits = request.image_count * CREDITS_PER_PHOTOSHOOT
    
    if current_credits < required_credits:
        raise HTTPException(
            status_code=402, 
            detail=f"余额不足。本次约拍预计消耗 {required_credits} 积分，您当前剩余 {current_credits} 积分。请点击个人中心充值。"
        )

    task_id = str(uuid.uuid4())
    
    # 2. 创建数据库记录
    success = supabase_service.create_task(
        task_id=task_id,
        user_id=user_id,
        template_id=request.template_id if request.template_id and len(request.template_id) > 10 else None,
        input_url=request.image_url # 此时可以是 None
    )
    
    if not success:
        print(f"Warning: Failed to create task record for {task_id}")

    # 3. 确定 Prompts 或 Reference URLs
    selected_prompts = []
    if request.reference_image_urls:
        # 如果有参考图，优化提示词以更好地触发底层多图换脸
        selected_prompts = ["使用图片1(image_1)的人脸，保持图片2(image_0)的动作、姿势、服装和背景完全不变。"] * request.image_count
    else:
        # 否则走旧的模板逻辑
        templates = supabase_service.get_all_templates()
        target_template = next((t for t in templates if str(t["id"]) == request.template_id), None)
        
        if not target_template:
            base_prompts = ["唯美写真，人像，高清质感"]
        else:
            base_prompts = target_template.get("prompts", ["唯美写真，人像，高清质感"])

        count = min(max(request.image_count, 1), len(base_prompts))
        selected_prompts = random.sample(base_prompts, count)
    
    # 异步执行生成逻辑
    background_tasks.add_task(
        process_photoshoot_task,
        task_id,
        user_id,
        request.image_url,
        selected_prompts,
        request.reference_image_urls,
        request.quality,
        request.size
    )
    
    return PhotoshootResponse(
        task_id=task_id,
        status="pending",
        message="任务已提交，正在排队中"
    )

@router.get("/templates")
async def get_templates():
    """获取所有可用模板 (优先从数据库获取)"""
    db_templates = supabase_service.get_all_templates()
    if db_templates:
        # 格式化数据库数据以适配前端
        return [
            {
                "id": str(t["id"]),
                "name": t["name"],
                "preview": t["preview_url"]
            } for t in db_templates
        ]
    
    # 兜底本地数据
    return [
        {"id": "1", "name": "影楼婚纱", "preview": "https://images.unsplash.com/photo-1594553813271-6562777d630a?q=80&w=300&h=400&auto=format&fit=crop"},
        {"id": "2", "name": "旗袍韵味", "preview": "https://images.unsplash.com/photo-1578301978018-3005759f48f7?q=80&w=300&h=400&auto=format&fit=crop"},
        {"id": "3", "name": "职场精英", "preview": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=300&h=400&auto=format&fit=crop"},
        {"id": "4", "name": "海边落日", "preview": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=300&h=400&auto=format&fit=crop"},
        {"id": "5", "name": "赛博朋克", "preview": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=300&h=400&auto=format&fit=crop"}
    ]

@router.get("/task_status")
async def get_task_status(task_id: str):
    """查询任务状态 (改为查询参数形式)"""
    task = supabase_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    # 如果任务仍在处理中，基于创建时间做“僵尸任务”兜底检测 (防止后端轮询死锁)
    if task.get("status") == "processing" and "created_at" in task:
        from datetime import datetime, timezone
        try:
            created_at_str = task["created_at"]
            if created_at_str == "now":
                # 如果是还没来得及更新的缓存数据，先跳过检测
                return task
                
            created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            elapsed_seconds = (now - created_time).total_seconds()
            
            # 如果超过 900 秒 (15分钟) 仍然在 processing，判定为底层卡死，强制干掉
            if elapsed_seconds > 900:
                supabase_service.update_task_status(task_id, "failed", error_message="生成任务在底层卡死或严重超时，已被系统安全熔断")
                task["status"] = "failed"
                task["error_message"] = "生成任务在底层卡死或严重超时，已被系统安全熔断"
        except Exception as e:
            print(f"解析时间检测僵尸任务失败: {e}, 原始时间字符串: {task.get('created_at')}")
            
    return task

async def process_photoshoot_task(task_id: str, user_id: str, input_url: Optional[str], prompts: List[str], reference_urls: Optional[List[str]] = None, quality: str = "auto", size: str = "auto"):
    """异步处理约拍任务 (支持逐张生成、实时扣费及 900s 硬超时)"""
    # 1. 更新状态为处理中
    supabase_service.update_task_status(task_id, "processing")
    
    success_count = 0
    last_error_msg = "所有图片生成均失败"
    
    try:
        # 设置整个任务的最大允许时间为 900 秒
        async def run_prompts():
            nonlocal success_count, last_error_msg
            for i, p in enumerate(prompts):
                try:
                    ref_url = reference_urls[i] if reference_urls and i < len(reference_urls) else None
                    print(f"[DEBUG] Generating image {i+1}/{len(prompts)} for task {task_id} (input_url={'present' if input_url else 'absent'})")
                    results = await ai_service.generate_images(input_url, p, ref_url, size, quality)
                    
                    if results and len(results) > 0:
                        external_url = results[0]
                        # 重点：转存到 R2 以持久化，避免第三方保存时间不可控
                        print(f"[DEBUG] Transferring result to R2 (length: {len(external_url)})")
                        final_url = external_url
                        try:
                            # 处理 Base64
                            if external_url.startswith("data:image"):
                                import base64
                                header, encoded = external_url.split(",", 1)
                                content = base64.b64decode(encoded)
                                watermarked_content = apply_watermark_to_bytes(content)
                                
                                today = datetime.now().strftime("%Y%m%d")
                                filename = f"{uuid.uuid4()}.png"
                                object_name = f"photoshoots/outputs/{today}/{user_id}/{filename}"
                                uploaded_url = r2_service.upload_content(watermarked_content, object_name)
                                if uploaded_url:
                                    final_url = uploaded_url
                                    print(f"✅ [DEBUG] Successfully stored Base64 to R2: {final_url}")
                            # 处理 URL
                            else:
                                async with httpx.AsyncClient() as client:
                                    resp = await client.get(external_url, timeout=60.0)
                                    if resp.status_code == 200:
                                        # 添加半透明水印 (合规要求，20% 透明度)
                                        watermarked_content = apply_watermark_to_bytes(resp.content)
                                        
                                        # 生成唯一文件名并保存到 R2
                                        today = datetime.now().strftime("%Y%m%d")
                                        filename = f"{uuid.uuid4()}.png"
                                        object_name = f"photoshoots/outputs/{today}/{user_id}/{filename}"
                                        uploaded_url = r2_service.upload_content(watermarked_content, object_name)
                                        if uploaded_url:
                                            final_url = uploaded_url
                                            print(f"✅ [DEBUG] Successfully stored URL to R2: {final_url}")
                        except Exception as e:
                            print(f"‼️ [ERROR] Failed to transfer to R2: {e}")

                        supabase_service.append_task_output(task_id, final_url)
                        supabase_service.deduct_credits(user_id, CREDITS_PER_PHOTOSHOOT, f"约拍生成: 任务 {task_id[:8]} 第 {i+1} 张")
                        success_count += 1
                    else:
                        last_error_msg = "生成结果为空"
                except Exception as e:
                    print(f"[ERROR] Task {task_id} step {i+1} failed: {e}")
                    last_error_msg = str(e)
                    continue
        
        await asyncio.wait_for(run_prompts(), timeout=900)

    except asyncio.TimeoutError:
        print(f"[TIMEOUT] Task {task_id} exceeded 900s limit.")
        supabase_service.update_task_status(task_id, "failed", error_message="生成任务超时 (900s)")
        return
    except Exception as e:
        print(f"[ERROR] Task {task_id} process failed: {e}")
        supabase_service.update_task_status(task_id, "failed", error_message=str(e))
        return

    # 4. 更新最终完成状态
    if success_count > 0:
        supabase_service.update_task_status(task_id, "completed")
    else:
        supabase_service.update_task_status(task_id, "failed", error_message=last_error_msg)

@router.get("/download")
async def proxy_download(url: str):
    """代理下载图片，解决前端跨域限制导致的下载失败问题"""
    async def stream_image():
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        raise HTTPException(status_code=response.status_code, detail="无法获取图片")
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception as e:
                print(f"Proxy download error: {str(e)}")
                raise HTTPException(status_code=500, detail="下载失败")

    # 简单提取或生成文件名
    filename = url.split("/")[-1].split("?")[0]
    if not filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        filename = f"photoshoot_{uuid.uuid4().hex[:8]}.png"

    return StreamingResponse(
        stream_image(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
