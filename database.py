import json, os
from datetime import datetime, date, timedelta

USER_FILE = "users.json"
LEADERBOARD_FILE = "leaderboard.json"

def load_all_users():
    try:
        with open(USER_FILE) as f:
            return json.load(f)
    except:
        return {}

def get_user_data(user_id: int):
    users = load_all_users()
    uid = str(user_id)
    today_str = str(date.today())
    
    if uid not in users:
        users[uid] = {
            "count": 0,
            "mock_count": 0,
            "last_date": today_str,
            "is_premium": False,
            "premium_until": None,
            "over_limit_attempts": 0,
            "name": f"User {user_id}"
        }
        save_users(users)
    
    data = users[uid]
    # Reset daily if new day
    if data.get("last_date") != today_str:
        data["count"] = 0
        data["mock_count"] = 0
        data["over_limit_attempts"] = 0
        data["last_date"] = today_str
        save_users(users)
    
    # Check premium expiry
    if data.get("is_premium") and data.get("premium_until"):
        try:
            until = datetime.fromisoformat(data["premium_until"])
            if datetime.now() > until:
                data["is_premium"] = False
                save_users(users)
        except:
            pass
    
    return data

def save_users(all_data):
    with open(USER_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)

def save_user_data(user_id: int, user_data):
    users = load_all_users()
    users[str(user_id)] = user_data
    save_users(users)

def check_limit(user_id: int):
    d = get_user_data(user_id)
    if d.get("is_premium"):
        return True, ""
    from config import FREE_DAILY_LIMIT
    if d.get("count", 0) >= FREE_DAILY_LIMIT:
        return False, "limit"
    return True, ""

def increment_usage(user_id: int):
    d = get_user_data(user_id)
    d["count"] = d.get("count", 0) + 1
    save_user_data(user_id, d)

def increment_mock(user_id: int):
    d = get_user_data(user_id)
    d["mock_count"] = d.get("mock_count", 0) + 1
    save_user_data(user_id, d)

def get_leaderboard_top():
    try:
        with open(LEADERBOARD_FILE) as f:
            lb = json.load(f)
        if lb:
            top = sorted(lb, key=lambda x: x.get("score", 0), reverse=True)[0]
            return top
    except:
        pass
    return {"name": "Adaeze Okafor", "score": 318, "subject": "Science"}