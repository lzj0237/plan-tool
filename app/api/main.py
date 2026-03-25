from fastapi import FastAPI

from app.api.routers import tasks

app = FastAPI(title="PlanPilot", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(tasks.router, prefix="/api")
