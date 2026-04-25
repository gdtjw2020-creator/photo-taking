from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_user_id
from ..services.supabase_service import supabase_service
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()

@router.get("/profile")
async def get_profile(user_id: str = Depends(get_user_id)):
    """获取用户个人资料 (从数据库获取真实数据)"""
    profile = supabase_service.get_user_profile(user_id)
    return {
        "user_id": user_id,
        "username": profile.get("username", "女神用户"),
        "avatar_url": profile.get("avatar_url"),
        "credits": profile.get("credits", 0)
    }

@router.get("/credits")
async def get_credits(user_id: str = Depends(get_user_id)):
    """获取用户剩余积分"""
    profile = supabase_service.get_user_profile(user_id)
    return {"credits": profile.get("credits", 0)}

class RedeemRequest(BaseModel):
    code: str

@router.post("/redeem")
async def redeem_code(request: RedeemRequest, user_id: str = Depends(get_user_id)):
    """兑换卡密充值积分"""
    success, result = supabase_service.redeem_code(user_id, request.code)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return {"status": "success", "amount": result, "message": f"兑换成功，已充值 {result} 积分"}

@router.get("/credit_logs")
async def get_credit_logs(user_id: str = Depends(get_user_id)):
    """获取积分明细"""
    logs = supabase_service.get_credit_logs(user_id)
    return logs

class FeedbackRequest(BaseModel):
    content: str
    type: Optional[str] = "style_request"

@router.post("/feedback")
async def post_feedback(request: FeedbackRequest, user_id: str = Depends(get_user_id)):
    """提交用户反馈"""
    success = supabase_service.save_feedback(user_id, request.content, request.type)
    if not success:
        raise HTTPException(status_code=500, detail="提交失败")
    return {"status": "success", "message": "反馈已收到，感谢您的建议！"}
