---
title: OpenEnv Email Triage
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

# Email Triage OpenEnv

An OpenEnv environment where AI agents learn to triage email inboxes. Agents must categorize, prioritize, respond to, escalate, and archive emails across three tasks of increasing complexity.

## Environment Description
This environment models a real-world email triage workflow. Agents are presented with a series of emails (an inbox) and must perform specific actions to process them. This is a genuine NLP task that requires understanding of content, urgency, and professional communication.

## Action Space
The agent can take one of the following 6 actions:

| Action | Description | Parameters |
| :--- | :--- | :--- |
| `categorize` | Assign a category to the email | `category`: one of "work", "personal", "spam", "newsletter", "support", "billing" |
| `prioritize` | Assign a priority level | `priority`: one of "urgent", "high", "normal", "low" |
| `respond` | Draft a professional reply | `response_text`: string (min 20 chars) |
| `archive` | Move the email to archive | - |
| `escalate` | Flag for management/legal review | - |
| `skip` | Skip the current email | - |

## Observation Space
The observation is a JSON object containing:

| Field | Description |
| :--- | :--- |
| `task_id` | Identifier of the current task |
| `task_description`| Description of the objective |
| `current_email` | Object containing `id`, `subject`, `body`, `sender`, `timestamp` |
| `inbox_remaining` | Number of emails left in the task |
| `step_number` | Current step index |
| `max_steps` | Maximum steps allowed for the task |
| `last_action_result`| Feedback message from the previous step |
| `context` | Task-specific metadata |

## Task Descriptions

### task_easy_categorize
**Difficulty:** Easy | **Max Steps:** 8
Requires the agent to categorize 5 clearly labeled emails. Content is unambiguous (e.g., meeting notes, billing confirmation, obvious spam). Scoring focuses on categorization accuracy and processing speed.

### task_medium_prioritize_respond
**Difficulty:** Medium | **Max Steps:** 12
Requires prioritizing 6 emails and drafting brief, relevant responses for selected ones. Scoring balances priority accuracy and the quality of responses (verified via keyword matching).

### task_hard_full_triage
**Difficulty:** Hard | **Max Steps:** 20
A full inbox triage of 10 emails. Agents must categorize, prioritize, respond where needed, escalate legal/compliance issues, and archive spam. Scoring is a weighted average across all triage criteria.

## Reward Structure
The environment provides dense rewards between 0.0 and 1.0 at each step:
- **Baseline:** 0.5 per step.
- **Bonuses:** Up to +0.2 for correct actions (categorization, escalation, etc.).
- **Response Quality:** Scaled based on length and keyword relevance.
- **Penalties:** -0.02 step penalty to encourage efficiency; small penalties for incorrect escalations/archives.
- **Episode Bonus:** +0.3 awarded at the end if the final grader score exceeds 0.8.

## Setup & Usage

### Local Development
1. Create and activate a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   venv/bin/uvicorn app.server:app --host 0.0.0.0 --port 7860
   ```
4. Run inference:
   ```bash
   export HF_TOKEN=your_token
   venv/bin/python3 inference.py
   ```

### Docker
1. Build image:
   ```bash
   docker build -t email-triage-env .
   ```
2. Run container:
   ```bash
   docker run -p 7860:7860 email-triage-env
   ```

## Baseline Scores

| Task                            | Model                              | Score  |
|---------------------------------|------------------------------------|--------|
| task_easy_categorize            | meta-llama/Llama-3.1-8B-Instruct   | 0.9990 |
| task_medium_prioritize_respond  | meta-llama/Llama-3.1-8B-Instruct   | 0.2667 |
| task_hard_full_triage           | meta-llama/Llama-3.1-8B-Instruct   | 0.4300 |
| **Average**                     |                                    | **0.5652** |

## Environment Variables
- `API_BASE_URL`: LLM API endpoint (default: HuggingFace Router)
- `MODEL_NAME`: Identifier for the model to use
- `HF_TOKEN`: API key for authentication
- `ENV_URL`: URL of the triage server (default: http://localhost:7860)
