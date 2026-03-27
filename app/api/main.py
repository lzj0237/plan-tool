from fastapi import FastAPI

from app.api.routers import auth, executions, reports, reschedule, tasks

app = FastAPI(title="PlanPilot", version="0.5.0")


@app.get("/health")
def health():
    return {"status": "ok"}


# 认证路由使用 /api/auth 前缀
app.include_router(auth, prefix="/api/auth")
# 其他路由使用 /api 前缀
app.include_router(tasks, prefix="/api")
app.include_router(executions, prefix="/api")
app.include_router(reschedule, prefix="/api")
app.include_router(reports, prefix="/api")
