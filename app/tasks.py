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
    
    # final score = 0.7 * correct_ratio + 0.3 * processed_ratio
    score = 0.7 * correct_ratio + 0.3 * processed_ratio
    # Ensure score is strictly 0.0 - 1.0 but not 1.0 unless perfect
    score = min(max(score, 0.001), 0.999)
    
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
    
    # final = 0.4 * priority_score + 0.4 * response_quality + 0.2 * processed_ratio
    score = 0.4 * prio_score + 0.4 * resp_score + 0.2 * processed_ratio
    score = min(max(score, 0.001), 0.999)
    
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
    
    # final = 0.20 * categorization + 0.20 * priority + 0.25 * escalation + 0.25 * response + 0.10 * archive
    score = 0.20 * cat_score + 0.20 * prio_score + 0.25 * esc_score + 0.25 * resp_score + 0.10 * arch_score
    score = min(max(score, 0.001), 0.999)
    
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
