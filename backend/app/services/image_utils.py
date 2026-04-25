from PIL import Image, ImageDraw, ImageFont
import os

def add_ai_watermark(image_path: str, text: str = "AI 合成 / AI Generated"):
    """
    为图片添加半透明水印
    """
    try:
        # 打开图片
        img = Image.open(image_path).convert("RGBA")
        
        # 创建一个透明层用于绘制水印
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        
        # 准备绘制
        draw = ImageDraw.Draw(txt_layer)
        
        # 尝试加载中文字体，如果失败则使用默认
        # 注意：在Railway(Linux)上需要指定字体路径，如 /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
        try:
            # 常见中文字体路径 (Windows)
            font_path = "C:\\Windows\\Fonts\\msyh.ttc" 
            if not os.path.exists(font_path):
                # 常见中文字体路径 (Linux)
                font_path = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
            
            font_size = int(img.size[0] / 30)  # 根据图片宽度动态计算字号
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
            
        # 计算位置 (右下角)
        margin = 20
        # 获取文字尺寸 (旧版 Pillow 使用 getsize, 新版推荐使用 textbbox)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            textwidth = bbox[2] - bbox[0]
            textheight = bbox[3] - bbox[1]
        except AttributeError:
            textwidth, textheight = draw.textsize(text, font)
            
        x = img.size[0] - textwidth - margin
        y = img.size[1] - textheight - margin
        
        # 绘制半透明文字 (白色，50%透明度)
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
        
        # 合并图层
        out = Image.alpha_composite(img, txt_layer)
        
        # 保存回原始路径 (转回 RGB 以存为 JPEG)
        out.convert("RGB").save(image_path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"Error adding watermark: {e}")
        return False
