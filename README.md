# SIR · 煤炉 / 骏合屋上新监控（可插拔数据源 + 通知聚合）

本项目是**监控与通知聚合系统**：任务、关键词匹配、去重、多渠道推送、日志与统计已经实现。  
**煤炉 / 骏合屋的商品数据源尚未接入**——当前**不能**发现真实平台商品，也不会用演示数据冒充结果。

> 不会绕过 401、403、Cloudflare、登录验证或验证码。

## 两层能力请分开看

| 层级 | 状态 | 说明 |
|---|---|---|
| 监控系统（任务 / 匹配 / 去重 / 通知 / 面板） | **已实现** | 不依赖浏览器常开；Docker Compose 可部署 |
| 平台商品数据源（煤炉 / 骏合屋） | **未接入 / 待确认** | 见下方调研；可插拔接口已预留 |

## 平台与数据源调研（有依据才写结论）

### 煤炉（Mercari）

| 数据源 | 状态 | 依据摘要 |
|---|---|---|
| C2C 官方公开搜索 API | **不可用** | 公开资料表明 jp.mercari.com 无面向外部开发者的通用公开搜索 API |
| メルカリShops API | **不适用** | 官方店铺卖家 GraphQL（库存/订单），需合作合同，不是 C2C 全站关键词监控 |
| 官方「保存搜索」新着邮件 | **有官方功能；本工具读取尚未启用** | 帮助中心确认可对保存搜索开启邮件通知。规划经用户 **OAuth** 只读邮箱接入，**不保存邮箱密码** |
| 非官方第三方封装 API | **不接入** | 非官方/未授权 |

### 骏合屋（Suruga-ya）

| 数据源 | 状态 | 依据摘要 |
|---|---|---|
| 官方公开搜索 API | **待确认** | 未检索到对外开放的商品搜索 API 文档 |
| 官方「入荷お知らせ」邮件 | **有官方功能；用途不匹配关键词监控** | 针对入荷待ちリスト到货提醒；合规代读范围待确认；本工具脚手架未启用 |
| HTML 公开页抓取 | **不实现** | 云出口常 403；不绕过 WAF |

参考链接见应用内「平台接入 / 数据源」页或 `GET /api/datasources`。

## 可插拔数据源设计

统一接口：`backend/app/datasources/`（`fetch` + `capability`）。

| 类型 | ID 示例 | 说明 |
|---|---|---|
| `official_api` | `mercari.official_api` / `surugaya.official_api` | 官方或合作 API 占位 |
| `email_alert` | `mercari.email_alert` / `surugaya.email_alert` | OAuth 读官方提醒邮件（脚手架） |
| `user_provided` | `multi.user_provided` | 用户主动 `POST /api/ingest` 提交有权使用的商品 JSON |

调度器按平台尝试数据源；`unavailable` / `pending_confirmation` 会写明日志并**跳过**，返回 0 条真实新增。  
用户入库为推模式，不在调度里假装拉取成功。

### 用户入库示例（可选）

```bash
# .env 中设置 INGEST_API_TOKEN=your-secret
curl -X POST http://127.0.0.1:8000/api/ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Token: your-secret" \
  -d '{"task_id":1,"items":[{"platform":"mercari","external_id":"m123","title":"示例","url":"https://jp.mercari.com/item/m123","price":1000}]}'
```

调用方须确保对提交数据具备使用权。系统只做去重与通知聚合。

### 邮件提醒接入（规划，未启用）

1. 用户在煤炉开启「保存した検索条件の新着」邮件通知  
2. 部署方配置 `EMAIL_OAUTH_PROVIDER` / `CLIENT_ID` / `CLIENT_SECRET`（Gmail 或 Microsoft）  
3. 用户完成 OAuth，仅授予只读邮件权限；**禁止邮箱密码**  
4. 用真实邮件样本校准解析器后，方可把该数据源标为 `available`

## 已实现的监控系统功能

- 监控任务：创建 / 编辑 / 暂停 / 删除；关键词包含/排除；匹配逻辑；价格等筛选；检查间隔  
- 服务端调度、重启恢复、退避、限流、商品去重  
- 通知：Telegram / Bark / 企微 / 钉钉 / 飞书 / Email / Webhook / 微信推送（凭证加密）  
- 总览、统计、运行日志与通知日志  

## 技术栈与启动

| 组件 | 选型 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + APScheduler + SQLite |
| 前端 | Vite + React + TypeScript |
| 部署 | Docker Compose |

```bash
cp .env.example .env
docker compose up --build -d
# http://localhost:8000
```

本地开发见 `.env.example`。前端构建：`cd frontend && npm install && npm run build`。

## 旧数据兼容

历史平台枚举值仍保留在数据库模型中；调度会跳过非煤炉/骏合屋平台并记日志。新建任务仅允许这两平台。

## 未来功能

- 自动收藏 / 自动下单：不做；若将来实现须平台允许且用户明确开启  
- 官方 API / OAuth 邮件数据源在满足条件后的正式启用  
- 完整邮箱 OAuth 授权页与邮件模板金丝雀测试  

## 许可证

GPL-3.0（见 `LICENSE`）。
