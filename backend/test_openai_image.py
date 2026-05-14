import os
import asyncio
import sys
import io
import base64
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 强制控制台输出使用 UTF-8，防止中文在部分终端乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8', line_buffering=True)

async def test_generate_image():
    # 加载 .env 文件
    load_dotenv()
    
    # 获取环境变量
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        print("❌ 错误: 未找到 AI_API_KEY，请确保 .env 文件中已取消注释并正确配置！")
        return
        
    print(f"🔧 配置信息:")
    print(f"   API Key: {api_key[:12]}...{api_key[-4:] if len(api_key)>16 else ''}")
    print(f"   Base URL: {base_url}")
    
    # 初始化 OpenAI 异步客户端
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    print("\n⏳ 正在调用 OpenAI API 生成图片 (gpt-image-2)...")
    try:
        response = await client.images.generate(
            model="gpt-image-2",
            prompt="A cute white cat playing with a ball of yarn, 3D render style, 4k",
            size="1024x1024",
            quality="auto", # 使用 gpt-image-2 支持的 quality 参数
            n=1,
        )
        
        if response.data[0].url:
            image_url = response.data[0].url
            print(f"✅ 生成成功！")
            print(f"🎨 图片预览链接: {image_url}")
        elif response.data[0].b64_json:
            b64_data = response.data[0].b64_json
            print(f"✅ 生成成功！但接口返回的是 Base64 格式，长度为: {len(b64_data)}")
            # 保存到本地图片文件
            image_path = "test_output.png"
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            print(f"🖼️ 图片已成功保存至本地：{os.path.abspath(image_path)}")
        else:
            print(f"✅ 生成成功（状态为成功），但未能解析出 url 或 b64_json。")
            print(f"👉 完整返回体数据: {response.model_dump()}")
        
    except Exception as e:
        print(f"\n❌ 生成图片失败！")
        print(f"异常信息: {str(e)}")

if __name__ == "__main__":
    # 在 Windows 下可能需要设置事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_generate_image())
