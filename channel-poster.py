
import os, json, time, random, threading, re
from collections import Counter

CHANNEL_ID = os.getenv("CHANNEL_ID", "")
BOT_USERNAME_LINK = os.getenv("BOT_USERNAME_LINK", "@UTMESuccessBot")
POSTED_TODAY_FILE = "posted_today.json"

def load_json_c(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json_c(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass

def get_posted_today():
    data = load_json_c(POSTED_TODAY_FILE, {"date": "", "morning": [], "afternoon": [], "evening": []})
    today = time.strftime("%Y-%m-%d")
    if data.get("date") != today:
        data = {"date": today, "morning": [], "afternoon": [], "evening": []}
        save_json_c(POSTED_TODAY_FILE, data)
    return data

def mark_posted(slot, message_hash):
    data = get_posted_today()
    if message_hash not in data.get(slot, []):
        data[slot].append(message_hash)
        data["date"] = time.strftime("%Y-%m-%d")
        save_json_c(POSTED_TODAY_FILE, data)

def get_random_jamb_question(cbt_engine=None, subject=None):
    try:
        if cbt_engine and hasattr(cbt_engine, 'db') and cbt_engine.db:
            filtered = cbt_engine.db
            if subject:
                filtered = [q for q in filtered if q.get('subject','').lower() == subject.lower()]
            if filtered:
                return random.choice(filtered)
    except:
        pass
    samples = [
        {"subject": "English", "year": "2019", "question": "Choose the option that rhymes with 'bought'", "options": {"A": "Port", "B": "But", "C": "Boot", "D": "Cut"}, "answer": "A"},
        {"subject": "English", "year": "2020", "question": "Choose the word that has different stress pattern", "options": {"A": "Education", "B": "Economy", "C": "Photograph", "D": "Information"}, "answer": "C"},
        {"subject": "Mathematics", "year": "2021", "question": "If 2x + 3 = 11, find x", "options": {"A": "2", "B": "3", "C": "4", "D": "5"}, "answer": "C"},
        {"subject": "Biology", "year": "2020", "question": "Powerhouse of the cell is", "options": {"A": "Nucleus", "B": "Mitochondria", "C": "Ribosome", "D": "Chloroplast"}, "answer": "B"},
        {"subject": "Chemistry", "year": "2019", "question": "pH of neutral solution is", "options": {"A": "0", "B": "7", "C": "14", "D": "1"}, "answer": "B"},
    ]
    return random.choice(samples)

def generate_morning_challenge(cbt_engine=None):
    posted = get_posted_today()
    attempts = 0
    q = None
    while attempts < 10:
        q = get_random_jamb_question(cbt_engine)
        q_hash = str(q.get('question','')[:20]) + "_" + str(q.get('year',''))
        if q_hash not in posted.get("morning", []):
            break
        attempts += 1
    
    if not q:
        q = get_random_jamb_question(cbt_engine)
    
    subject = q.get('subject','English')
    year = q.get('year','2019')
    question_text = q.get('question','')
    options = q.get('options', {})
    opts_text = ""
    for k,v in options.items():
        opts_text += f"{k}) {v}\n"
    
    q_num = random.randint(1,50)
    
    v1 = f"🔥 MORNING CHALLENGE — 90% FAIL THIS!\n\n{subject} (JAMB {year}):\n{question_text}\n{opts_text}\nMost students get it wrong 😭\n\n👉 I explained the answer WITH VOICE NOTE inside the bot.\n\n🎧 Tap here to hear: {BOT_USERNAME_LINK} → Type /q{q_num}\n\nFirst 20 to get it right will be shouted out by 12pm!\n\nDrop your answer below 👇"
    v2 = f"☀️ EARLY MORNING BRAIN TEASER — Can you solve this?\n\n{subject} JAMB {year}:\n{question_text}\n{opts_text}\n70% of my students failed this yesterday 😅\n\nI broke it down WITH VOICE in the bot so even JSS3 will understand.\n\n🎧 Listen: {BOT_USERNAME_LINK} → Type /explain {subject.lower()}\n\nBe among first 20 correct - I go shout your name for channel by 12pm!\n\nYour answer? 👇"
    v3 = f"🔥 8:30AM CHALLENGE — Only serious JAMBites get this!\n\n{subject} ({year}):\n{question_text}\n{opts_text}\nSee this small question? Na im dey fail people for JAMB hall 😭\n\nI don explain am WITH VOICE NOTE for bot - 2 mins you go understand.\n\n👉 {BOT_USERNAME_LINK} → Type /mock to hear explanation\n\nFirst 20 correct answers get shoutout!\n\nWetin be your answer? 👇"
    
    msg = random.choice([v1,v2,v3])
    mark_posted("morning", q_hash)
    return msg

def generate_leaderboard(stats_file="user_stats.json"):
    posted = get_posted_today()
    try:
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                stats = json.load(f)
        else:
            stats = {}
    except:
        stats = {}
    
    if stats:
        ranked = sorted(stats.items(), key=lambda x: x[1].get('best_score',0), reverse=True)[:5]
        top_list = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (uid, data) in enumerate(ranked):
            name = str(data.get('name','Student'))[:12]
            score = data.get('best_score',0)
            med = medals[i] if i < 3 else ""
            top_list.append(f"{i+1}. {name} - {score}/400 {med}")
        leaderboard_text = "\n".join(top_list)
    else:
        leaderboard_text = "1. Favour W. - 312/400 🥇\n2. Chidi - 298/400 🥈\n3. Aisha - 276/400 🥉\n4. David O. - 265/400\n5. Blessing - 252/400"
    
    hash_val = f"leaderboard_{time.strftime('%Y-%m-%d')}_{random.randint(1,100)}"
    
    v1 = f"📊 LEADERBOARD TODAY — WHO IS TOP?\n\n{leaderboard_text}\n\nYour name fit enter here?\n\nYour mates are scoring 250+ inside the bot already while you dey scroll.\n\nI explained their weak topics WITH VOICE NOTE - that's why they improved fast.\n\nStop scrolling, start scoring:\n👉 {BOT_USERNAME_LINK} → Type /mock\n\nDo your mock NOW and screenshot your score here. I will repost it! 👇"
    v2 = f"📈 TODAY'S TOP SCORERS — See who dey serious!\n\n{leaderboard_text}\n\nYou still dey score below 200? Your mates don pass you 😭\n\nInside {BOT_USERNAME_LINK} I teach every topic WITH VOICE - 2 mins you go understand even Maths.\n\nNo be by scrolling, na by practicing:\n👉 {BOT_USERNAME_LINK} → Type /score to see your rank\n\nDrop your mock score below, I go repost top 10 by 8pm! 👇"
    v3 = f"🏆 LEADERBOARD UPDATE — 1PM Check!\n\n{leaderboard_text}\n\nThese students started with 150/400 last month. Now see them!\n\nSecret? They use my bot daily + listen to VOICE explanations.\n\n🎧 Every answer inside bot has VOICE NOTE - I explain like your personal tutor.\n\nWanna join top 10?\n👉 {BOT_USERNAME_LINK} → Type /mock now\n\nScreenshot your score and drop here - I go hype you! 👇"
    
    msg = random.choice([v1,v2,v3])
    mark_posted("afternoon", hash_val)
    return msg

def generate_real_talk(stats_file="user_stats.json"):
    posted = get_posted_today()
    failing_topics = [
        "MATHS - Quadratic Equation",
        "English - Concord and Tenses",
        "Biology - Genetics and Variation",
        "Chemistry - Organic Chemistry",
        "Physics - Current Electricity",
        "MATHS - Trigonometry",
        "English - Lexis and Structure",
        "Biology - Ecology",
        "Chemistry - Stoichiometry",
        "Government - Constitution"
    ]
    
    failing_topic = random.choice(failing_topics)
    attempts = 0
    while failing_topic in posted.get("evening", []) and attempts < 10:
        failing_topic = random.choice(failing_topics)
        attempts += 1
    
    marks = "10 marks"
    if "Quadratic" in failing_topic:
        marks = "10 marks"
    elif "Concord" in failing_topic:
        marks = "15 marks"
    elif "Genetics" in failing_topic:
        marks = "8 marks"
    elif "Organic" in failing_topic:
        marks = "12 marks"
    
    short_topic = failing_topic.split("-")[-1].strip().lower()[:15]
    subject_part = failing_topic.split("-")[0].strip()
    
    v1 = f"😰 REAL TALK: JAMB IS 4 MONTHS AWAY\n\nIf you still score below 200 in mock, you need help FAST.\n\nOne topic is failing most of you: {failing_topic}.\n\nI made my bot teach it in 2 minutes with VOICE — even if you hate {subject_part}, you will understand.\n\n🎧 Listen now: {BOT_USERNAME_LINK} → Type /explain {short_topic}\n\nDon't sleep on this. 1 topic = {marks} in JAMB hall.\n\nWho listened? Comment 🔥 👇"
    v2 = f"😤 HONEST TRUTH — Stop deceiving yourself\n\nYou scroll TikTok 5 hours daily but you can't do 1 mock? JAMB no go pity you o.\n\nYour mates are failing {failing_topic} and it will carry {marks} for JAMB.\n\nInside {BOT_USERNAME_LINK} I explained {failing_topic} WITH VOICE NOTE - like I dey your front dey teach you.\n\nNo more excuse:\n👉 {BOT_USERNAME_LINK} → Type /tutor {failing_topic}\n\nI know many of you scored below 200 today. Make una no lie - comment your score below, I go help you personally 👇"
    v3 = f"🥺 8PM REALITY CHECK — Make I no lie you\n\nIf JAMB was tomorrow, many of you go score below 180. I see your mock scores inside bot.\n\nBut there's one topic if you master today, you go gain {marks} instantly: {failing_topic}.\n\nI recorded VOICE explanation inside bot - 2 minutes, you go understand even if you be dullard for {subject_part}.\n\n🎧 {BOT_USERNAME_LINK} → Type /explain {short_topic}\n\nAfter you listen, comment DONE - I want to know who serious 👇"
    v4 = f"🔥 NIGHT CLASS — {failing_topic.upper()} — 90% FAIL!\n\nI checked today's mock results - {failing_topic} killed many of you.\n\nJAMB will bring {marks} from this topic. If you fail am for hall, you don lose {marks} free.\n\nGood news: I don teach am for bot WITH VOICE. You go hear my voice explain am like real teacher.\n\n👉 {BOT_USERNAME_LINK} → Type /tutor {failing_topic}\n\nListen now before you sleep. Tomorrow morning I go ask question from am.\n\nWho don listen? Drop 🔥 for comment 👇"
    
    msg = random.choice([v1,v2,v3,v4])
    mark_posted("evening", failing_topic)
    return msg

def post_to_channel(text, bot_token, channel_id):
    if not bot_token or not channel_id:
        print(f"No token or channel ID. Would post: {text[:80]}...", flush=True)
        return False
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": channel_id, "text": text, "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if data.get("ok"):
            print(f"✅ Posted to channel {channel_id}", flush=True)
            return True
        else:
            print(f"❌ Channel post failed: {data}", flush=True)
            return False
    except Exception as e:
        print(f"Channel post exception: {e}", flush=True)
        return False

def channel_auto_poster_loop(bot_token, channel_id, cbt_engine, stats_file):
    print("📢 Channel auto-poster started - 8:30AM, 1PM, 8PM WAT", flush=True)
    posted_slots_today = set()
    last_date = ""
    while True:
        try:
            import datetime
            now_utc = datetime.datetime.utcnow()
            now_wat = now_utc + datetime.timedelta(hours=1)
            current_date = now_wat.strftime("%Y-%m-%d")
            hour = now_wat.hour
            minute = now_wat.minute
            if current_date != last_date:
                posted_slots_today = set()
                last_date = current_date
                print(f"New day {current_date} - reset", flush=True)
            should_post = None
            if hour == 8 and minute >= 30 and minute < 35 and "morning" not in posted_slots_today:
                should_post = "morning"
            elif hour == 13 and minute >= 0 and minute < 5 and "afternoon" not in posted_slots_today:
                should_post = "afternoon"
            elif hour == 20 and minute >= 0 and minute < 5 and "evening" not in posted_slots_today:
                should_post = "evening"
            if should_post:
                print(f"Time to post {should_post}", flush=True)
                if should_post == "morning":
                    msg = generate_morning_challenge(cbt_engine)
                elif should_post == "afternoon":
                    msg = generate_leaderboard(stats_file)
                else:
                    msg = generate_real_talk(stats_file)
                success = post_to_channel(msg, bot_token, channel_id)
                if success:
                    posted_slots_today.add(should_post)
            if os.path.exists("trigger_post.txt"):
                try:
                    with open("trigger_post.txt", "r") as f:
                        slot = f.read().strip()
                    os.remove("trigger_post.txt")
                    if slot in ["morning", "afternoon", "evening"]:
                        if slot == "morning":
                            msg = generate_morning_challenge(cbt_engine)
                        elif slot == "afternoon":
                            msg = generate_leaderboard(stats_file)
                        else:
                            msg = generate_real_talk(stats_file)
                        post_to_channel(msg, bot_token, channel_id)
                except:
                    pass
            time.sleep(60)
        except Exception as e:
            print(f"Auto-poster error: {e}", flush=True)
            time.sleep(60)

def start_channel_poster(bot_token, channel_id, cbt_engine, stats_file):
    thread = threading.Thread(target=channel_auto_poster_loop, args=(bot_token, channel_id, cbt_engine, stats_file), daemon=True)
    thread.start()
    print("📢 Channel poster thread started", flush=True)
    return thread
