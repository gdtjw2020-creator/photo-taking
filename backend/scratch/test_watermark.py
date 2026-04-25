import sys
import os
from PIL import Image

# 将 backend 目录加入路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_utils import add_ai_watermark

def test_watermark():
    input_dir = r"C:\Users\Admin\Documents\Downloads"
    output_dir = os.path.join(input_dir, "watermarked_test")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 获取下载目录下的所有图片
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not images:
        print("No images found in Downloads folder.")
        return

    print(f"Found {len(images)} images, starting watermark test...")
    
    for img_name in images[:3]: # Test first 3
        input_path = os.path.join(input_dir, img_name)
        output_path = os.path.join(output_dir, f"watermarked_{img_name}")
        
        # Copy to test, don't destroy original
        import shutil
        shutil.copy2(input_path, output_path)
        
        # Call watermark logic
        success = add_ai_watermark(output_path)
        
        if success:
            print(f"Success: {output_path}")
        else:
            print(f"Failed: {img_name}")

if __name__ == "__main__":
    test_watermark()

