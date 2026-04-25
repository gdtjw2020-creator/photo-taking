import httpx
import json
import asyncio
import traceback
import random
from typing import List, Optional
from ..config import AI_API_KEY, AI_BASE_URL, AI_MODEL_NAME, AI_IMAGE_SIZE, AI_IMAGE_QUALITY

class AIService:
    def __init__(self):
        self.api_key = AI_API_KEY
        self.base_url = AI_BASE_URL
        self.model_name = AI_MODEL_NAME
        self.image_size = AI_IMAGE_SIZE
        self.image_quality = AI_IMAGE_QUALITY

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

    async def generate_images(self, input_url: str, prompt: str) -> List[str]:
        """
        核心生成逻辑 (支持自动转存受限 URL)
        """
        job_no = random.randint(100, 999)
        try:
            # 0. 预处理：解决第三方平台无法访问 R2 地址的问题
            # 如果 URL 包含 cdn.flashvideos.org，先转存到平台内部
            platform_url = input_url
            if "cdn.flashvideos.org" in input_url:
                print(f"🔄 [任务#{job_no}] 检测到外部受限 URL，正在转存到平台内部...")
                async with httpx.AsyncClient() as client:
                    resp = await client.get(input_url)
                    if resp.status_code == 200:
                        uploaded_url = await self.upload_file(resp.content, "input_ref.png")
                        if uploaded_url:
                            platform_url = uploaded_url
                            print(f"✅ [任务#{job_no}] 转存成功: {platform_url}")
                        else:
                            print(f"⚠️ [任务#{job_no}] 转存失败，将尝试直接使用原地址")

            # 1. 提交任务
            ext_id = await self._submit_task(platform_url, prompt)
            if not ext_id:
                return []

            print(f"🚀 [任务#{job_no}] 提交成功！外部 ID: {ext_id}")

            # 2. 轮询状态 (提升至 600 次以支持最高 20 分钟的生成时间)
            max_retries = 600 
            for i in range(max_retries):
                result = await self._query_task(ext_id)
                
                # 参考项目逻辑：data = result.get('data', {})
                data = result.get('data', {})
                status = data.get('status', 'IN_PROGRESS').upper()
                
                if i % 10 == 0:
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
                    print(f"❌ [任务#{job_no}] 任务失败！原因: {fail_reason}")
                    return []
                
                await asyncio.sleep(2)
            
            return []
        except Exception as e:
            print(f"‼️ [任务#{job_no}] 异常: {str(e)}")
            traceback.print_exc()
            return []

    async def _submit_task(self, input_url: str, prompt: str) -> Optional[str]:
        """提交任务 (返回 task_id)"""
        url = f"{self.base_url}/v1/images/generations?async=true"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "prompt": f"{prompt}, extremely detailed, masterpiece, cinematic lighting",
            "response_format": "url",
            "quality": self.image_quality
        }

        # 根据模型类型适配参数 (统一适配 gpt-image-2 的最新推荐规范)
        # 优先使用 size 和 image (数组格式) 以获得最佳兼容性
        payload.update({
            "image": [input_url],
            "size": self.image_size
        })

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
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
