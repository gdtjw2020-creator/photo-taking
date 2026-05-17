from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
import httpx
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
import os
import shutil
import asyncio
import random
import traceback
from ..services.r2_service import r2_service
from ..services.ai_service import ai_service
from ..services.supabase_service import supabase_service
from ..services.image_utils import add_ai_watermark, apply_watermark_to_bytes
from ..dependencies import get_user_id, get_admin_user, check_service_active
from ..config import CREDITS_PER_PHOTOSHOOT, AI_IMAGE_QUALITY, AI_IMAGE_SIZE
from ..data.old_photo_styles import get_old_photo_style, list_old_photo_styles
from datetime import datetime

router = APIRouter()

@router.get("/config")
async def get_config():
    """获取前端公用配置，实现前后端环境变量统一"""
    return {
        "credits_per_photoshoot": CREDITS_PER_PHOTOSHOOT,
        "ai_image_quality": AI_IMAGE_QUALITY,
        "ai_image_size": AI_IMAGE_SIZE
    }

class PhotoshootRequest(BaseModel):
    module_type: Optional[str] = None  # classic_style, darkroom_random, reference_shoot
    style_id: Optional[str] = None
    prompt_mode: Optional[str] = None  # similar, strict, creative
    template_id: Optional[str] = None
    image_url: Optional[str] = None # 改为可选：如果不传则为纯模板生成模式
    reference_image_urls: Optional[List[str]] = None
    image_count: Optional[int] = 1 # 默认为 1 张
    is_face_swap: bool = False     # 显式指定是否换脸
    quality: str = AI_IMAGE_QUALITY      # 读取 .env 中的质量配置 (auto, high, medium, low)
    size: str = AI_IMAGE_SIZE            # 读取 .env 中的尺寸配置
    watermark: bool = True               # 是否添加"AI生成"水印，默认开启
    framing: Optional[str] = None        # 构图选择 (portrait, half_body, upper_body, etc.)

class PhotoshootResponse(BaseModel):
    task_id: str
    status: str
    message: str

class FaceSaveRequest(BaseModel):
    face_url: str
    name: Optional[str] = "未命名形象"

VALID_MODULE_TYPES = {"classic_style", "darkroom_random", "reference_shoot"}
REFERENCE_PROMPT_MODES = {"similar", "strict", "creative"}
LEGACY_FACE_SWAP_PROMPT = (
    "The first image is the target scene with a specific pose, clothing, and background. "
    "The second image is a portrait showing the person whose face should be used. "
    "Seamlessly replace the face in the first image with the face from the second image. "
    "Keep the exact pose, body proportions, clothing, hairstyle, background, and lighting "
    "from the first image completely unchanged. The face replacement must look natural with "
    "correct skin tone blending, consistent lighting direction, and proper proportional scaling. "
    "The result should be photorealistic, cinematic quality, 4K."
)

# 景别枚举到提示词关键词的映射
FRAMING_KEYWORDS = {
    "portrait": "Close-up portrait, high face detail",
    "upper_body": "Upper body shot",
    "half_body": "Half-body shot",
    "three_quarter": "Three-quarter view portrait",
    "full_body": "Full body shot, head to toe",
    "wide": "Wide shot, environmental portrait"
}


def _safe_image_count(value: Optional[int], default: int = 1, max_count: int = 5) -> int:
    count = value if isinstance(value, int) else default
    return min(max(count, 1), max_count)


def _build_reference_prompt(prompt_mode: Optional[str]) -> str:
    mode = prompt_mode if prompt_mode in REFERENCE_PROMPT_MODES else "similar"
    base = (
        "The first uploaded image is the target reference for composition, pose, "
        "clothing style, lighting, background, and visual mood. The second uploaded "
        "image is the identity reference. Create a realistic photo of the same "
        "person from the identity reference. Preserve the person's facial identity, "
        "natural features, age impression, and expression. Avoid distortion, cartoon "
        "style, illustration style, identity drift, extra people, and text artifacts."
    )
    mode_rules = {
        "strict": (
            "Match the target reference as closely as possible: composition, pose, "
            "body orientation, clothing silhouette, lighting direction, and background "
            "should stay very close to the first image while keeping the second image's identity."
        ),
        "similar": (
            "Follow the target reference's overall style, atmosphere, lighting, and composition, "
            "but allow natural adjustments so the final portrait looks coherent and realistic."
        ),
        "creative": (
            "Use the target reference as inspiration rather than a strict copy. Keep the same "
            "mood and era, but freely adapt pose, framing, clothing details, and background for "
            "a polished realistic portrait."
        ),
    }
    return f"{base} {mode_rules[mode]} Photorealistic, cinematic quality, natural skin texture, 4K."
def _select_mvp_prompts(request: PhotoshootRequest) -> Optional[Dict[str, Any]]:
    """Return prompt selection data for MVP modes, or None for legacy flow."""
    module_type = request.module_type
    if not module_type:
        return None

    if module_type not in VALID_MODULE_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的生成模式: {module_type}")

    if module_type in {"classic_style", "darkroom_random"} and not request.image_url:
        raise HTTPException(status_code=400, detail="请先上传人脸照片")

    if module_type == "classic_style":
        if not request.style_id:
            raise HTTPException(status_code=400, detail="请先选择年代风格")

        style = get_old_photo_style(request.style_id)
        if not style:
            raise HTTPException(status_code=400, detail=f"未知年代风格: {request.style_id}")

        # 确定最终景别：用户手动选择优先，否则使用风格默认值
        final_framing = request.framing or style.get("default_framing")
        framing_prefix = f"{FRAMING_KEYWORDS[final_framing]}, " if final_framing in FRAMING_KEYWORDS else ""

        prompts = style.get("prompts") or []
        count = min(_safe_image_count(request.image_count, style.get("recommended_count", 1)), len(prompts))
        selected_raw_prompts = random.sample(prompts, count)
        
        # 将景别前缀拼接到原始提示词中
        selected_prompts = [f"{framing_prefix}{p}" for p in selected_raw_prompts]

        return {
            "image_count": count,
            "selected_prompts": selected_prompts,
            "style_id": style["id"],
            "metadata": {
                "module_name": "时代艺术照",
                "style_ids": [style["id"]],
                "style_names": [style["name"]],
                "framing": final_framing,
                "selected_prompts": selected_prompts
            },
        }

    if module_type == "darkroom_random":
        styles = list_old_photo_styles()
        requested_count = request.image_count if request.image_count in (3, 6, 9) else 3
        count = min(requested_count, len(styles))
        selected_styles = random.sample(styles, count)
        
        # 盲盒模式：每张图使用各自风格的默认景别
        selected_prompts = []
        for style in selected_styles:
            raw_p = random.choice(style["prompts"])
            final_framing = style.get("default_framing")
            prefix = f"{FRAMING_KEYWORDS[final_framing]}, " if final_framing in FRAMING_KEYWORDS else ""
            selected_prompts.append(f"{prefix}{raw_p}")

        return {
            "image_count": count,
            "selected_prompts": selected_prompts,
            "style_id": None,
            "metadata": {
                "module_name": "暗房盲盒",
                "requested_count": requested_count,
                "actual_count": count,
                "style_ids": [style["id"] for style in selected_styles],
                "style_names": [style["name"] for style in selected_styles],
                "selected_prompts": selected_prompts
            },
        }

    if module_type == "reference_shoot":
        if not request.image_url:
            raise HTTPException(status_code=400, detail="请先上传人脸照片")
        if not request.reference_image_urls:
            raise HTTPException(status_code=400, detail="请先上传参考图")

        refs = request.reference_image_urls[:5]
        mode = request.prompt_mode if request.prompt_mode in REFERENCE_PROMPT_MODES else "similar"
        
        # 照着样子拍模式，不再受 framing 提示词干扰，完全尊重参考图构图
        prompt = _build_reference_prompt(mode)
        
        return {
            "image_count": len(refs),
            "selected_prompts": [prompt] * len(refs),
            "reference_image_urls": refs,
            "style_id": None,
            "metadata": {
                "module_name": "照着样子拍",
                "prompt_mode": mode,
                "reference_count": len(refs),
                "selected_prompts": [prompt] * len(refs)
            },
        }

    return None

@router.get("/gallery")
async def get_gallery(user_id: str = Depends(get_user_id)):
    """获取用户的生成作品集 (最近 1 个月数据可通过逻辑过滤，目前返回全部)"""
    return supabase_service.get_user_gallery(user_id)

@router.get("/faces")
async def get_faces(user_id: str = Depends(get_user_id)):
    """获取用户保存的形象档案"""
    return supabase_service.get_user_faces(user_id)

@router.get("/active_task")
async def get_active_task(user_id: str = Depends(get_user_id)):
    """获取用户当前正在进行的活跃任务"""
    return supabase_service.get_latest_active_task(user_id)

class GalleryDeleteRequest(BaseModel):
    url: str

@router.delete("/gallery/{task_id}")
async def delete_gallery_item(task_id: str, request: GalleryDeleteRequest, user_id: str = Depends(get_user_id)):
    """从作品集中删除一张图片"""
    success = supabase_service.remove_task_output(user_id, task_id, request.url)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"status": "success"}

@router.post("/faces")
async def save_face(request: FaceSaveRequest, user_id: str = Depends(get_user_id)):
    """保存形象档案"""
    face = supabase_service.save_user_face(user_id, request.face_url, request.name)
    if not face:
        raise HTTPException(status_code=500, detail="保存失败")
    return face

@router.delete("/faces/{face_id}")
async def delete_face(face_id: str, user_id: str = Depends(get_user_id)):
    """删除形象档案"""
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
    print(f"[UPLOAD] Received file: filename={file.filename}, content_type={file.content_type}, user_id={user_id}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件或文件名为空")

    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        file_ext = ".jpg"
    if file_ext.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")

    temp_dir = "temp_uploads"
    temp_path = None

    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)

        temp_filename = f"{uuid.uuid4()}{file_ext}"
        temp_path = os.path.join(temp_dir, temp_filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(temp_path)
        print(f"[UPLOAD] Saved temp file: {temp_path} ({file_size} bytes)")

        if file_size == 0:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        # 上传到 R2
        today = datetime.now().strftime("%Y%m%d")
        object_name = f"photoshoots/inputs/{today}/{user_id}/{temp_filename}"
        print(f"[UPLOAD] Uploading to R2: {object_name}")
        r2_url = r2_service.upload_file(temp_path, object_name)

        if not r2_url:
            raise Exception("R2 upload returned None — check R2 credentials, bucket, or network")

        print(f"[UPLOAD] Success: {r2_url}")
        return {"url": r2_url}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传失败: {type(e).__name__} — {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/generate", response_model=PhotoshootResponse)
async def generate_photoshoot(
    request: PhotoshootRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    active: bool = Depends(check_service_active)
):
    """开启约拍任务"""
    # 0. 确定 MVP 模式 prompt，旧请求保持原逻辑
    mvp_selection = _select_mvp_prompts(request)
    task_metadata = {}
    selected_prompts = []
    reference_urls = request.reference_image_urls
    selected_style_id = request.style_id

    if mvp_selection:
        request.image_count = mvp_selection["image_count"]
        selected_prompts = mvp_selection["selected_prompts"]
        reference_urls = mvp_selection.get("reference_image_urls", request.reference_image_urls)
        selected_style_id = mvp_selection.get("style_id") or request.style_id
        task_metadata = mvp_selection.get("metadata", {})

    # 1. 确定图片生成数量
    if not mvp_selection and request.reference_image_urls:
        request.image_count = len(request.reference_image_urls)
        # 限制最多 5 张
        if request.image_count > 5:
            raise HTTPException(status_code=400, detail="最多只能上传 5 张参考图")
            
    # 2. 余额检查 (提前拦截，防止浪费 AI 资源)
    profile = supabase_service.get_user_profile(user_id)
    current_credits = profile.get("credits", 0)
    required_credits = request.image_count * CREDITS_PER_PHOTOSHOOT
    
    if current_credits < required_credits:
        raise HTTPException(
            status_code=402, 
            detail=f"余额不足。本次约拍预计消耗 {required_credits} 积分，您当前剩余 {current_credits} 积分。请点击个人中心充值。"
        )

    # 4. 确定 Prompts 或 Reference URLs (调整至创建记录前，用于记录提示词到 task_metadata)
    if selected_prompts:
        pass
    elif request.reference_image_urls:
        # 如果有参考图，优化提示词以更好地触发底层多图换脸
        selected_prompts = [LEGACY_FACE_SWAP_PROMPT] * request.image_count
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

    # 将最终生成的提示词保存到任务元数据中，便于前端/调试排查
    task_metadata["selected_prompts"] = selected_prompts

    task_id = str(uuid.uuid4())
    
    # 3. 创建数据库记录
    success = supabase_service.create_task(
        task_id=task_id,
        user_id=user_id,
        template_id=request.template_id if request.template_id and len(request.template_id) > 10 else None,
        input_url=request.image_url, # 此时可以是 None
        module_type=request.module_type,
        style_id=selected_style_id,
        metadata=task_metadata
    )
    
    if not success:
        print(f"Warning: Failed to create task record for {task_id}")
    
    # 异步执行生成逻辑
    background_tasks.add_task(
        process_photoshoot_task,
        task_id,
        user_id,
        request.image_url,
        selected_prompts,
        reference_urls,
        request.quality,
        request.size,
        request.watermark
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

@router.get("/old_photo_styles")
async def get_old_photo_styles():
    """获取唐师傅老照片风格列表，优先从数据库获取封面图覆盖。"""
    hardcoded_styles = list_old_photo_styles()
    
    # 尝试从数据库获取覆盖配置 (preview_url)
    overrides = {}
    try:
        overrides = supabase_service.get_style_overrides()
    except Exception as e:
        print(f"Failed to fetch style overrides: {e}")
        
    return [
        {
            "id": style["id"],
            "name": style["name"],
            "description": style["description"],
            "preview_url": overrides.get(style["id"], {}).get("preview_url") or style["preview_url"],
            "tags": style["tags"],
            "recommended_count": style["recommended_count"],
            "default_framing": style.get("default_framing"),
        }
        for style in hardcoded_styles
    ]

@router.post("/styles/{style_id}/cover")
async def update_style_cover(
    style_id: str,
    file: UploadFile = File(...),
    admin_id: str = Depends(get_admin_user)
):
    """管理员更新风格封面图"""
    # 1. 上传图片到 R2
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"style_cover_{style_id}_{uuid.uuid4().hex[:8]}{file_ext}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        object_name = f"photoshoots/styles/{style_id}/{os.path.basename(temp_path)}"
        r2_url = r2_service.upload_file(temp_path, object_name)
        
        if not r2_url:
            raise HTTPException(status_code=500, detail="图片上传 R2 失败")
            
        # 2. 更新数据库
        success = supabase_service.update_style_preview(style_id, r2_url)
        if not success:
            raise HTTPException(status_code=500, detail="更新数据库记录失败")
            
        return {"id": style_id, "preview_url": r2_url}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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

async def process_photoshoot_task(task_id: str, user_id: str, input_url: Optional[str], prompts: List[str], reference_urls: Optional[List[str]] = None, quality: str = "auto", size: str = "auto", watermark: bool = True):
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
                    print(f"--- [AI GENERATION START] ---")
                    print(f"Task ID: {task_id}")
                    print(f"Image Index: {i+1}/{len(prompts)}")
                    print(f"Final Prompt: {p}")
                    print(f"Input URL: {input_url}")
                    print(f"Reference URL: {ref_url}")
                    print(f"--- [AI GENERATION CALLING] ---")
                    
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
                                watermarked_content = apply_watermark_to_bytes(content) if watermark else content
                                
                                today = datetime.now().strftime("%Y%m%d")
                                filename = f"{uuid.uuid4()}.png"
                                object_name = f"photoshoots/outputs/{today}/{user_id}/{filename}"
                                uploaded_url = r2_service.upload_content(watermarked_content, object_name)
                                if uploaded_url:
                                    final_url = uploaded_url
                                    print(f"✅ [DEBUG] Successfully stored Base64 to R2: {final_url}")
                            # 处理 URL
                            else:
                                async with ai_service.get_client_by_url(external_url, timeout=60.0) as client:
                                    resp = await client.get(external_url)
                                    if resp.status_code == 200:
                                        watermarked_content = apply_watermark_to_bytes(resp.content) if watermark else resp.content
                                        
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
        async with ai_service.get_client_by_url(url, timeout=30.0) as client:
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

    # 根据文件扩展名确定媒体类型，帮助移动端更好地识别文件
    content_type = "application/octet-stream"
    if filename.lower().endswith(".png"):
        content_type = "image/png"
    elif filename.lower().endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif filename.lower().endswith(".webp"):
        content_type = "image/webp"

    return StreamingResponse(
        stream_image(),
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
