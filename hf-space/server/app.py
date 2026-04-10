# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi",
#     "uvicorn[standard]",
#     "pydantic",
#     "openai",
#     "requests",
# ]
# ///

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from server.models import Action, ResetResult, StepResult, StateResult
from server.env import EmailTriageEnv
from server.tasks import TASKS

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

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()

