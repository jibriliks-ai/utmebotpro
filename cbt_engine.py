import json
import random
from pathlib import Path

BANK_FILE = Path("questions_clean.json")

ALL_QS = []
LOCAL_DATABANK = {}

def _normalize(q):
    """Convert clean JSON record into format the bot expects."""
    options = q.get("options") or []
    # Handle both new 'options' array and old option_a/b/c/d keys
    opt_a = q.get("option_a") or (options[0] if len(options) > 0 else "")
    opt_b = q.get("option_b") or (options[1] if len(options) > 1 else "")
    opt_c = q.get("option_c") or (options[2] if len(options) > 2 else "")
    opt_d = q.get("option_d") or (options[3] if len(options) > 3 else "")
    
    answer = q.get("answer_letter") or q.get("answer") or ""
    
    return {
        "id": q.get("id") or q.get("source_id") or "",
        "subject": q.get("subject", ""),
        "subject_key": q.get("subject_key", ""),
        "year": q.get("year", ""),
        "topic": q.get("topic", ""),
        "question": q.get("question", ""),
        "option_a": opt_a,
        "option_b": opt_b,
        "option_c": opt_c,
        "option_d": opt_d,
        "answer": answer,
        "explanation": q.get("explanation", ""),
    }

def load_bank():
    global ALL_QS, LOCAL_DATABANK
    if not BANK_FILE.exists():
        print(f"[cbt_engine] No {BANK_FILE} found")
        return
    try:
        data = json.loads(BANK_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[cbt_engine] Failed to load: {e}")
        return
    ALL_QS = [_normalize(q) for q in data]
    # Group by subject_key
    for q in ALL_QS:
        key = q.get("subject_key") or q.get("subject", "").lower()
        LOCAL_DATABANK.setdefault(key, []).append(q)
    print(f"[cbt_engine] Loaded {len(ALL_QS)} questions across {len(LOCAL_DATABANK)} subjects")

load_bank()

def format_question(q, i, total):
    lines = [f"Q{i}/{total}", q.get("question", "")]
    if q.get("option_a"): lines.append(f"A) {q['option_a']}")
    if q.get("option_b"): lines.append(f"B) {q['option_b']}")
    if q.get("option_c"): lines.append(f"C) {q['option_c']}")
    if q.get("option_d"): lines.append(f"D) {q['option_d']}")
    return "\n".join(lines)

def search_databank(query, subject=None, limit=5):
    """Simple keyword search over question text."""
    q = (query or "").lower().strip()
    if not q:
        return []
    pool = LOCAL_DATABANK.get(subject, []) if subject else ALL_QS
    words = [w for w in q.split() if len(w) > 2]
    scored = []
    for item in pool:
        text = item.get("question", "").lower()
        score = sum(1 for w in words if w in text)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]

def get_random_question(subject=None):
    pool = LOCAL_DATABANK.get(subject, []) if subject else ALL_QS
    return random.choice(pool) if pool else None

class _Fetcher:
    def fetch(self, subject, year=None, limit=40):
        pool = LOCAL_DATABANK.get(subject, [])
        if not pool:
            # Fallback: try matching by subject text
            pool = [q for q in ALL_QS if subject.lower() in q.get("subject", "").lower()]
        if not pool:
            return []
        # Prefer unused
        return random.sample(pool, min(limit, len(pool)))

fetcher = _Fetcher()
