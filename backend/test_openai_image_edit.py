import asyncio
import os
import sys
import base64
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 强制输出为 UTF-8 编码，防止控制台乱码
sys.stdout.reconfigure(encoding='utf-8')
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

async def test_openai_image_edit():
    load_dotenv()
    
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        print("❌ 错误: 未找到 AI_API_KEY，请确保 .env 文件中已取消注释并正确配置！")
        return
        
    image_path = "test_output.png"
    if not os.path.exists(image_path):
        print(f"❌ 错误: 未找到图片 {image_path}，请先运行 test_openai_image.py 生成图片！")
        return

    print(f"🔧 配置信息:")
    print(f"   API Key: {api_key[:12]}...{api_key[-4:] if len(api_key)>16 else ''}")
    print(f"   Base URL: {base_url}")
    print(f"   准备编辑图片: {image_path}")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    print("\n⏳ 正在调用 OpenAI API 编辑图片 (gpt-image-2)...")
    try:
        # 打开原始图片
        with open(image_path, "rb") as image_file:
            response = await client.images.edit(
                model="gpt-image-2",
                image=image_file,
                prompt="A cute white cat wearing a shiny golden crown and red sunglasses, 3D render style, 4k",
                size="1024x1024",
                n=1,
            )
        
        if response.data[0].url:
            image_url = response.data[0].url
            print(f"✅ 编辑成功！")
            print(f"🎨 图片预览链接: {image_url}")
        elif response.data[0].b64_json:
            b64_data = response.data[0].b64_json
            print(f"✅ 编辑成功！接口返回了 Base64 格式数据。")
            
            # 保存修改后的图片
            output_path = "test_edit_output.png"
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            print(f"🖼️ 编辑后的图片已成功保存至本地：{os.path.abspath(output_path)}")
        else:
            print(f"✅ 编辑成功（状态为成功），但未能解析出 url 或 b64_json。")
            
    except Exception as e:
        print(f"\n❌ 编辑图片失败！")
        print(f"异常信息: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_image_edit())
