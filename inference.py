"""
Inference Script — Email Triage OpenEnv

Required environment variables:
  API_BASE_URL   The API endpoint for the LLM (e.g. https://router.huggingface.co/v1)
  MODEL_NAME     The model identifier
  HF_TOKEN       Your Hugging Face / API key
  ENV_URL        The URL where the OpenEnv server is running (default: http://localhost:7860)

Usage:
  python inference.py
"""

import os
import json
import requests
from openai import OpenAI
from typing import Dict, Any, List

# ── Config ──────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")

MAX_STEPS    = 20
TEMPERATURE  = 0.1
MAX_TOKENS   = 300

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

For each email, decide the MOST IMPORTANT action to take first.
If an email is legal/compliance-related with terms like 'breach', 'legal', 'attorney', 'regulatory' — use "escalate".
If an email is clearly spam — use "archive".
Otherwise, "categorize" it first, then "prioritize" it in the next step.
"""

def call_env(method: str, endpoint: str, data: Any = None) -> Dict[str, Any]:
    url = f"{ENV_URL}{endpoint}"
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling environment: {e}")
        return {}

def build_user_prompt(observation: Dict[str, Any]) -> str:
    email = observation.get("current_email", {})
    return f"""
TASK DESCRIPTION: {observation.get('task_description')}
STEP: {observation.get('step_number')} / {observation.get('max_steps')}
EMAILS REMAINING: {observation.get('inbox_remaining')}
LAST ACTION RESULT: {observation.get('last_action_result')}

CURRENT EMAIL:
ID: {email.get('id')}
From: {email.get('sender')}
Subject: {email.get('subject')}
Body: {email.get('body')}

What action should be taken for this email?
"""

def parse_action(response_text: str) -> Dict[str, Any]:
    try:
        # Try to find JSON block if model wrapped it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "{" in response_text:
            response_text = response_text[response_text.find("{"):response_text.rfind("}")+1]
        
        action = json.loads(response_text)
        return action
    except Exception as e:
        print(f"Failed to parse action: {e}. Raw response: {response_text}")
        return {"action_type": "skip", "reasoning": "Parse failure"}

def run_episode(client: OpenAI, task_id: str) -> Dict[str, Any]:
    print(f"Starting Task: {task_id}")
    obs_res = call_env("POST", "/reset", {"task_id": task_id})
    if not obs_res:
        return {"cumulative_reward": 0.0, "step_number": 0}
    
    observation = obs_res.get("observation")
    done = False
    cumulative_reward = 0.0
    steps = 0
    
    while not done and steps < MAX_STEPS:
        user_prompt = build_user_prompt(observation)
        
        chat_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        raw_response = chat_completion.choices[0].message.content
        action = parse_action(raw_response)
        
        step_res = call_env("POST", "/step", action)
        if not step_res:
            break
            
        observation = step_res.get("observation")
        cumulative_reward += step_res.get("reward", 0.0)
        done = step_res.get("done", False)
        steps += 1
        
        info = step_res.get("info", {})
        if done:
            print(f"Task Complete: {task_id} | Score: {info.get('grader_score', 0.0):.4f} | Bonus: {info.get('bonus_awarded', False)}")
            return {
                "score": info.get("grader_score", 0.0),
                "steps": steps,
                "cumulative_reward": cumulative_reward
            }
            
    return {"score": 0.0, "steps": steps, "cumulative_reward": cumulative_reward}

def main():
    if not API_KEY:
        print("Error: HF_TOKEN or API_KEY environment variable is required.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    results = {}

    print("============================================================")
    print("OpenEnv Email Triage — Baseline Inference Results")
    
    for tid in TASK_IDS:
        res = run_episode(client, tid)
        results[tid] = res

    print("============================================================")
    total_score = 0.0
    for tid, res in results.items():
        score = res.get("score", 0.0)
        steps = res.get("steps", 0)
        print(f"Task: {tid:<35} | Score: {score:.4f} | Steps: {steps}")
        total_score += score
    
    avg_score = total_score / len(TASK_IDS)
    print(f"Average Score: {avg_score:.4f}")

if __name__ == "__main__":
    main()
