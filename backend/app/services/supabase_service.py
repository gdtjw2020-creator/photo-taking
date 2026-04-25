from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, INITIAL_CREDITS

# 本地内存缓存，防止数据库写入失败导致前端 404
_local_task_cache = {}

class SupabaseService:
    def __init__(self):
        try:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            print(f"Supabase Client Init Error: {e}")
            self.supabase = None

    def create_task(self, task_id: str, user_id: str, template_id: str, input_url: str):
        """创建约拍任务记录"""
        data = {
            "id": task_id,
            "user_id": user_id,
            "template_id": template_id,
            "input_url": input_url,
            "status": "pending",
            "created_at": "now" # 内存版本用
        }
        # 存入本地内存缓存（双写保险）
        _local_task_cache[task_id] = data
        
        if not self.supabase:
            return True

        try:
            res = self.supabase.table("photoshoot_tasks").insert(data).execute()
            print(f"Supabase Create Task Response: {res}")
            return True
        except Exception as e:
            print(f"Error creating task in Supabase (Exception): {e}")
            return True # 返回 True 允许任务继续，依赖内存缓存

    def update_task_status(self, task_id: str, status: str, output_urls: list = None, error_message: str = None):
        """更新任务状态"""
        # 更新本地内存缓存
        if task_id in _local_task_cache:
            _local_task_cache[task_id]["status"] = status
            if output_urls:
                _local_task_cache[task_id]["output_urls"] = output_urls
            if error_message:
                _local_task_cache[task_id]["error_message"] = error_message
        
        if not self.supabase:
            return True

        try:
            data = {"status": status}
            if output_urls:
                data["output_urls"] = output_urls
            if error_message:
                data["error_message"] = error_message
            
            res = self.supabase.table("photoshoot_tasks").update(data).eq("id", task_id).execute()
            print(f"Supabase Update Task Response: {res}")
            return True
        except Exception as e:
            print(f"Error updating task status (Exception): {e}")
            return True

    def get_task(self, task_id: str):
        """获取任务详情"""
        # 优先从本地内存缓存获取（最快且最稳）
        if task_id in _local_task_cache:
            return _local_task_cache[task_id]
            
        if not self.supabase:
            return None

        try:
            res = self.supabase.table("photoshoot_tasks").select("*").eq("id", task_id).execute()
            if res.data:
                return res.data[0]
            return None
        except Exception as e:
            print(f"Error getting task: {e}")
            return None

    def get_user_gallery(self, user_id: str, limit: int = 50):
        """获取用户的约拍作品集"""
        if not self.supabase:
            # 模拟数据
            return [t for t in _local_task_cache.values() if t.get("user_id") == user_id and t.get("status") == "completed"]
        try:
            res = self.supabase.table("photoshoot_tasks").select("*").eq("user_id", user_id).eq("status", "completed").order("created_at", desc=True).limit(limit).execute()
            return res.data
        except Exception as e:
            print(f"Error fetching gallery: {e}")
            return []

    def save_user_face(self, user_id: str, face_url: str, name: str = "未命名面部"):
        """保存一个人脸档案"""
        if not self.supabase:
            return None
        try:
            data = {"user_id": user_id, "face_url": face_url, "name": name}
            print(f"[DEBUG] Saving face for user {user_id}: {data}")
            res = self.supabase.table("user_faces").insert(data).execute()
            print(f"[DEBUG] Save face result: {res}")
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"[ERROR] Error saving face: {e}")
            return None

    def get_user_faces(self, user_id: str):
        """获取用户的所有面部档案"""
        if not self.supabase:
            return []
        try:
            print(f"[DEBUG] Fetching faces for user {user_id}")
            res = self.supabase.table("user_faces").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            print(f"[DEBUG] Found {len(res.data) if res.data else 0} faces")
            return res.data
        except Exception as e:
            print(f"[ERROR] Error fetching faces: {e}")
            return []

    def get_latest_active_task(self, user_id: str):
        """获取用户最新的一条活跃任务 (pending/processing)"""
        # 1. 检查本地内存缓存
        active_in_cache = [t for t in _local_task_cache.values() if t.get("user_id") == user_id and t.get("status") in ("pending", "processing")]
        if active_in_cache:
            # 返回最新创建的
            return active_in_cache[-1]

        if not self.supabase:
            return None
            
        try:
            res = self.supabase.table("photoshoot_tasks")\
                .select("*")\
                .eq("user_id", user_id)\
                .in_("status", ["pending", "processing"])\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            return res.data[0] if res.data else None
        except Exception as e:
            print(f"[ERROR] Error fetching active task: {e}")
            return None

    def delete_user_face(self, user_id: str, face_id: str):
        """删除一个人脸档案"""
        if not self.supabase:
            return True
        try:
            self.supabase.table("user_faces").delete().eq("id", face_id).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting face: {e}")
            return False

    def deduct_credits(self, user_id: str, amount: int, description: str):
        """扣除用户积分并记录日志"""
        if not self.supabase:
            return True
        try:
            # 1. 扣除积分 (使用 rpc 或简单 update，这里简单 update)
            # 注意：实际生产环境建议用 RPC 以保证原子性，这里先用 update 演示
            profile = self.supabase.table("profiles").select("credits").eq("id", user_id).execute()
            if not profile.data:
                return False
            
            new_credits = max(0, profile.data[0]["credits"] - amount)
            self.supabase.table("profiles").update({"credits": new_credits}).eq("id", user_id).execute()
            
            # 2. 记录日志
            log_data = {
                "user_id": user_id,
                "amount": -amount,
                "type": "photoshoot",
                "description": description
            }
            self.supabase.table("credit_logs").insert(log_data).execute()
            print(f"[DEBUG] Credits deducted for user {user_id}: {amount}")
            return True
        except Exception as e:
            print(f"[ERROR] Error deducting credits: {e}")
            return False

    def append_task_output(self, task_id: str, new_url: str):
        """向任务的输出列表中追加一张新图片"""
        # 更新本地缓存
        if task_id in _local_task_cache:
            if "output_urls" not in _local_task_cache[task_id]:
                _local_task_cache[task_id]["output_urls"] = []
            _local_task_cache[task_id]["output_urls"].append(new_url)
            
        if not self.supabase:
            return True
            
        try:
            # 1. 先获取现有列表
            res = self.supabase.table("photoshoot_tasks").select("output_urls").eq("id", task_id).execute()
            current_urls = res.data[0].get("output_urls") or []
            current_urls.append(new_url)
            
            # 2. 更新回去
            self.supabase.table("photoshoot_tasks").update({"output_urls": current_urls}).eq("id", task_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Error appending task output: {e}")
            return False

    def get_all_templates(self):
        """获取所有可用模板"""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table("templates").select("*").eq("is_active", True).execute()
            return res.data
        except Exception as e:
            print(f"Error fetching templates: {e}")
            return []

    def get_user_profile(self, user_id: str):
        """获取用户个人资料"""
        if not self.supabase:
            return {"id": user_id, "username": "本地用户", "credits": INITIAL_CREDITS}
        try:
            res = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                return res.data[0]
            # 如果不存在则自动创建一个初始配置，默认送积分
            new_profile = {"id": user_id, "username": "新用户", "credits": INITIAL_CREDITS}
            self.supabase.table("profiles").insert(new_profile).execute()
            return new_profile
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return {"id": user_id, "username": "系统用户", "credits": 0}

    def redeem_code(self, user_id: str, code: str):
        """兑换充值码"""
        if not self.supabase:
            return False, "系统配置错误"
            
        try:
            # 1. 查找兑换码
            res = self.supabase.table("redeem_codes")\
                .select("*")\
                .eq("code", code)\
                .eq("is_used", False)\
                .execute()
                
            if not res.data:
                return False, "无效或已被使用的兑换码"
                
            code_data = res.data[0]
            amount = code_data.get("amount", 0)
            
            # 2. 标记为已使用 (通过 update 返回结果确认是否竞争成功)
            from datetime import datetime
            update_res = self.supabase.table("redeem_codes")\
                .update({
                    "is_used": True, 
                    "used_by": user_id, 
                    "used_at": datetime.now().isoformat()
                })\
                .eq("id", code_data["id"])\
                .eq("is_used", False)\
                .execute()
                
            if not update_res.data:
                return False, "该兑换码已被他人抢先使用"
                
            # 3. 给用户加分
            profile_res = self.supabase.table("profiles").select("credits").eq("id", user_id).execute()
            if not profile_res.data:
                return False, "用户档案不存在"
                
            current_credits = profile_res.data[0].get("credits", 0)
            new_credits = current_credits + amount
            self.supabase.table("profiles").update({"credits": new_credits}).eq("id", user_id).execute()
            
            # 4. 记录日志
            self.supabase.table("credit_logs").insert({
                "user_id": user_id,
                "amount": amount,
                "type": "recharge",
                "description": f"卡密兑换: {code[:4]}****"
            }).execute()
            
            return True, amount
        except Exception as e:
            print(f"Redeem error: {e}")
            return False, "兑换系统暂时不可用"

    def get_credit_logs(self, user_id: str):
        """获取用户的积分变动明细"""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table("credit_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            return res.data
        except Exception as e:
            print(f"Error fetching credit logs: {e}")
            return []

    def save_feedback(self, user_id: str, content: str, feedback_type: str = "style_request"):
        """保存用户反馈"""
        if not self.supabase:
            return True
        try:
            data = {
                "user_id": user_id,
                "content": content,
                "type": feedback_type
            }
            self.supabase.table("feedback").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False

supabase_service = SupabaseService()
