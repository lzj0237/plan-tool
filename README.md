# PlanPilot(计划/排程/提醒/总结)

目标:一个面向个人/多人使用的计划工具,支持:
- 事项(计划日期、计划时间段、预计时长)
- 执行明细(开始/暂停/结束自动计时,可多段)
- 监督提醒(邮件,可配置频率;默认每日一次)
- 冲突自动顺延(按小时顺延;支持插入事项后其他事项自动顺延;记录顺延原因,支持叠加记录)
- 总结(周/月:各事项耗时统计,完成/未完成分开,明细可追溯)

## 技术栈(MVP)
- FastAPI + SQLAlchemy + Alembic
- Postgres
- Redis + Celery + Celery Beat
- 邮件:SMTP(QQ邮箱)
- 部署:docker-compose

## 快速开始(本地)

启动:
```bash
docker compose up -d
```

API:<http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

最小流程(创建→开始→暂停→继续→结束):
```bash
# 1) 创建任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"写 PlanPilot v0.1"}'

# 假设返回 id=1
# 2) 开始
curl -X POST http://localhost:8000/api/tasks/1/start

# 3) 暂停
curl -X POST http://localhost:8000/api/tasks/1/pause

# 4) 继续
curl -X POST http://localhost:8000/api/tasks/1/resume

# 5) 结束
curl -X POST http://localhost:8000/api/tasks/1/stop

# 查询任务
curl http://localhost:8000/api/tasks/1
```

## 开发里程碑
- v0.1:事项CRUD + 执行记录计时(单人)
- v0.2:顺延算法 + 顺延原因日志(分钟粒度;支持固定时间段任务;跨天顺延)
- v0.3:邮件提醒 + 定时任务(✅ 已完成)
- v0.4:周/月报导出 + API端点(✅ 已完成)
- v0.5:多用户/租户 + 权限(✅ 已完成)

## v0.2（顺延）说明

### 规则（当前实现）
- **分钟粒度**：不再限制"按小时"，顺延按分钟保持原任务时长。
- **跨天**：如果顺延导致超出当天 24:00，会自动滚到下一天继续排。
- **固定时间段任务（is_fixed）**：
  - 用户可将某些任务标记为 `is_fixed=true` 表示不可移动。
  - 当顺延遇到固定块冲突时，会继续把可移动任务往后推，直到避开固定块。

### API
- `POST /api/reschedule/run`

请求体：
```json
{
  "planned_date": "2026-03-26",
  "inserted_task_id": 1,
  "reason": "insert task"
}
```

返回：
```json
{
  "updated_task_ids": [2,3,4],
  "logs_created": 3
}
```

## v0.3（邮件提醒）说明

### 配置邮件

在 `docker-compose.yml` 中配置SMTP：

```yaml
environment:
  MAIL_ENABLED: "true"           # 启用邮件
  MAIL_TO: "your_email@qq.com"  # 收件人
  MAIL_FROM: "PlanPilot <your_email@qq.com>"
  MAIL_SMTP_HOST: "smtp.qq.com"
  MAIL_SMTP_PORT: "587"
  MAIL_USERNAME: "your_email@qq.com"
  MAIL_PASSWORD: "your_smtp_password"
```

**注意**：QQ邮箱需要使用"授权码"而不是QQ密码。

### 定时任务

- **每日摘要**：每天09:00自动发送当日任务清单（默认）
- **Celery Beat**：配置在 `docker-compose.yml` 的 `REMIND_CRON`

### API

获取任务统计：
```bash
curl http://localhost:8000/api/reports/summary?start_date=2026-03-01&end_date=2026-03-31
```

生成周报：
```bash
curl "http://localhost:8000/api/reports/weekly?week_start=2026-03-22&week_end=2026-03-28&email_to=your_email@qq.com"
```

生成月报：
```bash
curl "http://localhost:8000/api/reports/monthly?month=2026-03&email_to=your_email@qq.com"
```

## v0.4（周/月报导出）说明

### 功能

- **周报**：显示指定周内的任务，按天分组，包含统计信息
- **月报**：显示指定月份的任务，包含所有周的详细信息
- **统计**：总任务数、已完成、待处理、预计时长
- **邮件发送**：支持直接通过API发送报告到指定邮箱

### 报告格式

报告以纯文本和HTML两种格式提供：
- 纯文本：适合终端查看或简单文本编辑器
- HTML：支持样式和格式，适合邮件查看

### API

#### 1. 获取任务统计
```bash
GET /api/reports/summary?start_date=2026-03-01&end_date=2026-03-31
```

#### 2. 生成周报
```bash
GET /api/reports/weekly?week_start=2026-03-22&week_end=2026-03-28&email_to=your_email@qq.com
```

#### 3. 生成月报
```bash
GET /api/reports/monthly?month=2026-03&email_to=your_email@qq.com
```

参数说明：
- `week_start`, `week_end`: 日期范围（YYYY-MM-DD）
- `month`: 月份（YYYY-MM）
- `email_to`: 可选，发送报告的邮箱地址

### 示例

```bash
# 查看本周报告
curl "http://localhost:8000/api/reports/weekly?week_start=2026-03-22&week_end=2026-03-28"

# 发送报告到邮箱
curl "http://localhost:8000/api/reports/monthly?month=2026-03&email_to=your_email@qq.com&subject=3月份工作报告"
```

## v0.5（多用户/租户+权限）说明

### 核心概念

1. **租户(Tenant)**
   - 数据隔离的单位，每个租户拥有独立的空间
   - 租户内所有数据通过 `tenant_id` 关联
   - 个人用户：每个用户创建一个私人租户
   - 团队/企业：多个成员共享一个租户

2. **用户(User)**
   - 通过邮箱和密码注册/登录
   - 每个用户属于一个租户
   - 拥有角色权限：`admin`(管理员) 或 `member`(普通成员)

3. **认证方式**
   - 使用JWT Bearer Token
   - 登录成功后获得 `access_token`
   - 后续请求通过 Header 携带：`Authorization: Bearer <token>`

### 认证API

#### 1. 注册
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "full_name": "张三",
    "tenant_name": "我的团队"
  }'
```

响应：
```json
{
  "user_id": 1,
  "tenant_id": 1,
  "email": "user@example.com",
  "full_name": "张三",
  "message": "注册成功"
}
```

#### 2. 登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "full_name": "张三",
  "role": "admin"
}
```

#### 3. 获取当前用户信息
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 权限规则

| 操作 | admin | member |
|------|-------|--------|
| 查看所有租户任务 | ✅ | ❌ 只能看自己的 |
| 创建任务 | ✅ | ✅ |
| 修改任务 | ✅ 所有 | ❌ 只能修改自己的 |
| 删除任务 | ✅ 所有 | ❌ 只能删除自己的 |
| 查看执行记录 | ✅ 所有 | ❌ 只能看自己的 |
| 管理租户成员 | ✅ | ❌ |

### 数据模型变更

任务表新增字段：
- `tenant_id`: 所属租户ID
- `user_id`: 创建者用户ID

所有查询自动按 `tenant_id` 隔离，确保数据安全。

### 安全建议

1. **修改SECRET_KEY**：生产环境务必使用复杂的随机字符串
   ```yaml
   SECRET_KEY: your-super-secret-key-here-change-me
   ```

2. **使用HTTPS**：生产环境务必启用HTTPS

3. **定期更换密码**：建议用户定期更换密码

4. **邮件配置**：启用邮件功能可发送密码重置等安全邮件
