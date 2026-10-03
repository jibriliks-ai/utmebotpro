import json
import re
from pathlib import Path

# Fields your loader expects
Q_KEY = "q"
A_KEY = "a"
ANS_KEY = "ans"

def escape_control_chars_in_strings(text: str) -> str:
    """Escape raw control chars (newline, tab, CR) that appear inside JSON strings."""
    out = []
    in_string = False
    escaped = False
    for ch in text:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in ("\n", "\r", "\t"):
            out.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[ch])
            continue
        out.append(ch)
    return "".join(out)

def normalize_record(rec: dict) -> dict:
    """Map whatever schema this file uses into the loader's expected schema."""
    # question text
    q = rec.get("q") or rec.get("question") or ""
    # answer text
    a = rec.get("a") or rec.get("answer_text") or ""
    # answer letter
    ans = rec.get("ans") or rec.get("answer_letter") or ""

    # If answer text is missing, derive it from options + letter
    options = rec.get("options")
    if not a and ans:
        if isinstance(options, dict):
            a = options.get(ans, "")
        elif isinstance(options, list) and ans in ("A", "B", "C", "D"):
            idx = "ABCD".index(ans)
            if idx < len(options):
                a = options[idx]

    rec[Q_KEY] = q
    rec[A_KEY] = a
    rec[ANS_KEY] = ans
    return rec

for path in sorted(Path(".").glob("questions_*.json")):
    raw = path.read_text(encoding="utf-8", errors="replace")
    fixed = escape_control_chars_in_strings(raw)

    try:
        data = json.loads(fixed)
    except json.JSONDecodeError as e:
        print(f"[FAIL] {path}: still invalid after escape -> {e}")
        continue

    if not isinstance(data, list):
        print(f"[SKIP] {path}: top-level is not a list")
        continue

    cleaned = [normalize_record(r) for r in data if isinstance(r, dict)]
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK]   {path}: {len(cleaned)} records normalized")
