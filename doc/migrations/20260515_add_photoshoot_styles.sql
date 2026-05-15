-- [2026-05-15] 时代写真 MVP 风格配置与管理权限更新

-- 1. 创建风格配置表：用于存储管理员自定义的封面图 (preview_url)
CREATE TABLE IF NOT EXISTS photoshoot_styles (
    id TEXT PRIMARY KEY,           -- 风格 ID (与后端代码 data/old_photo_styles.py 中的 ID 对应)
    preview_url TEXT NOT NULL,      -- 管理员上传的封面图链接
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 开启 RLS (Row Level Security)
ALTER TABLE photoshoot_styles ENABLE ROW LEVEL SECURITY;

-- 策略 A：允许所有人查看风格封面
CREATE POLICY "Allow public read photoshoot_styles" 
ON photoshoot_styles FOR SELECT USING (true);

-- 策略 B：允许所有人（或特定管理员）执行 upsert 操作
-- 注意：在开发初期，为了方便管理，这里先允许通过 Service Role 或简单策略写入
CREATE POLICY "Allow management for photoshoot_styles" 
ON photoshoot_styles FOR ALL USING (true);


-- 2. 为 profiles 表增加管理员权限标识
-- 如果该表不存在，请确保先运行基础 schema.sql
ALTER TABLE IF EXISTS profiles 
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;

-- 3. (可选) 将特定用户设置为管理员示例
-- 请将 'YOUR_USER_ID' 替换为 Supabase Auth 中的真实 UUID
-- UPDATE profiles SET is_admin = true WHERE id = 'YOUR_USER_ID';

COMMENT ON TABLE photoshoot_styles IS '存储 AI 时代写真风格的自定义配置，目前主要用于封面图覆盖';
COMMENT ON COLUMN profiles.is_admin IS '标识用户是否具有管理员权限，开启后台配置功能';


-- 第一步：为 profiles 表增加管理员权限列（如果已经有了会自动跳过）
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false;
