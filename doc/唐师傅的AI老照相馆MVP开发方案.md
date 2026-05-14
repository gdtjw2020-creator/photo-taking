# 唐师傅的 AI 老照相馆 MVP 开发方案

## 1. MVP 目标

第一版目标不是完整实现原方案里的所有高级能力，而是用现有项目能力快速上线一个可体验、可付费、可分享的 H5 产品。

核心判断：

- 主力使用 `gpt-image-2` 官方图像接口。
- 先依赖模型自身的人脸一致性、参考图理解能力和图像编辑能力。
- 第一版不做人脸检测、姿态估计、复杂内容审核、多人协作房间。
- 重点投入在风格模板、提示词、前端包装、等待体验、结果展示和相册留存。

MVP 成功标准：

- 用户上传 1 张清晰人脸照后，可以稳定生成“像本人”的年代艺术照。
- 用户能快速理解玩法，3 步内开始生成。
- 生成结果能保存、下载、进入相册。
- 整体品牌感从“AI 女神约拍神器”切换为“唐师傅的 AI 老照相馆”。
- 后续可以平滑扩展全家福、衣帽间、更多风格和分享海报。

## 2. 首期功能范围

### 2.1 开放模块

首期只开放 3 个模块：

1. 时代艺术照
2. 暗房盲盒
3. 照着样子拍

暂缓模块：

- 那年全家福：首期不做多人邀请房间和多人站位。
- 快换衣帽间：首期并入“时代艺术照”的风格模板，不单独做入口。

### 2.2 模块一：时代艺术照

用户流程：

1. 进入首页，点击“时代艺术照”。
2. 选择一个年代风格。
3. 上传 1 张本人或已授权的人脸照。
4. 点击“唐师傅，开拍吧”。
5. 等待生成。
6. 查看 1-3 张结果图。
7. 下载、重拍或进入相册。

首期风格建议 8 个：

- 工农兵肖像
- 港风女星
- 上海名媛
- 民国学生
- 八零迪斯科
- 革命样板戏
- 九十年代影楼风
- 老北京照相馆

每个风格配置：

- `id`
- `name`
- `description`
- `preview_url`
- `tags`
- `prompts`
- `recommended_count`

提示词原则：

- 明确用户上传图是身份参考。
- 明确保持人脸身份、五官特征、年龄气质。
- 明确年代、服装、发型、摄影棚、胶片质感。
- 避免过度改变脸型、肤色、人种和年龄。
- 输出写实照片，不要插画、卡通、过度磨皮。

示例提示词：

```text
Use the uploaded portrait as the identity reference. Create a realistic vintage Chinese photo studio portrait of this same person in 1980s Shanghai style. Preserve the person's facial identity, facial structure, age impression, and natural expression. Dress the person in an elegant qipao, soft warm studio lighting, subtle film grain, authentic old photo texture, slightly faded colors, professional portrait photography, natural skin texture, realistic details. Do not change the person's identity. Do not make it look like a cartoon or illustration.
```

### 2.3 模块二：暗房盲盒

用户流程：

1. 进入首页，点击“暗房盲盒”。
2. 上传 1 张人脸照。
3. 选择胶卷套餐：
   - 135 胶卷：3 张
   - 120 胶卷：6 张
   - 大画幅底片：9 张
4. 系统随机抽取不重复风格。
5. 展示暗房冲洗等待页。
6. 逐张显示生成结果。

首期实现方式：

- 不新建复杂算法。
- 后端从风格库随机抽取 `image_count` 个 prompt。
- 每张图按现有异步任务逐张生成。
- 前端复用现有轮询逻辑，包装成“正在冲洗第 N 张”。

盲盒体验文案：

- “唐师傅正在找底片...”
- “暗房安全灯亮了...”
- “显影液开始起作用了...”
- “第 N 张底片快出来了...”

### 2.4 模块三：照着样子拍

对应原方案的“跟着名画学”，首期做简化版。

用户流程：

1. 进入首页，点击“照着样子拍”。
2. 上传参考图。
3. 上传本人或已授权的人脸照。
4. 选择模仿强度：
   - 神似就行，默认
   - 严丝合缝
   - 唐师傅自由发挥
5. 点击生成。
6. 查看结果。

首期不做：

- 参考图人脸检测
- 姿态关键点提取
- 自动裁剪多人参考图

首期只做：

- 上传参考图
- 上传人脸图
- 根据模仿强度拼接不同提示词
- 调用 `gpt-image-2` 多图编辑

示例提示词：

```text
The first uploaded image is the target reference for composition, pose, clothing style, lighting, background, and visual mood. The second uploaded image is the identity reference. Create a realistic photo of the same person from the identity reference, following the reference image's overall composition and atmosphere. Preserve the person's facial identity and natural features. Make the final image photorealistic, coherent, and historically styled. Avoid distortion, avoid cartoon style, avoid changing the person's identity.
```

## 3. 产品结构

### 3.1 首页

首页改为“唐师傅的 AI 老照相馆”。

首屏内容：

- 品牌标题：唐师傅的 AI 老照相馆
- 副标题：一张照片，回到旧时光
- 三个主入口：
  - 时代艺术照
  - 暗房盲盒
  - 照着样子拍

首页不做长营销页，直接让用户进入功能。

### 3.2 生成页

可以在现有 `GenerateView.vue` 基础上改造。

需要支持 3 种模式：

- `classic_style`：时代艺术照
- `darkroom_random`：暗房盲盒
- `reference_shoot`：照着样子拍

页面通用结构：

1. 选择玩法或风格
2. 上传照片
3. 确认合规和积分消耗
4. 提交任务
5. 等待生成
6. 查看结果

### 3.3 结果页

首期不单独做复杂分享海报，只做轻量结果区：

- 图片网格
- 单张下载
- 全部下载
- 再拍一组
- 进入我的相册

后续再扩展“取片单海报”。

### 3.4 相册

复用现有相册。

需要补充：

- 按模块显示来源，如“时代艺术照”“暗房盲盒”“照着样子拍”。
- 后续可按风格筛选。

## 4. 技术实现方案

### 4.1 现有能力复用

当前项目已有能力：

- Vue 3 + Vite H5 前端
- FastAPI 后端
- Supabase 用户、任务、模板、积分
- R2 图片存储
- 图片上传
- 异步生成任务
- 任务轮询
- 相册
- 下载代理
- `gpt-image-2` 图像生成/编辑调用

因此 MVP 不需要重建架构。

### 4.2 后端改造

建议改造 `PhotoshootRequest`：

```python
class PhotoshootRequest(BaseModel):
    module_type: Optional[str] = None
    style_id: Optional[str] = None
    template_id: Optional[str] = None
    image_url: Optional[str] = None
    reference_image_urls: Optional[List[str]] = None
    image_count: Optional[int] = 1
    prompt_mode: Optional[str] = None
    quality: str = AI_IMAGE_QUALITY
    size: str = AI_IMAGE_SIZE
    watermark: bool = True
```

新增逻辑：

- `classic_style`：根据 `style_id` 读取固定风格 prompt。
- `darkroom_random`：从风格库随机抽取 prompt。
- `reference_shoot`：用参考图和人脸图生成，多图编辑。

可以先用 Python 配置文件维护风格库，后续再迁移到 Supabase。

建议新增：

- `backend/app/services/style_prompts.py`
- 或 `backend/app/data/old_photo_styles.py`

### 4.3 数据库改造

首期最小改造：

给 `photoshoot_tasks` 增加字段：

```sql
ALTER TABLE public.photoshoot_tasks
ADD COLUMN IF NOT EXISTS module_type TEXT,
ADD COLUMN IF NOT EXISTS style_id TEXT,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
```

用途：

- `module_type`：区分时代艺术照、暗房盲盒、照着样子拍。
- `style_id`：记录生成风格。
- `metadata`：存储风格名、参考图、模仿强度等扩展信息。

首期不新增：

- 合照房间表
- 站位表
- 邀请表
- 成就表

### 4.4 前端改造

建议新增或改造页面：

- 改造 `HomeView.vue`：品牌和三个入口。
- 改造 `GenerateView.vue`：根据 query 参数或路由参数切换模式。
- 改造 `GalleryView.vue`：展示模块来源。

路由建议：

- `/generate?mode=classic_style`
- `/generate?mode=darkroom_random`
- `/generate?mode=reference_shoot`

也可以拆成：

- `/old-photo`
- `/darkroom`
- `/reference-shoot`

考虑 MVP 成本，建议先用同一个 `GenerateView.vue` 承载多个模式。

### 4.5 AI 调用策略

时代艺术照：

- 输入：人脸图
- 调用：`images.edit`
- prompt：风格 prompt + 身份保持约束

暗房盲盒：

- 输入：人脸图
- 调用：多次 `images.edit`
- prompt：随机风格 prompt

照着样子拍：

- 输入：参考图 + 人脸图
- 调用：`images.edit`
- prompt：参考图约束 + 身份保持约束 + 模仿强度

多图顺序约定：

- 参考图在前
- 人脸图在后

后端提示词必须明确：

- first image = target scene/reference
- second image = identity reference

## 5. 首期不做的功能

为了控制成本，以下功能首期不做：

- 人脸检测
- 人脸质量评分
- 姿态估计
- 性别识别
- 年龄识别
- NSFW 自动审核
- 多人合照房间
- 微信 JS-SDK 分享
- 复杂海报编辑器
- 成就系统
- 风格收集系统
- 支付渠道深度集成

保留的最低合规措施：

- 上传前展示授权确认。
- 默认加“AI生成”水印。
- 明确禁止上传未授权照片和违规内容。
- 失败时给出重试提示。

## 6. 风格提示词设计规范

每个 prompt 应包含 6 类信息：

1. 身份保持
2. 年代背景
3. 服装发型
4. 摄影风格
5. 画面质量
6. 禁止项

基础模板：

```text
Use the uploaded portrait as the identity reference. Generate a realistic vintage photo of the same person. Preserve the person's facial identity, facial structure, age impression, and natural expression.

Style: [年代/场景/服装/发型/背景].

Photography: realistic Chinese old photo studio portrait, authentic film grain, natural skin texture, coherent lighting, professional composition.

Avoid: changing identity, changing ethnicity, making the face look like another person, cartoon, illustration, plastic skin, distorted hands, distorted face, extra people, text artifacts.
```

## 7. 开发步骤

### 第一步：品牌和入口改造

- 首页改名为“唐师傅的 AI 老照相馆”。
- 增加三个入口卡片。
- 每个入口跳转到同一个生成页并带 `mode` 参数。

### 第二步：风格库和 prompt 配置

- 新增老照片风格配置文件。
- 先配置 8 个时代艺术照风格。
- 为暗房盲盒复用同一批风格。

### 第三步：后端生成接口扩展

- `PhotoshootRequest` 增加 `module_type`、`style_id`、`prompt_mode`。
- 生成任务根据模式选择 prompt。
- 记录 `module_type` 和 `style_id`。

### 第四步：生成页模式化

- `classic_style` 显示风格选择。
- `darkroom_random` 显示胶卷套餐。
- `reference_shoot` 显示参考图上传和模仿强度。
- 文案改为唐师傅风格。

### 第五步：等待和结果体验

- 等待文案改成暗房冲洗。
- 逐张生成时显示“第 N 张冲洗完成”。
- 结果按钮改成“取片”“再拍一组”。

### 第六步：相册分类

- 相册显示模块来源。
- 后续再加风格名筛选。

## 8. 验收标准

### 时代艺术照

- 可以选择 8 个风格之一。
- 上传 1 张人脸照后能提交生成。
- 能生成至少 1 张结果图。
- 结果能下载并进入相册。

### 暗房盲盒

- 可以选择 3/6/9 张套餐。
- 后端随机选择不重复风格。
- 结果逐张返回并展示。

### 照着样子拍

- 可以上传参考图和人脸图。
- 可以选择模仿强度。
- 后端按不同强度拼接不同 prompt。
- 能生成参考图风格明显、身份尽量一致的图片。

### 通用

- 余额不足时能拦截。
- 生成失败时能显示错误。
- 刷新页面后能恢复活跃任务。
- 移动端页面可用。

## 9. 后续扩展路线

MVP 验证后，再按数据决定扩展顺序：

1. 取片单分享海报
2. 更多年代风格
3. 微信分享能力
4. 简版全家福
5. 多人邀请房间
6. 人脸质量检测
7. 内容审核
8. 成就和风格收集

建议优先看这些指标：

- 首页到生成页点击率
- 上传完成率
- 提交生成率
- 生成成功率
- 下载率
- 重拍率
- 单用户平均生成张数
- 付费转化率

## 10. 总结

第一版可以轻量实现。

核心不是堆算法，而是利用 `gpt-image-2` 的多图理解和身份保持能力，把现有项目包装成一个清晰、有记忆点、能分享的垂直 AI 写真产品。

建议 MVP 只做：

- 时代艺术照
- 暗房盲盒
- 照着样子拍

暂缓：

- 全家福多人协作
- 姿态估计
- 人脸检测
- 复杂审核
- 成就系统

这样可以把开发重点集中在提示词、风格库、体验包装和生成稳定性上，用最小成本验证“唐师傅的 AI 老照相馆”是否值得继续投入。
