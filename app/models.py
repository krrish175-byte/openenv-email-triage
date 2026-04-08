from typing import Optional, Dict, List, Any
from pydantic import BaseModel, ConfigDict

class Email(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    subject: str
    body: str
    sender: str
    timestamp: str
    thread_id: Optional[str] = None

class Observation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    task_description: str
    current_email: Email
    inbox_remaining: int
    step_number: int
    max_steps: int
    last_action_result: Optional[str] = None
    context: Dict[str, Any] = {}

class Action(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    action_type: str  # categorize, prioritize, respond, archive, escalate, skip
    category: Optional[str] = None  # work, personal, spam, newsletter, support, billing
    priority: Optional[str] = None  # urgent, high, normal, low
    response_text: Optional[str] = None
    reasoning: Optional[str] = None

class Reward(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    value: float
    partial_scores: Dict[str, float]
    message: str

class StepResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]

class ResetResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    observation: Observation

class StateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    step_number: int
    done: bool
    cumulative_reward: float
    episode_id: str
    emails_processed: int
