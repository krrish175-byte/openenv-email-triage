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
from typing import List, Dict, Any, Tuple

# ── TASK 1: EASY ──────────────────────────────────────
EMAILS_EASY = [
    {"id": "e1", "subject": "Q3 Budget Review Meeting — Thursday 3pm", "body": "Hi team, please find the attached budget review for Q3. We will meet in the conference room.", "sender": "manager@work.com", "timestamp": "2024-01-10T15:00:00Z", "correct_category": "work"},
    {"id": "e2", "subject": "Your Netflix subscription renewed", "body": "This is a confirmation that your Netflix subscription has been successfully renewed. Your card has been billed.", "sender": "billing@netflix.com", "timestamp": "2024-01-11T09:00:00Z", "correct_category": "billing"},
    {"id": "e3", "subject": "Congratulations! You've won a $500 gift card!", "body": "You have been selected as a winner! Click here to claim your $500 Amazon gift card now!", "sender": "spam@promotions.net", "timestamp": "2024-01-11T10:30:00Z", "correct_category": "spam"},
    {"id": "e4", "subject": "Weekend BBQ at my place!", "body": "Hey, I'm hosting a BBQ this Saturday afternoon. Hope you can make it! Bring some drinks.", "sender": "friend@personal.me", "timestamp": "2024-01-11T14:45:00Z", "correct_category": "personal"},
    {"id": "e5", "subject": "Weekly Product Newsletter — Issue #42", "body": "Welcome to our weekly update. In this issue, we discuss new product features and upcoming events.", "sender": "newsletter@saas.com", "timestamp": "2024-01-12T08:00:00Z", "correct_category": "newsletter"},
]

def grader_easy(actions_taken: List[dict], emails: List[dict]) -> Tuple[float, dict]:
    correct_count = 0
    processed_ids = set()
    
    for action in actions_taken:
        email_id = action.get("email_id")
        processed_ids.add(email_id)
        email = next((e for e in emails if e["id"] == email_id), None)
        if email and action.get("action_type") == "categorize":
            if action.get("category") == email.get("correct_category"):
                correct_count += 1
                
    total = len(emails)
    correct_ratio = correct_count / total
    processed_ratio = len(processed_ids) / total
    
    score = float(0.7 * correct_ratio + 0.3 * processed_ratio)
    score = max(0.01, min(0.99, score))
    
    partial_scores = {
        "correct_categorizations": correct_ratio,
        "emails_processed": processed_ratio
    }
    return score, partial_scores

# ── TASK 2: MEDIUM ────────────────────────────────────
EMAILS_MEDIUM = [
    {"id": "m1", "subject": "URGENT: Production server down — customers affected", "body": "The main database server is non-responsive. Customers are seeing 500 errors. We need to investigate and fix this immediately.", "sender": "ops@work.com", "timestamp": "2024-01-15T02:30:00Z", "correct_priority": "urgent", "requires_response": True, "keywords": ["investigating", "fix", "team", "issue", "resolve", "working"]},
    {"id": "m2", "subject": "Lunch plans?", "body": "Hey, do you want to grab lunch today at the Japanese place? Let me know.", "sender": "colleague@work.com", "timestamp": "2024-01-15T11:00:00Z", "correct_priority": "low", "requires_response": False},
    {"id": "m3", "subject": "Client contract renewal — deadline Friday", "body": "The contract with Acme Corp is up for renewal. We need to review the terms and confirm the meeting for Friday.", "sender": "sales@work.com", "timestamp": "2024-01-15T14:00:00Z", "correct_priority": "high", "requires_response": True, "keywords": ["renewal", "contract", "discuss", "meeting", "review", "confirm"]},
    {"id": "m4", "subject": "FYI: Office closed next Monday", "body": "Please note that the office will be closed next Monday for the public holiday. Have a great weekend.", "sender": "hr@work.com", "timestamp": "2024-01-16T10:00:00Z", "correct_priority": "normal", "requires_response": False},
    {"id": "m5", "subject": "Invoice #2847 overdue — 30 days", "body": "Our records show that invoice #2847 is now 30 days overdue. Please settle this amount immediately to avoid service disruption.", "sender": "billing@vendor.com", "timestamp": "2024-01-16T11:30:00Z", "correct_priority": "high", "requires_response": False},
    {"id": "m6", "subject": "Great job on the presentation!", "body": "I just wanted to say you did a fantastic job on the presentation today. The board was very impressed.", "sender": "manager@work.com", "timestamp": "2024-01-16T16:00:00Z", "correct_priority": "normal", "requires_response": False},
]

def grader_medium(actions_taken: List[dict], emails: List[dict]) -> Tuple[float, dict]:
    priority_correct = 0
    response_quality = 0.0
    processed_ids = set()
    
    emails_requiring_resp = [e for e in emails if e.get("requires_response")]
    
    for email in emails:
        email_id = email["id"]
        actions = [a for a in actions_taken if a.get("email_id") == email_id]
        if actions: processed_ids.add(email_id)
        
        # Check priority
        prio_action = next((a for a in actions if a.get("action_type") == "prioritize"), None)
        if prio_action and prio_action.get("priority") == email.get("correct_priority"):
            priority_correct += 1
            
        # Check response if required
        if email.get("requires_response"):
            resp_action = next((a for a in actions if a.get("action_type") == "respond"), None)
            if resp_action and resp_action.get("response_text"):
                text = resp_action["response_text"]
                if len(text) > 20:
                    keywords = email.get("keywords", [])
                    match_count = sum(1 for kw in keywords if kw.lower() in text.lower())
                    response_quality += min(1.0, match_count / 2.0) # Need at least 2 keywords for full quality score for that email
    
    total = len(emails)
    prio_score = priority_correct / total
    resp_score = response_quality / len(emails_requiring_resp) if emails_requiring_resp else 1.0
    processed_ratio = len(processed_ids) / total
    
    score = float(0.4 * prio_score + 0.4 * resp_score + 0.2 * processed_ratio)
    score = max(0.01, min(0.99, score))
    
    partial_scores = {
        "priority_accuracy": prio_score,
        "response_quality": resp_score,
        "emails_processed": processed_ratio
    }
    return score, partial_scores

# ── TASK 3: HARD ──────────────────────────────────────
EMAILS_HARD = [
    {"id": "h1", "subject": "Legal Notice: Patent Infringement Claim", "body": "Our attorneys have identified a potential patent infringement in your latest release. Immediate legal action is being prepared.", "sender": "lawyer@legal.com", "timestamp": "2024-02-01T09:00:00Z", "correct_category": "work", "correct_priority": "urgent", "requires_escalation": True, "requires_response": False},
    {"id": "h2", "subject": "RE: Data breach notification — customer data", "body": "We are investigating a potential data breach. Compliance team has been notified. Regulatory authorities may need to be informed.", "sender": "security@work.com", "timestamp": "2024-02-01T10:30:00Z", "correct_category": "work", "correct_priority": "urgent", "requires_escalation": True, "requires_response": True, "keywords": ["investigating", "security", "breach", "team", "notified"]},
    {"id": "h3", "subject": "Your order #5521 has shipped!", "body": "Good news! Your order #5521 is on its way. Use the tracking number below to follow its progress.", "sender": "orders@ecom.com", "timestamp": "2024-02-01T14:00:00Z", "correct_category": "personal", "correct_priority": "low", "requires_escalation": False},
    {"id": "h4", "subject": "Team standup notes — 2024-01-15", "body": "Here are the notes from today's standup. John will handle the API, and Sarah is working on the frontend.", "sender": "sarah@work.com", "timestamp": "2024-02-02T08:30:00Z", "correct_category": "work", "correct_priority": "normal", "requires_escalation": False, "requires_response": False},
    {"id": "h5", "subject": "Claim your free iPhone 15 now!!!", "body": "SPECIAL OFFER: You've been chosen for a free iPhone 15. Just pay for shipping. Click now!", "sender": "spam@web.com", "timestamp": "2024-02-02T09:45:00Z", "correct_category": "spam", "correct_priority": "low", "requires_escalation": False, "should_archive": True},
    {"id": "h6", "subject": "Subscription cancellation request — customer #8821", "body": "I would like to cancel my subscription #8821. Please confirm when this has been processed in my account.", "sender": "customer@gmail.com", "timestamp": "2024-02-02T11:00:00Z", "correct_category": "support", "correct_priority": "high", "requires_escalation": False, "requires_response": True, "keywords": ["cancel", "subscription", "processed", "confirm", "account"]},
    {"id": "h7", "subject": "Monthly SaaS metrics digest", "body": "Our monthly digest is here. Check out the latest trends in SaaS and see how you compare to peers.", "sender": "industry@saas.com", "timestamp": "2024-02-02T13:00:00Z", "correct_category": "newsletter", "correct_priority": "low", "requires_escalation": False, "should_archive": False},
    {"id": "h8", "subject": "Performance review scheduled — next week", "body": "Your annual performance review is scheduled for next Tuesday. Please be prepared to discuss your achievements.", "sender": "hr@work.com", "timestamp": "2024-02-03T10:00:00Z", "correct_category": "work", "correct_priority": "high", "requires_escalation": False, "requires_response": True, "keywords": ["confirm", "available", "meeting", "review", "prepared"]},
    {"id": "h9", "subject": "RE: Unpaid invoice — final notice", "body": "This is a final notice regarding your unpaid invoice. We require immediate payment to continue service.", "sender": "vendor@billing.com", "timestamp": "2024-02-03T14:30:00Z", "correct_category": "billing", "correct_priority": "urgent", "requires_escalation": False, "requires_response": False},
    {"id": "h10", "subject": "You've been selected for our survey!", "body": "Hi there, help us improve and get a chance to win. It only takes 5 minutes to complete the survey.", "sender": "promos@spam.net", "timestamp": "2024-02-04T09:00:00Z", "correct_category": "spam", "correct_priority": "low", "requires_escalation": False, "should_archive": True},
]

def grader_hard(actions_taken: List[dict], emails: List[dict]) -> Tuple[float, dict]:
    cat_correct = 0
    prio_correct = 0
    esc_correct = 0
    resp_quality = 0.0
    arch_correct = 0
    
    total_emails = len(emails)
    emails_esc = [e for e in emails if e.get("requires_escalation")]
    emails_resp = [e for e in emails if e.get("requires_response")]
    emails_arch = [e for e in emails if e.get("should_archive")]

    for email in emails:
        email_id = email["id"]
        actions = [a for a in actions_taken if a.get("email_id") == email_id]
        
        if any(a.get("action_type") == "categorize" and a.get("category") == email.get("correct_category") for a in actions):
            cat_correct += 1
        if any(a.get("action_type") == "prioritize" and a.get("priority") == email.get("correct_priority") for a in actions):
            prio_correct += 1
        if email.get("requires_escalation"):
            if any(a.get("action_type") == "escalate" for a in actions):
                esc_correct += 1
        if email.get("requires_response"):
            resp_action = next((a for a in actions if a.get("action_type") == "respond"), None)
            if resp_action and resp_action.get("response_text") and len(resp_action["response_text"]) > 20:
                keywords = email.get("keywords", [])
                match_count = sum(1 for kw in keywords if kw.lower() in resp_action["response_text"].lower())
                resp_quality += min(1.0, match_count / 2.0)
        if email.get("should_archive"):
            if any(a.get("action_type") == "archive" for a in actions):
                arch_correct += 1

    cat_score = cat_correct / total_emails
    prio_score = prio_correct / total_emails
    esc_score = esc_correct / len(emails_esc) if emails_esc else 1.0
    resp_score = resp_quality / len(emails_resp) if emails_resp else 1.0
    arch_score = arch_correct / len(emails_arch) if emails_arch else 1.0
    
    score = float(0.20 * cat_score + 0.20 * prio_score + 0.25 * esc_score + 0.25 * resp_score + 0.10 * arch_score)
    score = max(0.01, min(0.99, score))
    
    partial_scores = {
        "categorization_score": cat_score,
        "priority_score": prio_score,
        "escalation_score": esc_score,
        "response_score": resp_score,
        "archive_score": arch_score
    }
    return score, partial_scores

TASKS = {
    "task_easy_categorize": {
        "description": "Categorize 5 emails into the correct category. Each email's correct category is deterministic based on its content.",
        "emails": EMAILS_EASY,
        "max_steps": 8
    },
    "task_medium_prioritize_respond": {
        "description": "You have 6 emails. Correctly prioritize each one AND draft a brief, relevant response for the 2 emails marked as requiring a response.",
        "emails": EMAILS_MEDIUM,
        "max_steps": 12
    },
    "task_hard_full_triage": {
        "description": "Full inbox triage: 10 emails requiring correct categorization, prioritization, responses for flagged emails, escalation of 2 emails that contain legal/compliance keywords, and archival of all spam. Partial credit is awarded per criterion.",
        "emails": EMAILS_HARD,
        "max_steps": 20
    }
}

GRADERS = {
    "task_easy_categorize": grader_easy,
    "task_medium_prioritize_respond": grader_medium,
    "task_hard_full_triage": grader_hard,
}
import uuid
import copy
from typing import Optional, List, Dict, Any
from server.models import Email, Observation, Action, Reward, StepResult, ResetResult, StateResult
from server.tasks import TASKS, GRADERS

class EmailTriageEnv:
    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self._task_id = None
        self._emails = []
        self._current_index = 0
        self._step_num = 0
        self._done = False
        self._cumulative_reward = 0.01
        self._episode_id = str(uuid.uuid4())
        self._actions_taken = []
        self._last_action_result = None

    def reset(self, task_id: Optional[str] = None) -> ResetResult:
        self._reset_state()
        self._task_id = task_id or "task_easy_categorize"
        
        if self._task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {self._task_id}")
            
        task_data = TASKS[self._task_id]
        self._emails = copy.deepcopy(task_data["emails"])
        self._max_steps = task_data["max_steps"]
        
        return ResetResult(observation=self._make_observation())

    def step(self, action: Action) -> StepResult:
        if self._done:
            return StepResult(
                observation=self._make_observation(),
                reward=0.01,
                done=True,
                info={"message": "Episode already finished"}
            )

        self._step_num += 1
        current_email = self._emails[self._current_index]
        
        # Log action
        action_dict = action.model_dump()
        action_dict["email_id"] = current_email["id"]
        self._actions_taken.append(action_dict)

        # Compute intermediate reward
        reward_delta = 0.0
        msg = ""

        if action.action_type == "categorize":
            if action.category == current_email.get("correct_category"):
                reward_delta += 0.15
                msg = "Correct category"
            else:
                msg = "Incorrect category"
        elif action.action_type == "prioritize":
            if action.priority == current_email.get("correct_priority"):
                reward_delta += 0.15
                msg = "Correct priority"
            else:
                msg = "Incorrect priority"
        elif action.action_type == "respond":
            if action.response_text:
                if len(action.response_text) > 20:
                    keywords = current_email.get("keywords", [])
                    if keywords:
                        match_count = sum(1 for kw in keywords if kw.lower() in action.response_text.lower())
                        quality = min(1.0, match_count / 2.0)
                        reward_delta += 0.1 * quality
                        msg = f"Response quality: {quality}"
                    else:
                        reward_delta += 0.01
                        msg = "Generic response provided"
                else:
                    msg = "Response too short"
            else:
                msg = "Empty response"
        elif action.action_type == "escalate":
            if current_email.get("requires_escalation"):
                reward_delta += 0.2
                msg = "Correct escalation"
            else:
                reward_delta -= 0.01
                msg = "Incorrect escalation"
        elif action.action_type == "archive":
            if current_email.get("should_archive"):
                reward_delta += 0.1
                msg = "Correct archival"
            else:
                reward_delta -= 0.03
                msg = "Incorrect archival"
        elif action.action_type == "skip":
            msg = "Email skipped"
        
        # Step penalty
        reward_delta -= 0.02
        
        # Intermediate step reward logic: 0.5 + delta
        step_reward = max(0.01, min(0.99, 0.5 + reward_delta))
        self._cumulative_reward += step_reward
        self._last_action_result = msg

        # Advance email index if not skipping mid-triage (simplified)
        # Actually, instructions imply one action per email or multiple?
        # "Each email agent is on" implies we advance after action.
        # But some emails need multiple actions. 
        # Standard RL for this would be one action per step.
        # Let's say we advance after ANY action types that aren't "skip" 
        # OR if we processed it. 
        # Requirement says "Advance _current_index".
        self._current_index += 1
        
        # Transitions to done
        task_data = TASKS[self._task_id]
        if self._current_index >= len(self._emails) or self._step_num >= self._max_steps:
            self._done = True
            
        final_info = {"last_action_msg": msg}
        
        if self._done:
            grader = GRADERS[self._task_id]
            final_score, extra_info = grader(self._actions_taken, self._emails)
            final_info.update(extra_info)
            final_info["final_score"] = final_score
            
            # Bonus of 0.3 if final_score >= 0.8
            if final_score >= 0.8:
                self._cumulative_reward += 0.3
                final_info["bonus_awarded"] = True

        reward_obj = Reward(
            value=step_reward,
            partial_scores={},
            message=msg
        )

        return StepResult(
            observation=self._make_observation(),
            reward=reward_obj,
            done=self._done,
            info=final_info
        )

    def state(self) -> StateResult:
        return StateResult(
            task_id=self._task_id or "",
            step_number=self._step_num,
            done=self._done,
            cumulative_reward=max(0.01, min(0.99, self._cumulative_reward)),
            episode_id=self._episode_id,
            emails_processed=self._current_index
        )

    def _make_observation(self) -> Observation:
        if self._current_index < len(self._emails):
            email_data = self._emails[self._current_index]
            current_email = Email(**email_data)
        else:
            # Placeholder for done state
            current_email = Email(id="none", subject="End of Inbox", body="", sender="", timestamp="")
            
        return Observation(
            task_id=self._task_id or "",
            task_description=TASKS[self._task_id]["description"] if self._task_id else "",
            current_email=current_email,
            inbox_remaining=max(0, len(self._emails) - self._current_index - 1),
            step_number=self._step_num,
            max_steps=TASKS[self._task_id]["max_steps"] if self._task_id else 0,
            last_action_result=self._last_action_result,
            context={}
        )
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
