
import json, random, time, os

SUBJECTS = ["English","Mathematics","Biology","Chemistry","Physics","Economics","Government","Literature","Commerce","CRS"]

class CBTEngine:
    def __init__(self):
        self.db=[]
        loaded_files = []
        for i in range(1,11):
            pf=f"questions_part{i}.json"
            if os.path.exists(pf):
                try:
                    with open(pf,'r',encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.db.extend(data)
                            loaded_files.append(f"{pf}:{len(data)}")
                except Exception as e:
                    print(f"Load {pf} failed: {e}", flush=True)
        
        if os.path.exists("questions.json"):
            try:
                with open("questions.json",'r',encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > len(self.db):
                        self.db = data
                        loaded_files.append(f"questions.json:{len(data)} (used as main)")
            except:
                pass
        
        print(f"Loaded files: {loaded_files}", flush=True)
        print(f"Raw loaded: {len(self.db)} questions", flush=True)
        
        # Deduplicate ONLY by ID, NOT by text - FIX for 29 unique bug
        seen_ids=set()
        unique_by_id=[]
        for q in self.db:
            qid = q.get('id')
            if qid not in seen_ids:
                seen_ids.add(qid)
                unique_by_id.append(q)
        self.db = unique_by_id
        
        print(f"After ID dedup: {len(self.db)} unique IDs", flush=True)
        
        # If still less than 100, generate fallback - but now with PROPER unique generation
        if len(self.db) < 100:
            print(f"WARNING: Only {len(self.db)} Qs found, generating fallback 5000", flush=True)
            id_counter = 100000
            for subj in SUBJECTS:
                for year in range(2015, 2025):
                    for i in range(50):
                        self.db.append({
                            "id": id_counter,
                            "subject": subj,
                            "year": year,
                            "topic": "General",
                            "question": f"[{subj} {year}] Fallback Q{id_counter}: What is the correct answer for {subj} {year} topic {i+1}?",
                            "options": {"A": f"Correct Answer for {subj}", "B": "Option B", "C": "Option C", "D": "Option D"},
                            "answer": "A",
                            "explanation": f"Answer A is correct for {subj} {year}."
                        })
                        id_counter += 1
        
        # Final count
        from collections import Counter
        subj_counts = Counter([q.get('subject') for q in self.db])
        year_counts = Counter([str(q.get('year')) for q in self.db])
        print(f"CBTEngine FINAL: {len(self.db)} Qs | Subjects: {dict(subj_counts)} | Years sample: {dict(list(year_counts.items())[:5])}", flush=True)
        
        # Test critical: Chemistry 2020
        chem_2020 = [q for q in self.db if q.get('subject','').lower()=='chemistry' and str(q.get('year'))=='2020']
        print(f"CRITICAL CHECK: Chemistry 2020 = {len(chem_2020)} Qs (should be 400-500) - {'✅ PASS' if len(chem_2020) >= 100 else '❌ FAIL'}", flush=True)
        
        self.active_exams={}

    def get_questions(self, subject=None, year=None, limit=40, exclude_ids=None, exclude_texts=None):
        exclude_ids=set(exclude_ids or [])
        exclude_texts=set(exclude_texts or [])
        filtered=self.db
        
        if subject:
            subj_lower = subject.lower().strip()
            filtered=[q for q in filtered if q.get('subject','').lower().strip()==subj_lower]
            print(f"Filter subject={subject} -> {len(filtered)}", flush=True)
        
        if year is not None and str(year).strip() != "" and str(year).lower() != "all":
            year_str = str(year).strip()
            temp=[]
            for q in filtered:
                qy = q.get('year','')
                if str(qy).strip() == year_str:
                    temp.append(q)
                else:
                    try:
                        if int(qy) == int(year_str):
                            temp.append(q)
                    except:
                        if str(qy).lower() == year_str.lower():
                            temp.append(q)
            filtered=temp
            print(f"Year filter {subject} {year_str} -> {len(filtered)} found", flush=True)
        
        # Apply excludes
        filtered=[q for q in filtered if q.get('id') not in exclude_ids]
        if exclude_texts:
            filtered=[q for q in filtered if q.get('question','').strip().lower() not in exclude_texts]
        
        random.shuffle(filtered)
        
        # Return up to limit WITHOUT text dedup (allow same text if different IDs - but our data is unique now)
        result = filtered[:limit]
        print(f"get_questions subj={subject} year={year} limit={limit} -> returning {len(result)}", flush=True)
        return result

    def get_years(self, subject=None):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower().strip()]
        years=sorted(set([str(q.get('year')) for q in filtered if q.get('year')]), reverse=True)
        if not years:
            years = [str(y) for y in range(2024,2009,-1)]
        print(f"get_years for {subject}: {years}", flush=True)
        return years

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=10, year=None):
        all_selected=[]
        used_ids=set()
        used_texts=set()
        
        if year is not None and len(subjects)==1:
            print(f"Starting STRICT YEAR mock: {subjects[0]} {year}", flush=True)
            qs=self.get_questions(subject=subjects[0], year=year, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
            # If no Qs for strict year, fallback to all years for that subject
            if not qs:
                print(f"FALLBACK: No Qs for {subjects[0]} {year}, trying all years", flush=True)
                qs=self.get_questions(subject=subjects[0], year=None, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
            for q in qs:
                used_ids.add(q.get('id'))
                used_texts.add(q.get('question','').strip().lower())
                all_selected.append(q)
        else:
            for subj in subjects:
                qs=self.get_questions(subject=subj, year=None, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
                for q in qs:
                    used_ids.add(q.get('id'))
                    txt = q.get('question','').strip().lower()
                    if txt not in used_texts:
                        used_texts.add(txt)
                        all_selected.append(q)
        
        random.shuffle(all_selected)
        
        # Final dedup by ID only
        seen_final=set()
        deduped=[]
        for q in all_selected:
            qid = q.get('id')
            if qid not in seen_final:
                seen_final.add(qid)
                deduped.append(q)
        all_selected=deduped
        
        print(f"Mock started for {user_id}: {len(all_selected)} Qs, subjects={subjects}, year={year}", flush=True)
        
        self.active_exams[user_id]={"questions":all_selected,"current_idx":0,"score":0,"answers":{},"subjects":subjects,"start_time":time.time(),"duration":duration,"year":year}
        return all_selected[0] if all_selected else None, len(all_selected)

    def get_current_question(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam:
            return None,0
        idx=exam['current_idx']
        if idx>=len(exam['questions']):
            return None,idx
        return exam['questions'][idx],idx

    def answer_current(self, user_id, option_letter):
        exam=self.active_exams.get(user_id)
        if not exam:
            return None,"NO_EXAM"
        idx=exam['current_idx']
        if idx>=len(exam['questions']):
            return self.finish_exam(user_id),"FINISHED"
        q=exam['questions'][idx]
        is_correct=(option_letter.upper()==q['answer'].upper())
        exam['answers'][idx]={"user":option_letter.upper(),"correct":is_correct}
        if is_correct:
            exam['score']+=1
        exam['current_idx']+=1
        if exam['current_idx']>=len(exam['questions']):
            return self.finish_exam(user_id),"FINISHED"
        return self.get_current_question(user_id),"NEXT"

    def finish_exam(self, user_id):
        exam=self.active_exams.pop(user_id,None)
        if not exam:
            return None
        total=len(exam['questions'])
        score=exam['score']
        jamb=int((score/total)*400) if total else 0
        return {"raw_score":score,"total":total,"jamb_score":jamb,"answers":exam['answers'],"questions":exam['questions'],"subjects":exam['subjects'],"year":exam.get('year')}

    def get_time_left(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam:
            return 0
        elapsed=time.time()-exam['start_time']
        return max(0,int(exam['duration']-elapsed))
