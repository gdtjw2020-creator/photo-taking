-- ====================================================================
-- 001_old_photo_mvp.sql
-- 唐师傅的 AI 老照相馆 MVP - 数据库字段扩展
-- 
-- 用途：为 photoshoot_tasks 表新增 module_type、style_id、metadata 字段，
--       支持时代艺术照、暗房盲盒、照着样子拍三种 MVP 模式的任务元数据存储。
--
-- 注意：本脚本使用 IF NOT EXISTS / ADD COLUMN IF NOT EXISTS，
--       可安全重复执行，不会破坏现有数据。
-- ====================================================================

-- 1. 为 photoshoot_tasks 表新增扩展字段
ALTER TABLE public.photoshoot_tasks
  ADD COLUMN IF NOT EXISTS module_type TEXT,
  ADD COLUMN IF NOT EXISTS style_id TEXT,
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- 2. 为 module_type 添加索引，便于后续按模块类型查询（可选但推荐）
CREATE INDEX IF NOT EXISTS idx_photoshoot_tasks_module_type
  ON public.photoshoot_tasks (module_type);

-- 3. 为 module_type 添加注释
COMMENT ON COLUMN public.photoshoot_tasks.module_type IS '模块类型：classic_style / darkroom_random / reference_shoot，旧任务为 NULL';
COMMENT ON COLUMN public.photoshoot_tasks.style_id IS '风格 ID，仅 classic_style / darkroom_random 模式使用';
COMMENT ON COLUMN public.photoshoot_tasks.metadata IS '扩展元数据 JSON，包含 prompt_mode / requested_count / actual_count 等';
