import json
import random
import time
import os

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

class CBTEngine:
    def __init__(self):
        self.db = []
        loaded_files = []
        
        for i in range(1, 11):
            pf = f"questions_part{i}.json"
            if os.path.exists(pf):
                try:
                    with open(pf, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.db.extend(data)
                            loaded_files.append(f"{pf}:{len(data)}")
                except Exception as e:
                    print(f"Load error on shard extraction {pf}: {e}", flush=True)
                    
        if os.path.exists("questions.json"):
            try:
                with open("questions.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list): self.db.extend(data)
            except: pass

        seen_ids = set()
        seen_texts = set()
        unique = []
        
        for q in self.db:
            qid = q.get('id')
            qtext = str(q.get('question', '')).strip()
            opts = q.get('options', {})
            
            if qid in seen_ids or not qtext or not opts or not q.get('answer'): continue
            
            # CRITICAL FILTER FIX: Safely weed out all unformatted or corrupt data entries
            if "Q55" in qtext or len(qtext) < 25 or "placeholder" in qtext.lower(): continue
            if opts.get('A') == 'Correct' and opts.get('B') == 'B' and opts.get('C') == 'C': continue
            
            seen_ids.add(qid)
            seen_texts.add(qtext.lower())
            unique.append(q)
            
        self.db = unique
        
        # Standalone verified dataset fallback arrays model populate mechanism
        if len(self.db) < 5:
            self.db = [
                {
                    "id": 50001, "subject": "Mathematics", "year": "2024", "topic": "Calculus",
                    "question": "Find the derivative of f(x) = 3x^2 + 5x - 2 with respect to x.",
                    "options": {"A": "6x + 5", "B": "3x + 5", "C": "6x", "D": "x^3 + 5"},
                    "answer": "A", "explanation": "Using the power rule, the derivative of 3x^2 is 6x, and the derivative of 5x is 5. Constants disappear."
                },
                {
                    "id": 50002, "subject": "English", "year": "2024", "topic": "Lexis",
                    "question": "Choose the word nearest in meaning to the italicized word: The council's decision was 'imperative' for completion.",
                    "options": {"A": "Optional", "B": "Crucial", "C": "Secondary", "D": "Trivial"},
                    "answer": "B", "explanation": "Imperative means of vital importance or crucial."
                }
            ]
        print(f"📦 CBTEngine Matrix Active. Mapped Clean Records Count: {len(self.db)} proper items.", flush=True)
        self.active_exams = {}

    def get_questions(self, subject=None, year=None, limit=10):
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if str(q.get('subject','')).lower().strip() == subject.lower().strip()]
        if year and str(year).lower() != "all":
            filtered = [q for q in filtered if str(q.get('year','')).strip() == str(year).strip()]
        pool = list(filtered)
        random.shuffle(pool)
        return pool[:limit]

    def get_years(self, subject=None):
        filtered = self.db
        if subject:
            filtered = [q for q in filtered if str(q.get('subject','')).lower().strip() == subject.lower().strip()]
        return sorted(list(set([str(q.get('year')) for q in filtered if q.get('year')])), reverse=True)

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=5):
        all_selected = []
        for subj in subjects:
            qs = self.get_questions(subject=subj, limit=limit_per_subject)
            all_selected.extend(qs)
        random.shuffle(all_selected)
        if not all_selected: return None, 0
        self.active_exams[user_id] = {
            "questions": all_selected, "current_idx": 0, "score": 0, "answers": {},
            "start_time": time.time(), "duration": duration
        }
        return all_selected[0], len(all_selected)

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
