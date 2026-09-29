# SIR · 日本二手商品多平台上新监控

关键词监控日本二手平台上新，并通过 Telegram / Bark / 企业微信 / 钉钉 / 飞书 / Email / Webhook / 微信推送等渠道提醒。  
**第一阶段只做提醒与商品跳转，不包含自动收藏、自动下单。**

## 技术选型

| 组件 | 选型 | 原因 |
|---|---|---|
| 后端 | Python 3.12 + FastAPI | 异步请求友好，部署简单 |
| 数据库 | SQLite（默认） | 零依赖可跑；Compose 可挂载持久卷 |
| 调度 | APScheduler（同进程） | 不依赖浏览器；任务状态落库，重启可恢复 |
| 前端 | Vite + React + TypeScript | 任务 / 商品 / 通知 / 统计面板 |
| 部署 | Docker Compose | 一键启动应用与数据卷 |

项目初始为空仓库，因此采用上述简洁、易部署的栈。

## 功能概览（MVP）

- 监控任务：创建 / 编辑 / 暂停 / 删除；多关键词；包含 / 排除；任意或全部命中；价格 / 品牌 / 型号 / 分类 / 卖家 / 状态筛选；可配置检查间隔
- 自动监控：服务端调度、重启恢复、失败退避、并发与频率限制、商品去重、记录首次发现时间与来源平台
- 商品库：标题 / 价格 / 图片 / 链接 / 卖家 / 发布时间 / 发现时间 / 匹配关键词；搜索与筛选；已读状态
- 通知：统一接口 + 多渠道适配器；凭证加密存储；测试发送；失败重试与发送记录（按渠道+商品+任务去重）
- 面板：任务数、今日发现、平台分布、通知成功/失败、按天/平台/关键词统计、运行日志

## 平台接入状态

| 平台 | 代码 | 状态 | 数据来源 | 说明 |
|---|---|---|---|---|
| 雅虎日拍 | `yahoo_auctions` | **partial** | 公开 HTML 搜索页 | 已实现解析；页面改版需维护；请控制频率 |
| 演示平台 | `demo` | **supported** | 本地合成数据 | 默认开启，用于离线联调全流程 |
| 煤炉 Mercari | `mercari` | **stub** | 非官方 API 现 401；公开页受 Cloudflare 保护 | 占位 + 解析辅助；不绕过访问控制 |
| 骏合屋 駿河屋 | `surugaya` | **stub** | 公开 HTML 在多数云出口 403 | 占位适配器 |
| 闪电市场 PayPayフリマ | `paypay_fleamarket` | **stub** | 无稳定公开官方搜索 API | 占位适配器 + 接入说明 |
| 乐天二手 ラクマ | `rakuma` | **stub** | 无稳定公开官方搜索 API | 占位适配器 |
| 雅虎闲置 | `yahoo_fleamarket` | **stub** | 业务已并入 PayPayフリマ | 历史兼容占位 |

**不会实现**：绕过登录、验证码、付费墙或其他访问控制；不会要求用户提供平台账号密码。

### 如何维护 / 替换某个平台适配器

1. 实现 `backend/app/platforms/base.py` 中的统一接口：`search` / `parse_item` / `make_external_id` / `capability`
2. 在 `backend/app/platforms/__init__.py` 注册
3. 保持调度、通知、前端不感知具体解析细节

## 快速启动

### 方式 A：Docker Compose（推荐）

```bash
cp .env.example .env
# 编辑 SECRET_KEY（以及可选 CREDENTIALS_FERNET_KEY）
docker compose up --build -d
```

浏览器打开：<http://localhost:8000>

### 方式 B：本地开发

```bash
# 后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
mkdir -p data
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 另开终端：前端
cd frontend && npm install && npm run dev
```

- API / 已构建前端：<http://localhost:8000>
- 前端开发：<http://localhost:5173>（已代理 `/api`）

### 首次验证（不依赖外网）

1. 打开「通知渠道」可先跳过，或配置 Telegram 等
2. 「监控任务」新建任务，关键词任意（如 `Switch`），平台勾选 **演示平台 (demo)**
3. 点击「立即检查」或等待调度
4. 在「商品」中应看到合成商品；总览与日志同步更新

## 环境变量

见 [`.env.example`](.env.example)。敏感通知凭证通过面板写入数据库，并使用 Fernet 加密；**不要把密钥硬编码进代码**。

生成 Fernet Key：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 目录结构

```
backend/app/
  api/            # REST API
  models/         # SQLAlchemy 模型
  platforms/      # 各平台适配器（独立维护）
  notifications/  # 各通知渠道适配器
  scheduler/      # 后台定时调度
  services/       # 监控去重、加密等
frontend/         # React 面板
docker-compose.yml
Dockerfile
```

## API 摘要

- `GET /api/health`
- `GET/POST /api/tasks`，`PATCH/DELETE /api/tasks/{id}`，`POST .../pause|resume|run`
- `GET /api/items`，`POST /api/items/{id}/read`
- `GET/POST /api/channels`，`POST /api/channels/{id}/test`
- `GET /api/platforms`，`GET /api/stats/dashboard`，`GET /api/stats/charts`
- `GET /api/logs/runs`，`GET /api/logs/notifications`

## 未来功能（未实现）

- **自动收藏 / 自动下单**：不属于 MVP。若将来实现，必须先确认目标平台允许，并由用户明确开启；架构上平台适配器可额外扩展动作接口，但当前刻意不提供。
- PayPayフリマ / ラクマ 在获得允许的数据源后的正式接入
- 多用户认证与权限
- PostgreSQL 生产配置与 Alembic 精细迁移

## 合规与频率建议

- 仅用于个人监控提醒；请遵守各平台服务条款与 robots 约定
- 建议检查间隔 ≥ 60 秒（骏合屋等 HTML 源建议 ≥ 120 秒）
- 本工具出站请求使用可识别的 User-Agent，不伪装成浏览器以绕过限制

## 许可证

本仓库根目录为 GPL-3.0（见 `LICENSE`）。
