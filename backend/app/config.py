"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "zhenzhen").lower() # 'zhenzhen' or 'openrouter'

# 中间商 AI API配置 (GPT-image2)
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai-proxy.com/v1")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-image-2")
AI_IMAGE_SIZE = os.getenv("AI_IMAGE_SIZE", "1440x2560")
AI_IMAGE_QUALITY = os.getenv("AI_IMAGE_QUALITY", "high")
AI_IMAGE_OUTPUT_FORMAT = os.getenv("AI_IMAGE_OUTPUT_FORMAT", "webp")
AI_IMAGE_MODERATION = os.getenv("AI_IMAGE_MODERATION", "low")
AI_POLL_INTERVAL_SECONDS = int(os.getenv("AI_POLL_INTERVAL_SECONDS", "5"))
AI_POLL_MAX_ATTEMPTS = int(os.getenv("AI_POLL_MAX_ATTEMPTS", "120"))

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.4-image-2")

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Cloudflare R2配置
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "goddess-photoshoot")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "")
R2_CUSTOM_DOMAIN = os.getenv("R2_CUSTOM_DOMAIN", "")

# 服务熔断开关
SERVICE_ACTIVE = os.getenv("SERVICE_ACTIVE", "true").lower() in ("true", "1", "t")

# 积分配置
CREDITS_PER_PHOTOSHOOT = float(os.getenv("CREDITS_PER_PHOTOSHOOT", "1.5"))
INITIAL_CREDITS = float(os.getenv("INITIAL_CREDITS", "1.5"))
