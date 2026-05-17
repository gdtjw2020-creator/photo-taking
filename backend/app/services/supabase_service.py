from supabase import create_client, Client
from datetime import datetime, timezone
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

    def create_task(
        self,
        task_id: str,
        user_id: str,
        template_id: str,
        input_url: str,
        module_type: str = None,
        style_id: str = None,
        metadata: dict = None
    ):
        """创建约拍任务记录"""
        data = {
            "id": task_id,
            "user_id": user_id,
            "template_id": template_id,
            "input_url": input_url,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat() # 内存版本用，使用 ISO 格式
        }
        extended_data = {
            **data,
            "module_type": module_type,
            "style_id": style_id,
            "metadata": metadata or {}
        }
        # 存入本地内存缓存（双写保险）
        _local_task_cache[task_id] = extended_data
        
        if not self.supabase:
            return True

        try:
            res = self.supabase.table("photoshoot_tasks").insert(extended_data).execute()
            print(f"Supabase Create Task Response: {res}")
            return True
        except Exception as e:
            print(f"Error creating task in Supabase with extended fields (Exception): {e}")
            try:
                # T04 迁移前，远程表可能还没有 module_type/style_id/metadata 字段。
                # 回退到旧字段插入，确保现有生成流程不被新字段阻断。
                res = self.supabase.table("photoshoot_tasks").insert(data).execute()
                print(f"Supabase Create Task Fallback Response: {res}")
                return True
            except Exception as fallback_e:
                print(f"Error creating task in Supabase fallback (Exception): {fallback_e}")
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

    def save_user_face(self, user_id: str, face_url: str, name: str = "未命名形象"):
        """保存一个形象档案"""
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
        """获取用户的所有形象档案"""
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
        """获取用户最新的一条活跃任务 (pending/processing)，并自动熔断过期的僵尸任务"""
        # 1. 检查本地内存缓存
        active_in_cache = [t for t in _local_task_cache.values() if t.get("user_id") == user_id and t.get("status") in ("pending", "processing")]
        
        task = None
        if active_in_cache:
            task = active_in_cache[-1]
        elif self.supabase:
            try:
                res = self.supabase.table("photoshoot_tasks")\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .in_("status", ["pending", "processing"])\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()
                if res.data:
                    task = res.data[0]
            except Exception as e:
                print(f"[ERROR] Error fetching active task: {e}")

        # 2. 自动熔断僵尸任务
        if task and task.get("status") in ("pending", "processing") and "created_at" in task:
            try:
                created_at_str = task["created_at"]
                if created_at_str != "now":
                    # 处理带Z或偏移量的 ISO 字符串
                    created_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    elapsed_seconds = (now - created_time).total_seconds()
                    
                    # 获取提示词数量（用来计算动态超时时间，默认最少 1 张，每张最长 7 分钟）
                    metadata = task.get("metadata") or {}
                    if isinstance(metadata, str):
                        import json
                        try:
                            metadata = json.loads(metadata)
                        except:
                            metadata = {}
                    prompts_count = len(metadata.get("selected_prompts", [])) or 1
                    dynamic_timeout = prompts_count * 7 * 60
                    
                    if elapsed_seconds > dynamic_timeout:
                        print(f"[DEBUG] Found zombie active task {task['id']}, elapsed {elapsed_seconds}s > {dynamic_timeout}s. Marking failed.")
                        self.update_task_status(task["id"], "failed", error_message=f"生成任务严重超时超过 {prompts_count * 7} 分钟限制，已被系统安全熔断")
                        # 更新内存状态，防止当前请求继续返回该任务为活跃
                        task["status"] = "failed"
                        return None
            except Exception as e:
                print(f"检测僵尸活跃任务失败: {e}")

        return task if task and task.get("status") in ("pending", "processing") else None

    def delete_user_face(self, user_id: str, face_id: str):
        """删除一个形象档案"""
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

    def remove_task_output(self, user_id: str, task_id: str, image_url: str):
        """从任务输出列表中移除一张图片。如果列表为空，则删除整个任务。"""
        # 更新本地缓存
        if task_id in _local_task_cache:
            if "output_urls" in _local_task_cache[task_id]:
                try:
                    _local_task_cache[task_id]["output_urls"].remove(image_url)
                except ValueError:
                    pass
        
        if not self.supabase:
            return True
            
        try:
            # 1. 获取现有任务
            res = self.supabase.table("photoshoot_tasks").select("*").eq("id", task_id).eq("user_id", user_id).execute()
            if not res.data:
                return False
                
            task = res.data[0]
            current_urls = task.get("output_urls") or []
            
            if image_url in current_urls:
                current_urls.remove(image_url)
                
                if not current_urls:
                    # 如果没有图片了，直接删除任务记录
                    self.supabase.table("photoshoot_tasks").delete().eq("id", task_id).execute()
                else:
                    # 否则更新列表
                    self.supabase.table("photoshoot_tasks").update({"output_urls": current_urls}).eq("id", task_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] Error removing task output: {e}")
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
            print(f"[DEBUG] Supabase not initialized, returning local default for user: {user_id}")
            return {"id": user_id, "username": "本地用户", "credits": INITIAL_CREDITS}
        try:
            print(f"[DEBUG] Fetching profile for user_id: {user_id}")
            res = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                profile = res.data[0]
                print(f"[DEBUG] Profile found: {profile.get('username')}, Credits: {profile.get('credits')}")
                return profile
            
            # 如果不存在则自动创建一个初始配置，默认送积分
            print(f"[DEBUG] Profile not found for {user_id}, creating new one...")
            new_profile = {"id": user_id, "username": "新用户", "credits": INITIAL_CREDITS}
            self.supabase.table("profiles").insert(new_profile).execute()
            return new_profile
        except Exception as e:
            print(f"[ERROR] Exception in get_user_profile for {user_id}: {str(e)}")
            import traceback
            traceback.print_exc()
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
            update_res = self.supabase.table("redeem_codes")\
                .update({
                    "is_used": True, 
                    "used_by": user_id, 
                    "used_at": datetime.now(timezone.utc).isoformat()
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

    def get_all_feedbacks(self):
        """获取所有用户反馈 (仅管理员使用)"""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table("feedback")\
                .select("*")\
                .order("created_at", desc=True)\
                .execute()
            return res.data
        except Exception as e:
            print(f"Error fetching feedbacks: {e}")
            return []

    def get_style_overrides(self) -> dict:
        """从数据库获取风格覆盖配置 (如封面图)"""
        if not self.supabase:
            return {}
        try:
            res = self.supabase.table("photoshoot_styles").select("id, preview_url").execute()
            return {item["id"]: item for item in res.data}
        except Exception as e:
            print(f"Error fetching style overrides: {e}")
            return {}

    def update_style_preview(self, style_id: str, preview_url: str) -> bool:
        """更新或创建风格的预览图记录"""
        if not self.supabase:
            return True
        try:
            data = {"id": style_id, "preview_url": preview_url, "updated_at": datetime.now(timezone.utc).isoformat()}
            # 使用 upsert
            self.supabase.table("photoshoot_styles").upsert(data).execute()
            return True
        except Exception as e:
            print(f"Error updating style preview: {e}")
            return False

supabase_service = SupabaseService()
