"""
Inference Script — Email Triage OpenEnv

Required environment variables:
  API_BASE_URL   The API endpoint for the LLM
  MODEL_NAME     The model identifier
  HF_TOKEN       Your Hugging Face / API key
"""

import os
import json
import requests
from typing import List, Optional
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
BENCHMARK    = "email-triage"

MAX_STEPS = 20
TEMPERATURE = 0.1
MAX_TOKENS = 300
SUCCESS_SCORE_THRESHOLD = 0.5

TASK_IDS = [
    "task_easy_categorize",
    "task_medium_prioritize_respond",
    "task_hard_full_triage",
]

SYSTEM_PROMPT = """You are an expert email triage assistant.
You will be shown one email at a time and must decide what to do with it.

Respond with a single JSON object and nothing else. The JSON must have:
- "action_type": one of "categorize", "prioritize", "respond", "escalate", "archive", "skip"
- "category": one of "work", "personal", "spam", "newsletter", "support", "billing" (if categorizing)
- "priority": one of "urgent", "high", "normal", "low" (if prioritizing)
- "response_text": a brief professional reply (if responding)
- "reasoning": one sentence explaining your decision

If an email is legal/compliance-related with terms like 'breach', 'legal', 'attorney', 'regulatory' — use "escalate".
If an email is clearly spam — use "archive".
Otherwise, "categorize" it first, then "prioritize" it in the next step.
"""


# ── Logging helpers (mandatory format) ──────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Sanitize action string to single line
    action_str = action.replace("\n", " ").replace("\r", "")[:80]
    print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


# ── Environment helpers ──────────────────────────────────────────────────────

def call_env(method: str, endpoint: str, data=None):
    url = f"{ENV_URL}{endpoint}"
    try:
        if method == "POST":
            resp = requests.post(url, json=data or {}, timeout=30)
        else:
            resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[DEBUG] ENV call failed {method} {endpoint}: {e}", flush=True)
        return None

def build_user_prompt(obs: dict) -> str:
    email = obs.get("current_email", {})
    return (
        f"Task: {obs.get('task_description', '')}\n\n"
        f"Email #{obs.get('step_number', 0) + 1} of {obs.get('max_steps', 0)}:\n"
        f"From: {email.get('sender', '')}\n"
        f"Subject: {email.get('subject', '')}\n"
        f"Body: {email.get('body', '')}\n\n"
        f"Emails remaining: {obs.get('inbox_remaining', 0)}\n"
        f"Last result: {obs.get('last_action_result', 'None')}\n\n"
        f"Respond with a single JSON action object."
    )

def parse_action(response_text: str) -> dict:
    try:
        text = response_text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"action_type": "skip"}


# ── Episode runner ───────────────────────────────────────────────────────────

def run_episode(client: OpenAI, task_id: str) -> dict:
    rewards: List[float] = []
    steps_taken = 0
    success = False
    final_score = 0.0

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = call_env("POST", "/reset", {"task_id": task_id})
        if not result:
            log_end(success=False, steps=0, rewards=[])
            return {"score": 0.0, "steps": 0}

        obs = result.get("observation", {})

        for step in range(1, MAX_STEPS + 1):
            done = result.get("done", False)
            if done:
                break

            user_prompt = build_user_prompt(obs)

            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=False,
                )
                response_text = completion.choices[0].message.content or ""
            except Exception as e:
                print(f"[DEBUG] Model request failed: {e}", flush=True)
                response_text = '{"action_type": "skip"}'

            action = parse_action(response_text)
            action_str = action.get("action_type", "skip")

            step_result = call_env("POST", "/step", action)
            if not step_result:
                log_step(step=step, action=action_str, reward=0.0, done=True, error="env_error")
                break

            reward_obj = step_result.get("reward", {})
            reward = reward_obj.get("value", reward_obj) if isinstance(reward_obj, dict) else float(reward_obj or 0.0)
            done = step_result.get("done", False)
            error = obs.get("last_action_result") if "error" in str(obs.get("last_action_result", "")).lower() else None

            rewards.append(reward)
            steps_taken = step
            obs = step_result.get("observation", {})

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            if done:
                final_score = step_result.get("info", {}).get("grader_score", step_result.get("info", {}).get("cumulative_reward", sum(rewards) / len(rewards) if rewards else 0.0))
                break

        success = final_score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, rewards=rewards)

    return {"score": final_score, "steps": steps_taken}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    print("=" * 60, flush=True)
    print("OpenEnv Email Triage — Baseline Inference Results", flush=True)
    print("=" * 60, flush=True)

    results = {}
    for task_id in TASK_IDS:
        print(f"Starting Task: {task_id}", flush=True)
        res = run_episode(client, task_id)
        results[task_id] = res
        print(f"Task Complete: {task_id} | Score: {res['score']:.4f} | Steps: {res['steps']}", flush=True)

    print("=" * 60, flush=True)
    for task_id, res in results.items():
        print(f"Task: {task_id:<35} | Score: {res['score']:.4f} | Steps: {res['steps']}", flush=True)
    avg = sum(r["score"] for r in results.values()) / len(results)
    print(f"Average Score: {avg:.4f}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
