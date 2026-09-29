# SIR · 煤炉 / 骏合屋上新监控

针对**煤炉（Mercari）**与**骏合屋（Suruga-ya）**的关键词上新监控与通知工具。  
本版本**不包含**雅虎日拍、PayPayフリマ、ラクマ、演示平台等其他站点入口。

**第一阶段只做提醒与商品跳转，不包含自动收藏、自动下单。**

## 技术选型

| 组件 | 选型 | 原因 |
|---|---|---|
| 后端 | Python 3.12 + FastAPI | 异步请求友好，部署简单 |
| 数据库 | SQLite（默认） | 零依赖可跑；Compose 可挂载持久卷 |
| 调度 | APScheduler（同进程） | 不依赖浏览器；任务状态落库，重启可恢复 |
| 前端 | Vite + React + TypeScript | 任务 / 商品 / 通知 / 统计面板 |
| 部署 | Docker Compose | 一键启动应用与数据卷 |

## 功能概览（MVP）

- 监控任务：创建 / 编辑 / 暂停 / 删除；多关键词；包含 / 排除；任意或全部命中；价格 / 品牌 / 型号等筛选；可配置检查间隔
- 自动监控：服务端调度、重启恢复、失败退避、并发与频率限制、商品去重
- 商品库：标题 / 价格 / 图片 / 链接 / 卖家 / 发现时间 / 匹配关键词；搜索与筛选；已读状态
- 通知：Telegram / Bark / 企业微信 / 钉钉 / 飞书 / Email / Webhook / 微信推送；凭证加密；测试发送与失败记录
- 面板：任务数、今日发现、平台分布、通知成功/失败、按天/关键词统计、运行日志

## 平台接入状态（本版本仅此两个）

| 平台 | 代码 | 状态 | 说明 |
|---|---|---|---|
| 煤炉 Mercari | `mercari` | **未接入** | 非官方 search API 现返回 401；公开搜索页受 Cloudflare 保护。无允许稳定使用的公开数据源。 |
| 骏合屋 駿河屋 | `surugaya` | **未接入** | 公开 HTML 搜索在多数云出口返回 403；无官方开放搜索 API。 |

**不会实现**：绕过登录、验证码、Cloudflare、付费墙或其他访问控制；不会用演示数据冒充真实商品；不要求用户提供平台账号密码。

### 后续接入所需条件

1. **煤炉**：官方开放搜索 API，或平台明确允许的合作数据源 → 在 `backend/app/platforms/mercari.py` 实现 `search()`，复用已有 `parse_item` / `make_external_id`，将 `status` 改为 `supported` / `partial`。
2. **骏合屋**：官方开放 API，或合规前提下可稳定访问的允许数据源 → 在 `backend/app/platforms/surugaya.py` 同样处理。

适配器与调度、通知、前端分离，可单独替换。

### 旧数据兼容

若数据库中仍有早期版本写入的其他平台商品/任务（如 `demo`、`yahoo_auctions`）：

- `PlatformCode` 枚举保留历史值，读取旧记录不会崩溃
- 调度遇到非本版本平台会**跳过并写警告日志**，不会中断整个任务循环
- 新建/编辑任务只允许选择 `mercari` / `surugaya`

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
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
mkdir -p data
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 另开终端：前端
cd frontend && npm install && npm run build
# 或 npm run dev（开发代理 /api → :8000）
```

## 环境变量

见 [`.env.example`](.env.example)。通知凭证通过面板写入数据库并用 Fernet 加密，**不要硬编码密钥**。

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 目录结构

```
backend/app/
  api/            # REST API
  models/         # SQLAlchemy 模型
  platforms/      # mercari.py / surugaya.py（独立适配器）
  notifications/  # 通知渠道适配器
  scheduler/      # 后台定时调度
  services/       # 监控去重、加密等
frontend/         # React 面板
docker-compose.yml
Dockerfile
```

## 未来功能（未实现）

- **自动收藏 / 自动下单**：不属于 MVP；若将来实现须先确认平台允许并由用户明确开启
- 煤炉 / 骏合屋在获得允许数据源后的正式抓取接入
- 多用户认证；PostgreSQL 生产配置与 Alembic 精细迁移

## 合规建议

- 仅用于个人监控提醒；遵守各平台服务条款
- 接入后请控制检查间隔（建议 ≥ 60–120 秒）
- 出站请求使用可识别 User-Agent，不伪装浏览器以绕过限制

## 许可证

本仓库根目录为 GPL-3.0（见 `LICENSE`）。
