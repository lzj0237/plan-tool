# PlanPilot（计划/排程/提醒/总结）

目标：一个面向个人/多人使用的计划工具，支持：
- 事项（计划日期、计划时间段、预计时长）
- 执行明细（开始/暂停/结束自动计时，可多段）
- 监督提醒（邮件，可配置频率；默认每日一次）
- 冲突自动顺延（按小时顺延；支持插入事项后其他事项自动顺延；记录顺延原因，支持叠加记录）
- 总结（周/月：各事项耗时统计，完成/未完成分开，明细可追溯）

## 技术栈（MVP）
- FastAPI + SQLAlchemy + Alembic
- Postgres
- Redis + Celery + Celery Beat
- 邮件：SMTP（QQ邮箱）
- 部署：docker-compose

## 快速开始（本地）

启动：
```bash
docker compose up -d
```

API：<http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

最小流程（创建→开始→暂停→继续→结束）：
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
- v0.1：事项CRUD + 执行记录计时（单人）
- v0.2：顺延算法 + 顺延原因日志（分钟粒度；支持固定时间段任务；跨天顺延）
- v0.3：邮件提醒（可配置）
- v0.4：周/月报导出（Markdown/CSV）
- v0.5：多用户/租户 + 权限

## v0.2（顺延）说明

### 规则（当前实现）
- **分钟粒度**：不再限制“按小时”，顺延按分钟保持原任务时长。
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
