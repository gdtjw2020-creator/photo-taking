import httpx
import json
import asyncio
import traceback
import random
from typing import List, Optional
from ..config import (
    AI_API_KEY, AI_BASE_URL, AI_MODEL_NAME, AI_IMAGE_SIZE, AI_IMAGE_QUALITY,
    AI_IMAGE_OUTPUT_FORMAT, AI_IMAGE_MODERATION, AI_POLL_INTERVAL_SECONDS, AI_POLL_MAX_ATTEMPTS,
    AI_PROVIDER, OPENROUTER_API_KEY, OPENROUTER_MODEL
)

class AIService:
    def __init__(self):
        self.api_key = AI_API_KEY
        self.base_url = AI_BASE_URL
        self.model_name = AI_MODEL_NAME
        self.image_size = AI_IMAGE_SIZE
        self.image_quality = AI_IMAGE_QUALITY
        self.output_format = AI_IMAGE_OUTPUT_FORMAT
        self.moderation = AI_IMAGE_MODERATION
        self.poll_interval = AI_POLL_INTERVAL_SECONDS
        self.poll_max_attempts = AI_POLL_MAX_ATTEMPTS

    async def upload_file(self, file_content: bytes, filename: str) -> Optional[str]:
        """上传图片到第三方平台，获取一个他们能直接访问的内部 URL"""
        url = f"{self.base_url}/v1/files"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # 使用 multipart/form-data 格式
        files = {
            "file": (filename, file_content, "image/png")
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 注意：httpx 的 files 参数用法
                response = await client.post(url, headers=headers, files=files)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("url")
                else:
                    print(f"❌ 上传到平台失败: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"❌ 上传到平台异常: {str(e)}")
            return None

    async def generate_images(self, input_url: str, prompt: str, ref_url: Optional[str] = None) -> List[str]:
        """
        核心生成逻辑入口 (路由到不同的 Provider)
        """
        if AI_PROVIDER == "openrouter":
            return await self._generate_openrouter(input_url, prompt)
        else:
            return await self._generate_zhenzhen(input_url, prompt, ref_url)

    async def _generate_openrouter(self, input_url: str, prompt: str) -> List[str]:
        """
        使用 OpenRouter 接口生成图片
        """
        job_no = random.randint(100, 999)
        print(f"🚀 [OpenRouter任务#{job_no}] 正在提交生成请求...")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Using the woman in the provided image as a character reference, generate a cinematic, photorealistic 4K image. {prompt}. High skin texture, authentic film grain, masterpiece."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": input_url
                            }
                        }
                    ]
                }
            ],
            "extra_body": {
                "modalities": ["image", "text"],
                "size": "1024x1024"
            }
        }
        
        try:
            # 延长超时时间以支持生图
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    print(f"❌ [OpenRouter任务#{job_no}] 请求失败: {response.status_code} - {response.text}")
                    return []
                    
                data = response.json()
                try:
                    # 尝试从 OpenRouter 返回的特定结构中获取数据
                    choices = data.get("choices", [])
                    if not choices:
                        print(f"⚠️ [OpenRouter任务#{job_no}] 响应中没有 choices 数据: {json.dumps(data, ensure_ascii=False)}")
                        return []
                        
                    message = choices[0].get("message", {})
                    
                    # 结构 1: images 数组内嵌在 message 中
                    if "images" in message and isinstance(message["images"], list) and len(message["images"]) > 0:
                        image_url = message["images"][0].get("image_url", {}).get("url")
                        if image_url:
                            print(f"✅ [OpenRouter任务#{job_no}] 成功提取图片 (从 images 结构)")
                            return [image_url]
                            
                    # 结构 2: image_url 直接返回或者在 content 中
                    content = message.get("content", "")
                    if isinstance(content, str) and (content.startswith("http") or content.startswith("data:image/")):
                        print(f"✅ [OpenRouter任务#{job_no}] 成功提取图片 (从 content 结构)")
                        return [content]
                    
                    # 如果上述解析失败，打印结构以便调试
                    print(f"⚠️ [OpenRouter任务#{job_no}] 无法解析返回数据结构: {json.dumps(message, ensure_ascii=False)}")
                    return []
                    
                except Exception as parse_e:
                    print(f"❌ [OpenRouter任务#{job_no}] 解析响应异常: {str(parse_e)}")
                    return []
                    
        except Exception as e:
            print(f"‼️ [OpenRouter任务#{job_no}] 异常: {str(e)}")
            traceback.print_exc()
            return []

    async def _generate_zhenzhen(self, input_url: str, prompt: str, ref_url: Optional[str] = None) -> List[str]:
        """
        核心生成逻辑 (支持多图下载与提交)
        """
        job_no = random.randint(100, 999)
        try:
            # 0. 预处理：下载图片用于表单提交
            print(f"🔄 [任务#{job_no}] 正在下载参考图片...")
            image_bytes_list = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 下载图1 (人脸图)
                if input_url:
                    resp1 = await client.get(input_url)
                    if resp1.status_code == 200:
                        image_bytes_list.append(resp1.content)
                        print(f"✅ [任务#{job_no}] 图1(人脸)下载成功")
                    else:
                        print(f"⚠️ [任务#{job_no}] 图1下载失败: {resp1.status_code}")
                
                # 下载图2 (动作参考图)
                if ref_url:
                    resp2 = await client.get(ref_url)
                    if resp2.status_code == 200:
                        image_bytes_list.append(resp2.content)
                        print(f"✅ [任务#{job_no}] 图2(参考)下载成功")
                    else:
                        print(f"⚠️ [任务#{job_no}] 图2下载失败: {resp2.status_code}")

            # 1. 提交任务
            ext_id = await self._submit_task(image_bytes_list, prompt)
            if not ext_id:
                return []

            print(f"🚀 [任务#{job_no}] 提交成功！外部 ID: {ext_id}")

            # 2. 轮询状态
            for i in range(self.poll_max_attempts):
                result = await self._query_task(ext_id)
                
                # 参考项目逻辑：data = result.get('data', {})
                data = result.get('data', {})
                status = data.get('status', 'IN_PROGRESS').upper()
                
                if i % (10 // self.poll_interval + 1) == 0:
                    print(f"⏳ [任务#{job_no}] 正在查询... 状态: [{status}]")

                # 成功判断：必须是 SUCCESS
                if status == "SUCCESS":
                    # 深度提取图片：data -> data -> data[0] -> url
                    inner_data = data.get('data', {})
                    images = inner_data.get('data', [])
                    if images and len(images) > 0:
                        img_url = images[0].get('url')
                        print(f"✅ [任务#{job_no}] 任务完成！获取到图片地址")
                        return [img_url]
                    else:
                        print(f"⚠️ [任务#{job_no}] 状态成功但未找到图片数据: {json.dumps(data, ensure_ascii=False)}")
                
                # 失败判断
                if status == "FAILURE":
                    fail_reason = data.get('fail_reason', '未知失败')
                    error_msg = f"平台异常: {fail_reason}"
                    print(f"❌ [任务#{job_no}] 任务失败！原因: {fail_reason}")
                    raise Exception(error_msg)
                
                await asyncio.sleep(self.poll_interval)
            
            print(f"❌ [任务#{job_no}] 任务超时！超过最大轮询次数。")
            raise Exception("生图排队超时：当前服务器生图排队人数过多，请稍后再试")
        except Exception as e:
            print(f"‼️ [任务#{job_no}] 异常: {str(e)}")
            traceback.print_exc()
            raise e

    async def _submit_task(self, image_bytes_list: List[bytes], prompt: str) -> Optional[str]:
        """提交任务 (返回 task_id)"""
        url = f"{self.base_url}/v1/images/edits?async=true"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # 注意：使用 files 参数时，httpx 会自动生成包含 boundary 的 multipart/form-data Content-Type
        }
        
        # 如果有多张图（换脸模式），自动使用 'auto' 尺寸以匹配目标底图大小
        size_to_use = "auto" if image_bytes_list and len(image_bytes_list) > 1 else self.image_size

        data = {
            "model": self.model_name,
            "prompt": f"{prompt}, 4K",
            "quality": self.image_quality,
            "size": size_to_use,
            "output_format": self.output_format,
            "moderation": self.moderation
        }

        # 构建 files 数组 (支持多张同名 image 字段)
        files = []
        if image_bytes_list and len(image_bytes_list) > 0:
            from io import BytesIO
            from PIL import Image
            for i, img_bytes in enumerate(image_bytes_list):
                try:
                    # 严格按照官方节点逻辑，将所有输入强制转换为标准 PNG 格式
                    img = Image.open(BytesIO(img_bytes)).convert("RGB")
                    
                    # 如果原图过大，可以考虑加一个 resize 保护 (长边不超过 3840)
                    max_edge = max(img.size)
                    if max_edge > 3840:
                        ratio = 3840.0 / max_edge
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    files.append(("image", (f"image_{i}.png", buf.getvalue(), "image/png")))
                except Exception as e:
                    print(f"⚠️ 图片 {i} 转换 PNG 失败: {e}，将使用原始字节")
                    files.append(("image", (f"image_{i}.png", img_bytes, "image/png")))
        else:
            # 如果没有图片，官方节点会上传一张空白图片来规避 API 限制
            from io import BytesIO
            from PIL import Image
            buf = BytesIO()
            Image.new("RGB", (1024, 1024), color="white").save(buf, format="PNG")
            files.append(("image", ("blank.png", buf.getvalue(), "image/png")))

        # 增加详细日志打印，以排查传图或参数是否正确
        print(f"================ API REQUEST DEBUG ================")
        print(f"URL: {url}")
        print(f"DATA: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        file_log_info = []
        for field_name, (file_name, file_bytes, content_type) in files:
            file_log_info.append({
                "field_name": field_name,
                "file_name": file_name,
                "content_type": content_type,
                "size_bytes": len(file_bytes)
            })
        print(f"FILES: {json.dumps(file_log_info, indent=2)}")
        print(f"===================================================")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, data=data, files=files)
                result = response.json()
                
                if response.status_code == 200:
                    # 优先取 task_id
                    return result.get("task_id") or result.get("id")
                else:
                    print(f"DEBUG: 提交失败原始数据: {json.dumps(result, ensure_ascii=False)}")
                    return None
        except Exception as e:
            print(f"❌ 提交错误: {str(e)}")
            return None

    async def _query_task(self, ext_id: str) -> dict:
        """查询任务状态 (使用参考项目的正确地址)"""
        # 正确地址：/v1/images/tasks/{id}
        url = f"{self.base_url}/v1/images/tasks/{ext_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                return {"data": {"status": "ERROR"}}
        except Exception:
            return {"data": {"status": "ERROR"}}

ai_service = AIService()
