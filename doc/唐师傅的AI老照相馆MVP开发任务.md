# 唐师傅的 AI 老照相馆 MVP 开发任务

## 0. 使用说明

本文档用于指导后续开发 Agent 按任务推进 MVP 实现。

开发规则：

- 每个任务必须有明确产出。
- 每个任务完成后必须更新开发日志。
- 只有开发日志中记录了验收结果，任务才算通过。
- 遇到实现偏差、模型效果问题、接口坑、样式坑，必须写入开发日志。
- 不要一次性重构无关代码，优先复用现有项目能力。

关联文档：

- MVP 方案：[唐师傅的AI老照相馆MVP开发方案.md](./唐师傅的AI老照相馆MVP开发方案.md)
- 开发日志：[唐师傅的AI老照相馆MVP开发日志.md](./唐师傅的AI老照相馆MVP开发日志.md)

## 1. 总体任务拆分

| 任务 ID | 任务名称 | 优先级 | 状态 | 依赖 |
|---|---|---:|---|---|
| T01 | 品牌与首页入口改造 | P0 | 已通过 | 无 |
| T02 | 老照片风格库与提示词配置 | P0 | 已通过 | 无 |
| T03 | 后端生成请求模型扩展 | P0 | 已通过 | T02 |
| T04 | 数据库字段扩展脚本 | P0 | 已通过 | 无 |
| T05 | 时代艺术照模式 | P0 | 已通过 | T01, T02, T03 |
| T06 | 暗房盲盒模式 | P0 | 已通过 | T03 |
| T07 | 照着样子拍模式 | P0 | 已通过 | T03 |
| T08 | 等待页与结果区唐师傅包装 | P1 | 已通过 | T05, T06, T07 |
| T09 | 相册模块来源展示 | P1 | 已通过 | T03, T04 |
| T10 | 基础验收与回归测试 | P0 | 已通过 | T01-T09 |

## 2. 任务详情

## T01 品牌与首页入口改造

### 目标

将现有首页从“AI 女神约拍神器”调整为“唐师傅的 AI 老照相馆”，并提供 3 个 MVP 功能入口。

### 涉及文件

- `frontend/src/views/HomeView.vue`
- 如有必要，调整 `frontend/src/assets/main.css`
- 如有必要，调整 `frontend/src/router/index.js`

### 实现细节

1. 首页标题改为“唐师傅的 AI 老照相馆”。
2. 副标题改为“一张照片，回到旧时光”。
3. 删除或弱化现有“女神约拍”营销文案。
4. 增加 3 个入口：
   - 时代艺术照：跳转 `/generate?mode=classic_style`
   - 暗房盲盒：跳转 `/generate?mode=darkroom_random`
   - 照着样子拍：跳转 `/generate?mode=reference_shoot`
5. 首页首屏直接展示入口，不做长营销页。
6. 移动端入口卡片不得溢出或重叠。

### 验收标准

- 首页不再出现“AI 女神约拍神器”主品牌文案。
- 三个入口点击后能进入生成页，并携带正确 `mode`。
- 移动端和桌面端布局正常。
- 无控制台明显报错。

### 开发日志要求

完成后在开发日志记录：

- 修改文件
- 路由验证结果
- 移动端布局检查结果
- 是否通过验收

## T02 老照片风格库与提示词配置

### 目标

新增老照片风格库，供时代艺术照和暗房盲盒复用。

### 涉及文件

- 建议新增 `backend/app/data/old_photo_styles.py`
- 如需包初始化，新增或检查 `backend/app/data/__init__.py`

### 实现细节

1. 新增 `OLD_PHOTO_STYLES` 配置。
2. 首期至少包含 8 个风格：
   - `worker_soldier_portrait`：工农兵肖像
   - `hong_kong_star`：港风女星
   - `shanghai_lady`：上海名媛
   - `republic_student`：民国学生
   - `disco_80s`：八零迪斯科
   - `model_opera`：革命样板戏
   - `studio_90s`：九十年代影楼风
   - `beijing_photo_studio`：老北京照相馆
3. 每个风格包含：
   - `id`
   - `name`
   - `description`
   - `preview_url`
   - `tags`
   - `prompts`
   - `recommended_count`
4. 每个风格至少 2 条 prompt。
5. prompt 必须包含身份保持、年代风格、写实摄影、禁止项。
6. `preview_url` 可以先使用远程占位图或空字符串，但前端必须能兜底显示。

### 验收标准

- 后端能正常导入风格库，无 import error。
- 风格数量不少于 8 个。
- 每个风格至少 2 条 prompt。
- prompt 中明确包含 identity reference / preserve identity 等身份保持约束。

### 开发日志要求

完成后在开发日志记录：

- 风格数量
- 是否通过导入检查
- 是否有缺失字段
- prompt 设计备注

## T03 后端生成请求模型扩展

### 目标

扩展生成接口，使其支持 3 种 MVP 模式。

### 涉及文件

- `backend/app/routers/photoshoot.py`
- `backend/app/services/supabase_service.py`
- `backend/app/data/old_photo_styles.py`

### 实现细节

1. 扩展 `PhotoshootRequest`：

```python
module_type: Optional[str] = None
style_id: Optional[str] = None
prompt_mode: Optional[str] = None
```

2. 支持 `module_type`：
   - `classic_style`
   - `darkroom_random`
   - `reference_shoot`
3. `classic_style`：
   - 根据 `style_id` 查找风格。
   - 从该风格 prompts 中按 `image_count` 选择 prompt。
4. `darkroom_random`：
   - 从所有风格中随机抽取不重复风格。
   - 每个风格抽 1 条 prompt。
   - `image_count` 限制为 3、6、9 之一，后端可做兜底 clamp。
5. `reference_shoot`：
   - 要求 `image_url` 和至少 1 张 `reference_image_urls`。
   - 根据 `prompt_mode` 拼接不同模仿强度：
     - `similar`
     - `strict`
     - `creative`
6. 保留现有旧模板逻辑作为兼容兜底。
7. 任务创建时传入 `module_type`、`style_id`、`metadata`。

### 验收标准

- 旧的模板生成请求仍可用。
- `classic_style` 请求能生成 selected_prompts。
- `darkroom_random` 请求能生成不重复风格 prompt。
- `reference_shoot` 请求能正确使用参考图 prompt。
- 非法 `style_id` 返回清晰错误或使用兜底风格。
- 非法 `module_type` 不导致 500。

### 开发日志要求

完成后在开发日志记录：

- 接口请求示例
- 三种模式的 prompt 选择结果
- 是否保持旧逻辑兼容
- 异常参数测试结果

## T04 数据库字段扩展脚本

### 目标

为任务记录增加模块来源和扩展元数据，支持相册分类和后续扩展。

### 涉及文件

- `doc/schema.sql`
- 可选新增 `doc/migrations/old_photo_mvp.sql`

### 实现细节

给 `photoshoot_tasks` 增加字段：

```sql
ALTER TABLE public.photoshoot_tasks
ADD COLUMN IF NOT EXISTS module_type TEXT,
ADD COLUMN IF NOT EXISTS style_id TEXT,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
```

如项目没有 migrations 目录，可以新增：

- `doc/migrations/001_old_photo_mvp.sql`

并在 `schema.sql` 中同步最终结构。

### 验收标准

- SQL 可重复执行。
- 不破坏现有表结构。
- `photoshoot_tasks` 可保存 `module_type`、`style_id`、`metadata`。

### 开发日志要求

完成后在开发日志记录：

- SQL 文件路径
- 是否已同步 `schema.sql`
- 是否实际执行数据库迁移
- 如未执行，明确记录“仅生成脚本，未应用到远程数据库”

## T05 时代艺术照模式

### 目标

在生成页实现“时代艺术照”完整 MVP 流程。

### 涉及文件

- `frontend/src/views/GenerateView.vue`
- `backend/app/routers/photoshoot.py`
- `backend/app/data/old_photo_styles.py`

### 实现细节

前端：

1. 读取 `route.query.mode`。
2. 当 `mode=classic_style` 时：
   - 页面标题显示“时代艺术照”。
   - 显示老照片风格列表。
   - 用户选择风格后上传人脸照。
   - 提交 payload：

```json
{
  "module_type": "classic_style",
  "style_id": "shanghai_lady",
  "image_url": "...",
  "image_count": 1,
  "watermark": true
}
```

后端：

1. 根据 `style_id` 选择 prompt。
2. 使用现有 `ai_service.generate_images(input_url, prompt)`。

### 验收标准

- 从首页进入后默认显示时代艺术照流程。
- 能选择至少 8 个风格。
- 未选择风格或未上传照片时无法提交，并提示用户。
- 提交后能创建任务并进入轮询。
- 成功生成后结果可展示、下载、进入相册。

### 开发日志要求

完成后在开发日志记录：

- 测试使用的风格
- 提交 payload
- 任务状态流转
- 生成结果是否成功
- 验收截图或文字说明

## T06 暗房盲盒模式

### 目标

实现随机风格多张生成体验。

### 涉及文件

- `frontend/src/views/GenerateView.vue`
- `backend/app/routers/photoshoot.py`
- `backend/app/data/old_photo_styles.py`

### 实现细节

前端：

1. 当 `mode=darkroom_random` 时：
   - 页面标题显示“暗房盲盒”。
   - 不展示风格选择。
   - 展示 3 个套餐：
     - 135 胶卷：3 张
     - 120 胶卷：6 张
     - 大画幅底片：9 张
2. 用户选择套餐并上传人脸照。
3. 提交 payload：

```json
{
  "module_type": "darkroom_random",
  "image_url": "...",
  "image_count": 3,
  "watermark": true
}
```

后端：

1. 从风格库随机抽取不重复风格。
2. 每个风格抽 1 条 prompt。
3. 逐张生成。

### 验收标准

- 暗房模式不要求用户选择具体风格。
- 3/6/9 张套餐能正确计算积分。
- 后端不会抽到重复风格。
- 结果数量与套餐一致，生成失败时允许部分成功并显示结果。
- 轮询过程能逐张展示已完成图片。

### 开发日志要求

完成后在开发日志记录：

- 测试套餐
- 抽取到的风格 ID
- 生成成功张数
- 是否有失败图片
- 用户可见提示是否合理

## T07 照着样子拍模式

### 目标

实现参考图 + 人脸图的多图编辑生成。

### 涉及文件

- `frontend/src/views/GenerateView.vue`
- `backend/app/routers/photoshoot.py`
- `backend/app/services/ai_service.py`

### 实现细节

前端：

1. 当 `mode=reference_shoot` 时：
   - 页面标题显示“照着样子拍”。
   - 先上传参考图。
   - 再上传人脸图。
   - 显示模仿强度选择：
     - `similar`：神似就行，默认
     - `strict`：严丝合缝
     - `creative`：唐师傅自由发挥
2. 提交 payload：

```json
{
  "module_type": "reference_shoot",
  "prompt_mode": "similar",
  "image_url": "...",
  "reference_image_urls": ["..."],
  "image_count": 1,
  "watermark": true
}
```

后端：

1. 按 `prompt_mode` 拼接 prompt。
2. 多图顺序保持：
   - 参考图在前
   - 人脸图在后
3. 明确提示词：
   - first image = target reference
   - second image = identity reference

### 验收标准

- 未上传参考图时无法提交。
- 未上传人脸图时无法提交。
- 三种模仿强度能影响 prompt。
- 后端调用时 `ref_url` 和 `input_url` 顺序正确。
- 能生成一张参考图风格明显、身份尽量一致的图片。

### 开发日志要求

完成后在开发日志记录：

- 参考图类型
- 模仿强度
- 最终 prompt 摘要
- 生成效果主观判断
- 是否存在明显身份漂移

## T08 等待页与结果区唐师傅包装

### 目标

统一生成等待和结果展示的品牌体验。

### 涉及文件

- `frontend/src/views/GenerateView.vue`
- 如有必要，`frontend/src/assets/main.css`

### 实现细节

1. 等待文案替换为暗房冲洗风格：
   - “唐师傅正在找底片...”
   - “暗房安全灯亮了...”
   - “显影液开始起作用了...”
   - “第 N 张底片快出来了...”
2. 结果标题改为“取片成果”或“照片冲洗好了”。
3. 按钮文案：
   - 下载：取片
   - 全部下载：取走全部照片
   - 再拍一组：再找唐师傅拍一组
4. 保留现有轮询和下载逻辑。

### 验收标准

- 生成中不再出现“约拍”“写真”等明显旧品牌文案，除非兼容旧模式。
- 逐张完成提示符合唐师傅老照相馆语境。
- 结果区按钮功能正常。
- 移动端文案不挤压、不溢出。

### 开发日志要求

完成后在开发日志记录：

- 替换的主要文案
- 移动端展示检查
- 下载功能检查

## T09 相册模块来源展示

### 目标

相册中能看出照片来自哪个模块。

### 涉及文件

- `frontend/src/views/GalleryView.vue`
- `backend/app/services/supabase_service.py`
- `doc/schema.sql`

### 实现细节

1. 后端 `get_user_gallery` 返回任务原始字段即可。
2. 前端 flatten 图片时带上：
   - `module_type`
   - `style_id`
   - `metadata`
3. 图片卡片显示来源标签：
   - `classic_style`：时代艺术照
   - `darkroom_random`：暗房盲盒
   - `reference_shoot`：照着样子拍
   - 旧数据：AI 约拍
4. 不要求首期做筛选。

### 验收标准

- 新生成图片在相册中显示模块来源。
- 旧任务没有 `module_type` 时不报错。
- 删除和下载功能不受影响。

### 开发日志要求

完成后在开发日志记录：

- 新旧任务展示结果
- 删除功能检查
- 下载功能检查

## T10 基础验收与回归测试

### 目标

确认 MVP 三个模块可用，并且没有破坏原有核心流程。

### 涉及范围

- 前端构建
- 后端导入检查
- 三种模式接口请求
- 上传、生成、轮询、下载、相册

### 建议执行

根据项目环境选择：

```powershell
cd frontend
npm run build
```

```powershell
cd backend
python -m pytest
```

如测试环境缺少依赖或密钥，至少做：

- 前端构建
- Python import 检查
- 手动接口请求检查
- 浏览器手动流程检查

### 验收标准

- 前端构建通过。
- 后端核心模块可导入。
- 三个入口都能进入正确模式。
- 三种模式都能提交任务。
- 任务状态能从 processing 到 completed 或 failed。
- completed 时结果能展示并进入相册。
- failed 时错误信息可见。

### 开发日志要求

完成后在开发日志记录：

- 执行过的命令
- 命令结果摘要
- 未执行测试的原因
- 三个模块最终验收结论

## 3. 统一验收规则

任务通过必须同时满足：

1. 代码实现完成。
2. 本任务验收标准逐项检查。
3. 开发日志记录验收结果。
4. 如有未通过项，标记为“未通过”并说明原因。
5. 如存在临时绕过或技术债，记录到“遗留问题”。

## 4. 状态枚举

任务状态只能使用：

- 待开发
- 开发中
- 待验收
- 已通过
- 未通过
- 暂缓

## 5. 优先开发顺序

建议顺序：

1. T02 老照片风格库与提示词配置
2. T03 后端生成请求模型扩展
3. T04 数据库字段扩展脚本
4. T01 品牌与首页入口改造
5. T05 时代艺术照模式
6. T06 暗房盲盒模式
7. T07 照着样子拍模式
8. T08 等待页与结果区唐师傅包装
9. T09 相册模块来源展示
10. T10 基础验收与回归测试

原因：

- 先完成风格库和后端模式，前端才有稳定接口目标。
- 首页入口可以并行做，但最终要依赖生成页模式。
- 三个核心模块完成后再统一做等待页和相册体验。
