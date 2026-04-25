# AI 女神约拍神器 - 支付方案升级计划 (低费率方案)

## 1. 背景与目标
目前系统使用的是“面包多”卡密方案，虽然实现简单，但存在以下痛点：
*   **手续费极高**：面包多服务费高达 13%，严重侵蚀利润。
*   **用户体验断层**：用户需跳出 App -> 购买卡密 -> 复制卡密 -> 回到 App 粘贴，流程过长导致流失。

**目标**：切换至类“贞贞工坊”的支付方案，实现扫码直充，费率降低至 **0.6% - 3%**。

---

## 2. 推荐平台选择

### 方案 A：支付宝当面付 (官方方案 - 强烈推荐)
*   **主体**：个人/个体户（无需营业执照也可申请小微商户）。
*   **费率**：**0.6%**。
*   **安全性**：最高。资金直接进入支付宝官方商户余额，秒到账。
*   **适用**：主要做支付宝收款的场景。

### 方案 B：三方聚合支付 (如：易支付 / 独鹿支付)
*   **主体**：个人。
*   **费率**：**1% - 3%**。
*   **安全性**：中。资金由平台代收，存在平台跑路风险（建议选老牌、每日结算的平台）。
*   **适用**：需要同时支持微信和支付宝，且不愿折腾官方接口的场景。

---

## 3. 技术架构设计

### 3.1 核心流程
1.  **用户下单**：用户在“我的”页面选择充值面额（如：13.5元 10积分）。
2.  **创建订单**：前端请求后端 `POST /api/payment/create`，后端调用支付平台 API 获取支付链接/二维码。
3.  **用户扫码**：前端显示支付二维码，用户完成支付。
4.  **支付通知 (Webhook)**：支付平台向后端 `POST /api/payment/callback` 发送异步通知。
5.  **自动加分**：后端校验签名后，根据订单金额自动给用户加积分，并记录 `credit_logs`。

### 3.2 数据库变更
新增 `payments` 表用于追踪订单状态：
```sql
CREATE TABLE public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    order_no TEXT UNIQUE NOT NULL, -- 系统内部订单号
    platform_no TEXT,              -- 支付平台订单号
    amount FLOAT NOT NULL,
    credits FLOAT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, paid, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    paid_at TIMESTAMP WITH TIME ZONE
);
```

---

## 4. 实施清单 (待对接)

### 后端 (Python/FastAPI)
- [ ] 集成支付 SDK (如：alipay-sdk-python 或通用易支付 SDK)。
- [ ] 开发订单创建接口 `create_order`。
- [ ] 开发支付回调处理接口 `handle_callback` (核心是签名校验)。
- [ ] 实现支付后的 WebSocket 或前端轮询，用于实时刷新页面余额。

### 前端 (Vue3)
- [ ] 在“我的”页面增加“充值中心”模块，展示价格档位。
- [ ] 增加支付确认弹窗，显示支付二维码及倒计时。
- [ ] 支付成功后自动刷新用户个人资料。

---

## 5. 提示
当你休息好准备对接时，请提供：
1. 你选择的支付平台名称。
2. 该平台的 `AppID`、`AppSecret` 或 `商户ID/密钥`。
3. 支付平台的 API 文档链接。

我将负责后续的全套自动化集成。
