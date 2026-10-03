import json
from pathlib import Path

def load_partial_array(text):
    # Try normal parse first
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        pass

    s = text.strip()
    if not s.startswith('['):
        raise ValueError("Not a JSON array")

    # Remove leading '['
    body = s[1:]
    decoder = json.JSONDecoder()
    objs = []
    idx = 0
    n = len(body)

    while idx < n:
        # Skip whitespace and commas
        while idx < n and body[idx] in ' \t\r\n,':
            idx += 1

        if idx >= n or body[idx] == ']':
            break

        try:
            obj, end = decoder.raw_decode(body, idx)
            objs.append(obj)
            idx = end
        except json.JSONDecodeError:
            # Incomplete object at the end — stop here
            break

    return objs, True

for path in Path('.').glob('*.json'):
    text = path.read_text()
    try:
        data, repaired = load_partial_array(text)
    except Exception as e:
        print(f"Skipping {path}: {e}")
        continue

    if repaired:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Repaired {path}: kept {len(data)} complete records, dropped incomplete tail.")
    else:
        print(f"{path} is already valid ({len(data)} records).")
