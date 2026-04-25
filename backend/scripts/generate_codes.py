import random
import string
import uuid

def generate_redeem_codes(count=20, amount=1.5):
    """
    生成面包多风格的随机兑换码
    格式：GD-XXXX-XXXX-XXXX
    """
    codes = []
    for _ in range(count):
        # 使用字母和数字混合，去掉容易混淆的字符 (O, 0, I, 1)
        chars = ''.join(c for c in string.ascii_uppercase + string.digits if c not in '01OI')
        parts = [''.join(random.choices(chars, k=4)) for _ in range(3)]
        code = f"GD-{''.join(parts[0])}-{''.join(parts[1])}-{''.join(parts[2])}"
        codes.append(code)
    
    print(f"\n-- [SUCCESS] Generated {count} redeem codes (each worth {amount} credits)")
    print("-- 请复制下方 SQL 语句并在 Supabase SQL Editor 中运行以导入卡密：\n")
    
    print("INSERT INTO redeem_codes (code, amount) VALUES")
    values = []
    for c in codes:
        values.append(f"('{c}', {amount})")
    print(",\n".join(values) + ";")
    
    print("\n-- [LIST] Plain text list of redeem codes (copy to Mianbaoduo):")
    for c in codes:
        print(c)

if __name__ == "__main__":
    # 你可以修改这里的参数：第一个是生成数量，第二个是每个码的积分面额
    generate_redeem_codes(20, 1.5)
