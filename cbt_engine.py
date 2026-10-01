``python
"""
UTME BOT CBT ENGINE - SAFE SYNC EDITIONS
- Pure synchronous past questions streaming execution structures
- Drops multi-thread loops to keep Render platform completely happy
"""

import requests
import random
import time

class CBTEngine:
    def __init__(self):
        self.db = ["Active Live API Mode"]
        print("📦 CBTEngine Cloud Directory Link Stabilized.", flush=True)
        self.active_exams = {}

    def fetch_exact_jamb_questions(self, subject, limit=5, year=None):
        api_subject = subject.lower().strip()
        url = f"https://aloc.ng{api_subject}&limit={limit}"
        
        if year and str(year).lower() != "all":
            url += f"&year={year}"
            
        headers = {
            "Accept": "application/json",
            "X-Public-Key": "anon_public_key_utme_success_bot_2026"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                raw_questions = data.get("data", [])
                
                clean_list = []
                for idx, q in enumerate(raw_questions):
                    raw_opts = q.get("option", {})
                    
                    clean_q = {
                        "id": q.get("id", int(time.time()) + idx),
                        "subject": subject,
                        "year": q.get("year", year or "Past JAMB Year"),
                        "topic": "JAMB Core Unit Mapped Focus",
                        "question": q.get("question", "Question context unavailable."),
                        "options": {
                            "A": raw_opts.get("a", "Option A choice descriptions"),
                            "B": raw_opts.get("b", "Option B choice descriptions"),
                            "C": raw_opts.get("c", "Option C choice descriptions"),
                            "D": raw_opts.get("d", "Option D choice descriptions")
                        },
                        "answer": str(q.get("answer", "A")).upper().strip(),
                        "explanation": q.get("solution", "Review official syllabus reference guides.")
                    }
                    clean_list.append(clean_q)
                return clean_list
        except Exception as e:
            print(f"⚠️ Cloud sync skip exception parameter: {e}", flush=True)
            
        return []

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=5, year=None):
        all_selected = []
        for subj in subjects:
            qs = self.fetch_exact_jamb_questions(subject=subj, limit=limit_per_subject, year=year)
            all_selected.extend(qs)
            
        random.shuffle(all_selected)
        
        if not all_selected:
            all_selected = [{
                "id": 88001, "subject": "General", "year": "2024", "topic": "Network Delay",
                "question": "The public archive took too long to stream. Check your connection or retry.",
                "options": {"A": "Retry Sync Loop", "B": "Check Network Status", "C": "Go Premium Tier", "D": "Contact Support"},
                "answer": "A", "explanation": "Stabilizing server latency ensures full past questions are pulled."
            }]
            
        self.active_exams[user_id] = {
            "questions": all_selected,
            "current_idx": 0,
            "score": 0,
            "answers": {},
            "start_time": time.time(),
            "duration": duration
        }
        return all_selected if all_selected else None, len(all_selected)

    def get_current_question(self, user_id):
        exam = self.active_exams.get(user_id)
        if not exam: return None, 0
        idx = exam['current_idx']
        if idx >= len(exam['questions']): return None, idx
        return exam['questions'][idx], idx

    def answer_current(self, user_id, option_letter):
        exam = self.active_exams.get(user_id)
        if not exam: return None, "NO_EXAM"
        idx = exam['current_idx']
        q = exam['questions'][idx]
        is_correct = (str(option_letter).upper() == str(q.get('answer','')).upper())
        exam['answers'][idx] = {"choice": option_letter.upper(), "is_correct": is_correct}
        if is_correct: exam['score'] += 1
        exam['current_idx'] += 1
        if exam['current_idx'] >= len(exam['questions']):
            return self.finish_exam(user_id), "FINISHED"
        return self.get_current_question(user_id), "NEXT"

    def finish_exam(self, user_id):
        exam = self.active_exams.pop(user_id, None)
        if not exam: return None
        total = len(exam['questions'])
        score = exam['score']
        jamb = int((score / total) * 400) if total else 0
        return {"raw_score": score, "total": total, "jamb_score": jamb}

    def get_time_left(self, user_id):
        exam = self.active_exams.get(user_id)
        if not exam: return 0
        return max(0, int(exam['duration'] - (time.time() - exam['start_time'])))
