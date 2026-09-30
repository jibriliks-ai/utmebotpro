```python
import json
import random
import time
import os

class CBTEngine:
    def __init__(self):
        self.db = []
        loaded_files = []
        
        # Look across all 10 standard partitions inside your project folder structure
        for i in range(1, 11):
            pf = f"questions_part{i}.json"
            if os.path.exists(pf):
                try:
                    with open(pf, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.db.extend(data)
                            loaded_files.append(f"{pf}:{len(data)}")
                except:
                    pass
                    
        if os.path.exists("questions.json"):
            try:
                with open("questions.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > len(self.db):
                        self.db = data
                        loaded_files.append(f"questions.json:{len(data)}")
            except:
                pass
                
        # Deduplicate records instantly by primary keys
        seen_ids = set()
        uniq = []
        for q in self.db:
            qid = q.get('id')
            if qid not in seen_ids:
                seen_ids.add(qid)
                uniq.append(q)
        self.db = uniq
        
        # PROPER FALLBACK DATA FIX (Prevents unformatted question templates)
        if len(self.db) < 5:
            self.db = [
                {
                    "id": 10001,
                    "subject": "Mathematics",
                    "year": 2016,
                    "topic": "Algebra",
                    "question": "Solve for x if 2x + 5 = 15.",
                    "options": {
                        "A": "x = 5",
                        "B": "x = 10",
                        "C": "x = 15",
                        "D": "x = 20"
                    },
                    "answer": "A",
                    "explanation": "Subtract 5 from both sides to get 2x = 10. Dividing by 2 yields x = 5."
                },
                {
                    "id": 10002,
                    "subject": "Mathematics",
                    "year": 2017,
                    "topic": "Geometry",
                    "question": "What is the sum of angles in a triangle?",
                    "options": {
                        "A": "90 degrees",
                        "B": "180 degrees",
                        "C": "270 degrees",
                        "D": "360 degrees"
                    },
                    "answer": "B",
                    "explanation": "According to the triangle angle sum theorem, the interior angles always add up to 180 degrees."
                }
            ]
        print(f"📦 CBTEngine Pipeline Setup Complete. Active elements records: {len(self.db)}")
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
        if not all_selected:
            return None, 0
            
        self.active_exams[user_id] = {
            "questions": all_selected,
            "current_idx": 0,
            "score": 0,
            "answers": {},
            "start_time": time.time(),
            "duration": duration
        }
        return all_selected[0] if all_selected else None, len(all_selected)

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
        is_correct = (str(option_letter).upper() == str(q.get('answer')).upper())
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
        elapsed = time.time() - exam['start_time']
        return max(0, int(exam['duration'] - elapsed))
