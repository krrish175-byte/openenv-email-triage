import uuid
import copy
from typing import Optional, List, Dict, Any
from app.models import Email, Observation, Action, Reward, StepResult, ResetResult, StateResult
from app.tasks import TASKS, GRADERS

class EmailTriageEnv:
    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self._task_id = None
        self._emails = []
        self._current_index = 0
        self._step_num = 0
        self._done = False
        self._cumulative_reward = 0.0
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
                reward=0.0,
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
                        reward_delta += 0.05
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
                reward_delta -= 0.05
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
        step_reward = max(0.001, min(0.999, 0.5 + reward_delta))
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

        return StepResult(
            observation=self._make_observation(),
            reward=step_reward,
            done=self._done,
            info=final_info
        )

    def state(self) -> StateResult:
        return StateResult(
            task_id=self._task_id or "",
            step_number=self._step_num,
            done=self._done,
            cumulative_reward=self._cumulative_reward,
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
