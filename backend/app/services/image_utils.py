from PIL import Image, ImageDraw, ImageFont
import os
import io

def add_ai_watermark(image_path: str, text: str = "AI生成"):
    """
    为本地文件添加半透明水印
    """
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        watermarked_bytes = apply_watermark_to_bytes(image_bytes, text)
        
        if watermarked_bytes:
            with open(image_path, "wb") as f:
                f.write(watermarked_bytes)
            return True
        return False
    except Exception as e:
        print(f"Error adding watermark to file: {e}")
        return False

def apply_watermark_to_bytes(image_bytes: bytes, text: str = "AI生成") -> bytes:
    """
    为图片字节流添加半透明水印，并返回新的字节流
    """
    try:
        # 打开图片
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # 创建一个透明层用于绘制水印
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        
        # 准备绘制
        draw = ImageDraw.Draw(txt_layer)
        
        # 尝试加载中文字体
        font = _get_font(img.size[0])
            
        # 计算位置 (右下角)
        margin = 20
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            textwidth = bbox[2] - bbox[0]
            textheight = bbox[3] - bbox[1]
        except AttributeError:
            textwidth, textheight = draw.textsize(text, font)
            
        x = img.size[0] - textwidth - margin
        y = img.size[1] - textheight - margin
        
        # 绘制极低透明度文字 (白色，约 20% 透明度: 50/255)
        # 这样既符合合规要求，又不影响整体观感
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 50))
        
        # 合并图层
        out = Image.alpha_composite(img, txt_layer)
        
        # 转回 RGB 并输出为字节流
        output = io.BytesIO()
        out.convert("RGB").save(output, format="JPEG", quality=95)
        return output.getvalue()
    except Exception as e:
        print(f"Error applying watermark: {e}")
        return image_bytes # 失败则返回原图，保证业务不中断

def _get_font(img_width: int):
    """获取适配环境的字体"""
    font_paths = [
        "C:\\Windows\\Fonts\\msyh.ttc",              # Windows 微软雅黑
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", # Linux 文泉驿
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux 备用
        "/system/fonts/NotoSansCJK-Regular.ttc",      # Android
    ]
    
    font_size = max(12, int(img_width / 35))
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except:
                continue
    
    return ImageFont.load_default()

