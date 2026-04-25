import os
import sys
import httpx
import asyncio
from dotenv import load_dotenv

# 添加项目根目录到 path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 加载环境
load_dotenv("backend/.env")

from backend.app.services.r2_service import r2_service

async def transfer_images(urls):
    async with httpx.AsyncClient() as client:
        for url in urls:
            print(f"Downloading: {url}")
            resp = await client.get(url)
            if resp.status_code == 200:
                filename = url.split("/")[-1]
                # 加一个前缀防止冲突，或者保持原样
                object_name = f"manual_transfer/{filename}"
                new_url = r2_service.upload_content(resp.content, object_name)
                if new_url:
                    print(f"SUCCESS: {new_url}")
                else:
                    print(f"FAILED to upload: {filename}")
            else:
                print(f"FAILED to download: {url} (Status: {resp.status_code})")

if __name__ == "__main__":
    target_urls = [
        "https://webstatic.aiproxy.vip/output/20260425/47158/179004c9-d2aa-4914-a75e-3a7d12dc03ea.png",
        "https://webstatic.aiproxy.vip/output/20260425/47158/023c9124-5d64-4f34-81de-7360adff9a5d.png"
    ]
    asyncio.run(transfer_images(target_urls))
