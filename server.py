from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from app.models import Action, ResetResult, StepResult, StateResult
from app.env import EmailTriageEnv
from app.tasks import TASKS

app = FastAPI(title="Email Triage OpenEnv")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
env = EmailTriageEnv()

@app.post("/reset", response_model=ResetResult)
async def reset(data: Optional[Dict[str, Any]] = Body(None)):
    task_id = data.get("task_id") if data else None
    try:
        return env.reset(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step", response_model=StepResult)
async def step(action: Action):
    return env.step(action)

@app.get("/state", response_model=StateResult)
async def get_state():
    return env.state()

@app.get("/tasks")
async def get_tasks():
    return {tid: task["description"] for tid, task in TASKS.items()}

@app.get("/health")
async def health():
    return {"status": "ok"}
