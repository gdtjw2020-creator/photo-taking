from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..dependencies import get_user_id

router = APIRouter()

class RedeemRequest(BaseModel):
    code: str

@router.post("/redeem")
async def redeem_code(
    request: RedeemRequest,
    user_id: str = Depends(get_user_id)
):
    """使用卡密兑换积分 (写入 credit_logs 并更新 profiles.credits)"""
    # TODO: 校验卡密并执行数据库事务
    if request.code == "DEBUG100":
        return {"success": True, "amount": 100, "message": "兑换成功"}
    
    raise HTTPException(status_code=400, detail="无效的卡密")
