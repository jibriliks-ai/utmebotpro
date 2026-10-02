"""
cbt_engine.py
Loads the clean question bank and exposes the interface ssmain.py expects:
    fetcher, format_question, search_databank, get_random_question,
    LOCAL_DATABANK, ALL_QS, AVAILABLE_SUBJECTS
"""
import json
import random
from pathlib import Path

# Primary bank (first match wins). Falls back to extras if not present.
PRIMARY_FILES = [
    "questions_clean.json",
    "questions_valid.json",
]

# Also merge any questions_*.json sitting next to the bot
EXTRA_GLOBS = ["questions_*.json"]


ALL_QS = []              # flat list of all usable questions
LOCAL_DATABANK = {}      # subject_key -> [question, ...]
AVAILABLE_SUBJECTS = []  # subject_keys that actually have questions
_seen_fp = set()


# ---------- internals ----------

def _fingerprint(q):
    return "|".join([
        str(q.get("subject_key", "")).lower(),
        str(q.get("year", "")),
        str(q.get("question", "")).lower().strip(),
    ])


def _normalize(q):
    """Return a dict in the exact shape ssmain.py expects."""
    options = q.get("options") or []

    def pick(idx, key):
        v = q.get(key)
        if v:
            return str(v).strip()
        if idx < len(options):
            return str(options[idx]).strip()
        return ""

    answer = (q.get("answer_letter") or q.get("answer") or "")
    answer = str(answer).strip().upper()[:1]

    return {
        "id": str(q.get("id") or q.get("source_id") or ""),
        "subject": str(q.get("subject", "")).strip(),
        "subject_key": str(q.get("subject_key", "")).strip().lower(),
        "year": q.get("year", ""),
        "topic": q.get("topic", "General"),
        "question": str(q.get("question", "")).strip(),
        "option_a": pick(0, "option_a"),
        "option_b": pick(1, "option_b"),
        "option_c": pick(2, "option_c"),
        "option_d": pick(3, "option_d"),
        "option_e": pick(4, "option_e"),
        "answer": answer,
        "answer_text": str(q.get("answer_text", "")).strip(),
        "explanation": str(q.get("explanation", "")).strip(),
    }


def _add(q):
    # Reject unusable records so mocks never crash
    if not q["question"]:
        return False
    if not q["option_a"] or not q["option_b"]:
        return False
    if q["answer"] not in ("A", "B", "C", "D", "E"):
        return False

    fp = _fingerprint(q)
    if fp in _seen_fp:
        return False
    _seen_fp.add(fp)

    ALL_QS.append(q)
    key = q["subject_key"] or q["subject"].lower().replace(" ", "_")
    LOCAL_DATABANK.setdefault(key, []).append(q)
    return True


def _load_file(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[cbt_engine] skip {path}: {e}")
        return 0
    if not isinstance(data, list):
        print(f"[cbt_engine] {path} is not a list")
        return 0
    added = 0
    for item in data:
        if isinstance(item, dict) and _add(_normalize(item)):
            added += 1
    print(f"[cbt_engine] {path}: +{added} questions")
    return added


def _bootstrap():
    loaded = set()

    for f in PRIMARY_FILES:
        if Path(f).exists():
            _load_file(f)
            loaded.add(f)

    for pattern in EXTRA_GLOBS:
        for p in sorted(Path(".").glob(pattern)):
            name = str(p)
            if name in loaded or name in PRIMARY_FILES:
                continue
            _load_file(name)
            loaded.add(name)

    AVAILABLE_SUBJECTS.clear()
    for key, items in sorted(LOCAL_DATABANK.items()):
        if items:
            AVAILABLE_SUBJECTS.append(key)

    print(f"[cbt_engine] TOTAL: {len(ALL_QS)} questions across "
          f"{len(AVAILABLE_SUBJECTS)} subjects")
    for key in AVAILABLE_SUBJECTS:
        print(f"   {key}: {len(LOCAL_DATABANK[key])}")


_bootstrap()


# ---------- public API ----------

def format_question(q, i, total):
    lines = [f"Q{i}/{total}", q.get("question", "")]
    for letter in ("A", "B", "C", "D", "E"):
        opt = q.get(f"option_{letter.lower()}")
        if opt:
            lines.append(f"{letter}) {opt}")
    return "\n".join(lines)


def search_databank(query, subject=None, limit=5):
    q = (query or "").lower().strip()
    if not q:
        return []
    pool = LOCAL_DATABANK.get(subject) or ALL_QS
    words = [w for w in q.split() if len(w) > 2]
    if not words:
        return []
    scored = []
    for item in pool:
        text = item.get("question", "").lower()
        score = sum(1 for w in words if w in text)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def get_random_question(subject=None):
    pool = LOCAL_DATABANK.get(subject) or ALL_QS
    return random.choice(pool) if pool else None


class _Fetcher:
    def fetch(self, subject, year=None, limit=40):
        key = (subject or "").lower()
        pool = LOCAL_DATABANK.get(key, [])
        if not pool:
            pool = [q for q in ALL_QS if key and key in q["subject"].lower()]
        if not pool:
            return []
        return random.sample(pool, min(limit, len(pool)))


fetcher = _Fetcher()
