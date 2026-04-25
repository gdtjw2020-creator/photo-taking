-- ====================================================================
-- AI 女神约拍神器 - 核心数据库结构 (Schema)
-- ====================================================================

-- 开启扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. 用户档案表 (扩展 Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  username TEXT,
  avatar_url TEXT,
  credits INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. 约拍模板表
CREATE TABLE IF NOT EXISTS public.templates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  preview_url TEXT,
  prompts TEXT[] NOT NULL, -- 存储 5 张套图的提示词数组
  reference_image_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. 约拍任务表
CREATE TABLE IF NOT EXISTS public.photoshoot_tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL, -- 为了开发方便，先移除 auth.users 强外键，或保持为 UUID
  template_id UUID REFERENCES public.templates,
  status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
  input_url TEXT,
  output_urls TEXT[], -- 存储生成的多张图片链接
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. 积分消费/充值流水
CREATE TABLE IF NOT EXISTS public.credit_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  amount INTEGER NOT NULL, -- 正数为充值，负数为消费
  type TEXT, -- photoshoot, recharge, gift
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. 用户面部存档表 (永久保存人脸)
CREATE TABLE IF NOT EXISTS public.user_faces (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  face_url TEXT NOT NULL,
  name TEXT DEFAULT '未命名面部',
  is_favorite BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. 开启 Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photoshoot_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_faces ENABLE ROW LEVEL SECURITY;

-- 7. 创建安全策略 (使用 DROP POLICY IF EXISTS 确保幂等性)

-- Profiles
DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
CREATE POLICY "Users can view their own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
CREATE POLICY "Users can update their own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Templates
DROP POLICY IF EXISTS "Anyone can view templates" ON public.templates;
CREATE POLICY "Anyone can view templates" ON public.templates FOR SELECT USING (is_active = true);

-- Photoshoot Tasks
DROP POLICY IF EXISTS "Users can view their own photoshoot tasks" ON public.photoshoot_tasks;
CREATE POLICY "Users can view their own photoshoot tasks" ON public.photoshoot_tasks FOR SELECT USING (true); -- 开发模式允许所有人查看，生产环境请改回 auth.uid() = user_id

DROP POLICY IF EXISTS "System can insert tasks" ON public.photoshoot_tasks;
CREATE POLICY "System can insert tasks" ON public.photoshoot_tasks FOR INSERT WITH CHECK (true);

-- Credit Logs
DROP POLICY IF EXISTS "Users can view their own credit logs" ON public.credit_logs;
CREATE POLICY "Users can view their own credit logs" ON public.credit_logs FOR SELECT USING (true);

-- User Faces
DROP POLICY IF EXISTS "Users can manage their own faces" ON public.user_faces;
CREATE POLICY "Users can manage their own faces" ON public.user_faces FOR ALL USING (true);


-- 创建卡密表
CREATE TABLE IF NOT EXISTS public.redeem_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT UNIQUE NOT NULL, 
    amount FLOAT DEFAULT 1.5,   
    is_used BOOLEAN DEFAULT FALSE, 
    used_by UUID REFERENCES auth.users(id), 
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
-- 开启安全策略
ALTER TABLE public.redeem_codes ENABLE ROW LEVEL SECURITY;
-- 记录日志：修改积分相关字段为浮点型以支持 1.5 分
ALTER TABLE public.profiles ALTER COLUMN credits TYPE FLOAT;
ALTER TABLE public.credit_logs ALTER COLUMN amount TYPE FLOAT;
-- 注意：不需要为 redeem_codes 表添加任何 POLICY。
-- 后端使用 service_role 秘钥会自动绕过 RLS，而前端用户将无法访问。

-- 7. 用户反馈表
CREATE TABLE IF NOT EXISTS public.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    content TEXT NOT NULL,
    type TEXT DEFAULT 'style_request',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
-- 开启安全策略
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can insert feedback" ON public.feedback;
CREATE POLICY "Anyone can insert feedback" ON public.feedback FOR INSERT WITH CHECK (true);
