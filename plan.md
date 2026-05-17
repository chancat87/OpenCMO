# OpenCMO 免费试用平台 PRD

## 1. 背景

OpenCMO 当前更像一个共享的增长控制台：用户可以进入产品界面、创建项目、运行扫描，但系统还没有真正的账号归属、项目归属和多用户数据隔离。

下一阶段要把 OpenCMO 做成一个小规模免费试用平台：每个人都可以注册、登录，并进入自己的 OpenCMO 增长控制台，操作自己的项目，而不是看到所有人的项目。

本 PRD 暂时不包含订阅、收款、发票、退款、税务和正式商业化。第一版的目标是先验证产品使用、用户隔离和成本控制。

## 2. 产品目标

把 OpenCMO 改造成免费试用平台：

- 访客可以从首页输入一个 URL 开始。
- 访客可以注册账号并进入自己的增长控制台。
- 每个用户只能看到自己的项目、扫描、报告、审批、评论草稿和内容动作。
- 管理员可以在 `/admin` 查看整体平台数据。
- 免费试用有明确额度，避免 LLM、搜索、抓取和浏览器自动化成本失控。
- 现有生产项目不能丢，迁移时统一挂到 admin account 下。

## 3. 非目标

第一版不做：

- Stripe / Paddle / 订阅付款。
- 发票、退款、优惠码、税务处理。
- 多人团队协作和多席位计费。
- 复杂组织管理。
- 公开 marketplace。
- 自动化法律文档流转。

这些都等账号隔离和真实试用数据稳定后再做。

## 4. 用户角色

### 4.1 免费试用用户

可能是 founder、marketer、indie hacker、开发者产品操盘手或 agency operator。

核心需求：

- 快速从一个 URL 开始。
- 在一个控制台里看到 SEO、AI 搜索、SERP、海外社区机会。
- 自己的项目不被其他用户看到。
- 清楚知道免费试用额度和剩余天数。

### 4.2 管理员

OpenCMO 运营者。

核心需求：

- 查看注册用户数。
- 查看活跃试用账号。
- 查看高成本动作：扫描、报告、AI action、社区搜索。
- 发现异常和高用量账号。
- 禁用滥用账号。
- 保留现有线上项目的访问权。

## 5. 首页定位

中文首页主张：

> OpenCMO 免费试用：输入一个 URL，进入你自己的海外增长控制台。

支撑文案：

> 注册后，每个用户都会获得独立的 OpenCMO 增长控制台。你可以为自己的产品创建项目，扫描 SEO、AI 搜索、SERP、Reddit、Hacker News、X 和垂直社区，并把发现转成评论、内容和页面优化动作。

CTA：

- 主 CTA：`开始免费试用`
- 次 CTA：`前往 GitHub`
- 低优先级 CTA：`联系部署支持`

## 6. 用户流程

### 6.1 首页流程

1. 用户访问 `/zh`。
2. 首屏看到单行 URL 输入框。
3. 用户输入网站 URL。
4. 如果未登录，后续实现应跳到 `/signup?url=<encoded-url>`。
5. 注册或登录成功后进入 `/console?url=<encoded-url>`。
6. 控制台用 URL 创建或预填项目。

在 signup 功能实现前，首页 CTA 可以继续指向 `/console?url=...`，保证本地演示和现有产品链路可用。

### 6.2 注册流程

新增路由：

- `/signup`
- `/login`
- `/console`

注册字段：

- Email
- Password
- Display name，可选

注册成功后：

- 创建 `users` 记录。
- 创建个人 `accounts` 记录。
- 创建 `account_members` owner 关系。
- 创建 HttpOnly session cookie。
- 带着原始 `url` 参数跳转到 `/console`。

### 6.3 登录流程

登录字段：

- Email
- Password

登录成功后：

- 写入 session cookie。
- 返回当前 user 和 active account。
- 跳转到 `/console`。

### 6.4 控制台流程

登录后的免费试用用户只能看到：

- 自己的项目列表。
- 自己的试用状态。
- 自己的扫描、报告、审批、评论草稿。
- 自己的免费额度使用情况。

不能看到：

- 全局项目列表。
- 其他用户项目名。
- 其他用户报告。
- 其他用户审批队列。
- admin 统计。

### 6.5 管理后台流程

新增路由：

- `/admin`

管理员可以看到：

- 用户总数。
- 今日新增用户。
- 活跃试用 account。
- 项目总数。
- 今日扫描次数。
- 本月报告生成次数。
- 高用量账号。
- 最近失败任务。
- 最近注册用户。

第一版 admin action：

- 禁用账号。
- 恢复账号。
- 延长试用。
- 手动调整额度。

## 7. 免费试用策略

默认策略：

- 试用期：14 天。
- 项目上限：3 个。
- 每日扫描：3 次。
- 每月报告：10 份。
- AI chat / AI action：按 usage event 限制。

环境变量：

```bash
OPENCMO_SIGNUP_MODE=open
OPENCMO_TRIAL_DAYS=14
OPENCMO_FREE_MAX_PROJECTS=3
OPENCMO_FREE_DAILY_SCANS=3
OPENCMO_FREE_MONTHLY_REPORTS=10
OPENCMO_ADMIN_EMAIL=hello@aidcmo.com
OPENCMO_COOKIE_SECRET=replace-me
```

注册模式：

- `open`：任何人可注册。
- `invite`：需要邀请码，后续实现。
- `closed`：关闭注册。

第一版建议支持 `open` 和 `closed`，`invite` 可以第二批再做。

## 8. 数据模型

### 8.1 新增表

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'user',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free_trial',
    status TEXT NOT NULL DEFAULT 'active',
    trial_started_at TEXT NOT NULL DEFAULT (datetime('now')),
    trial_ends_at TEXT NOT NULL,
    max_projects INTEGER NOT NULL DEFAULT 3,
    daily_scan_limit INTEGER NOT NULL DEFAULT 3,
    monthly_report_limit INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE account_members (
    account_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'owner',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (account_id, user_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    user_id INTEGER,
    project_id INTEGER,
    event_type TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);
```

### 8.2 修改现有表

给 `projects` 增加归属：

```sql
ALTER TABLE projects ADD COLUMN account_id INTEGER;
CREATE INDEX idx_projects_account_id ON projects(account_id);
```

迁移策略：

1. 用 `OPENCMO_ADMIN_EMAIL` 创建 admin 用户。
2. 创建 admin account。
3. 把现有所有项目挂到 admin account。
4. 确认没有 `account_id IS NULL` 的项目。
5. 之后所有新项目都必须带 `account_id`。

## 9. 后端需求

### 9.1 认证 API

新增：

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Session 要求：

- 使用 HttpOnly cookie。
- 生产环境 cookie 必须 `Secure`。
- `SameSite=Lax`。
- session token 在 SQLite 中只存 hash。
- 默认过期时间 30 天。

密码要求：

- 使用 `argon2` 或 `bcrypt`。
- 最低 8 位。
- Email 统一转 lowercase。

### 9.2 请求上下文

每个已登录请求都要解析：

- `current_user`
- `current_account`
- `is_admin`

普通用户 API 不能从请求里接受 `account_id`。账号范围必须来自 session。

### 9.3 项目隔离

需要改造存储和服务函数：

- `list_projects(account_id)`
- `get_project(project_id, account_id)`
- `delete_project(project_id, account_id)`
- `create_project(..., account_id)`

所有 `/api/v1/projects/{project_id}/...` 路由必须先校验项目是否属于当前 account。

返回策略：

- 如果项目不属于当前用户，返回 404，避免泄露项目存在。
- admin 全局查询只能放在 `/api/v1/admin/*`。

### 9.4 用量限制

高成本动作执行前要检查额度：

- 新建项目。
- 启动扫描。
- 生成报告。
- AI chat。
- 社区搜索。
- 图谱扩展。

第一版先强制限制：

- 项目数量。
- 每日扫描次数。
- 每月报告数量。

## 10. 前端需求

### 10.1 路由

新增：

- `/signup`
- `/login`
- `/admin`

保留：

- `/console`
- `/workspace` 作为历史兼容入口，跳转到 `/console`。

### 10.2 首页

首页必须围绕免费试用平台表达：

- Hero 说明每个用户都有自己的增长控制台。
- URL 输入框仍然是第一动作。
- 主 CTA 是 `开始免费试用`。
- 产品预览展示试用额度和个人项目隔离。
- 页面解释三步：注册、创建项目、运行增长扫描。
- 明确说明数据隔离。
- 保留 GitHub / 开源证明，但不能压过免费试用 CTA。

### 10.3 控制台

控制台需要展示：

- 当前试用状态。
- 剩余天数。
- 项目额度使用情况。
- 今日扫描额度。
- 报告额度。

第一版不展示付款入口，最多预留后续升级位置。

### 10.4 管理后台

`/admin` 与普通增长控制台分离。

第一版页面：

- Summary cards。
- Recent users table。
- Recent accounts table。
- Usage table。
- Failed tasks panel。

## 11. 安全要求

必须做：

- 密码 hash。
- HttpOnly session cookie。
- cookie auth 下的 CSRF 策略。
- 注册 / 登录限流。
- admin 路由强制 role 校验。
- 普通用户 API 不接受手写 `account_id`。
- 跨 account 项目请求不泄露存在性。
- 生产迁移前备份 SQLite。

建议做：

- admin action audit log。
- account disable 开关。
- 密码重置后清理 session。
- 提高额度前要求邮箱验证。

## 12. 管理后台指标

第一版统计：

- `total_users`
- `new_users_today`
- `active_trial_accounts`
- `expired_trial_accounts`
- `total_projects`
- `projects_created_today`
- `scans_today`
- `reports_this_month`
- `high_usage_accounts`
- `failed_tasks_24h`

## 13. 迁移计划

1. 本地实现 schema migration。
2. 本地创建 admin 用户。
3. 本地把现有项目挂到 admin account。
4. 确认 admin 登录后仍能看到旧项目。
5. 确认新用户项目列表为空。
6. 确认新用户不能请求 admin 项目 ID。
7. 部署前备份 New York 的 `/opt/OpenCMO/opencmo.db`。
8. 同步代码。
9. 运行迁移。
10. 重启 `opencmo`。
11. 验证 `/zh`、`/console`、signup/login、项目创建、admin summary。

## 14. 验收标准

### 14.1 用户隔离

- A 用户创建项目后，B 用户看不到。
- B 用户请求 A 用户项目详情返回 404 或 403。
- B 用户不能对 A 用户项目触发扫描或报告。
- `/api/v1/projects` 对不同用户返回不同数据。

### 14.2 试用流程

- 新用户可以注册。
- 新用户自动获得个人 account。
- 新用户可以创建不超过免费额度的项目。
- 扫描额度会被执行。
- 控制台能看到剩余试用天数和额度。

### 14.3 管理后台

- admin 可以打开 `/admin`。
- 普通用户打不开 `/admin`。
- admin 可以看到全局统计。
- admin 可以禁用账号。

### 14.4 生产安全

- 现有项目仍然归 admin 可见。
- 没有项目丢失或孤立。
- `/workspace` 仍然跳转到 `/console`。
- 首页 CTA 可用。

## 15. 实施阶段

### Phase 1：PRD 与首页改造

- 写本 PRD。
- 首页改成免费试用平台表达。
- 保持 `/console` 可用。
- 不引入真实 auth。

### Phase 2：账号与 session

- 新增 users / accounts / account_members / sessions。
- 新增 signup / login / logout / me API。
- 新增 signup / login 页面。
- 写入 HttpOnly session cookie。

### Phase 3：项目归属

- 给 projects 加 `account_id`。
- 迁移旧项目到 admin account。
- 改造 project storage API。
- 所有 project route 做归属校验。

### Phase 4：免费额度

- 新增 usage_events。
- 限制项目、扫描、报告。
- 控制台展示试用状态。

### Phase 5：admin 后台

- 新增 `/admin`。
- 新增 admin summary API。
- 展示用户、账号和用量。

### Phase 6：生产上线

- 备份生产 DB。
- 部署代码。
- 运行迁移。
- smoke test。
- 观察日志和高成本动作。

## 16. 待确认问题

- 试用期最终是 14 天还是 30 天？
- 生产一开始是否直接 `open`，还是先用 `invite`？
- 跑扫描前是否要求邮箱验证？
- 第一批法律页面是否先做 Terms / Privacy / Security？
- 免费试用使用服务端默认 key，还是要求用户 BYOK？

## 17. 建议的第一版决策

建议第一版采用：

- `OPENCMO_SIGNUP_MODE=open`
- 14 天免费试用
- 3 个项目
- 每天 3 次扫描
- 每月 10 份报告
- 不接支付
- 不做团队成员
- 旧项目全部归 admin account

这条路径能最快把 OpenCMO 从单项目工具升级成真正的平台，同时控制数据隔离风险和运行成本。
