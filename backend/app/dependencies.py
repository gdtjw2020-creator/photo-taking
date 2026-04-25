"""统一鉴权依赖项"""
from fastapi import Header, HTTPException, Depends
from typing import Optional, Dict, Any
import base64
import json
from .config import SERVICE_ACTIVE

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """尝试获取用户ID，如果未登录则返回 None"""
    if not authorization or not authorization.startswith('Bearer '):
        return None
    try:
        token = authorization.split(' ')[1]
        payload = token.split('.')[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        return data.get('sub')
    except Exception:
        return None

def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """强制要求登录，提取 user_id"""
    user_id = get_optional_user(authorization)
    if not user_id:
        # 开发模式特殊处理：如果环境变量允许，返回测试 ID
        from .config import DEBUG
        if DEBUG:
            return "00000000-0000-0000-0000-000000000001"
        raise HTTPException(status_code=401, detail="请先登录后操作")
    return user_id

def check_service_active():
    """检查服务是否处于激活状态（熔断开关）"""
    if not SERVICE_ACTIVE:
        raise HTTPException(status_code=503, detail="服务维护中，请稍后再试")
    return True
