from fastapi import FastAPI

from app.api.routers import executions, reschedule, tasks

app = FastAPI(title="PlanPilot", version="0.2.0")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(tasks.router, prefix="/api")
app.include_router(executions.router, prefix="/api")
app.include_router(reschedule.router, prefix="/api")
