
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
        
        print(f"Loaded files: {loaded_files}", flush=True)
        print(f"Raw loaded: {len(self.db)} questions", flush=True)
        
        # Deduplicate ONLY by ID - keep all unique questions
        seen_ids=set()
        unique_by_id=[]
        for q in self.db:
            qid = q.get('id')
            if qid not in seen_ids and qid is not None:
                seen_ids.add(qid)
                # Ensure required fields exist
                if q.get('question') and q.get('options') and q.get('answer'):
                    unique_by_id.append(q)
        self.db = unique_by_id
        
        print(f"After ID dedup and validation: {len(self.db)} unique IDs", flush=True)
        
        if len(self.db) < 100:
            print(f"WARNING: Only {len(self.db)} Qs, generating fallback", flush=True)
            id_counter = 100000
            for subj in SUBJECTS:
                for year in range(2015, 2025):
                    for i in range(50):
                        self.db.append({
                            "id": id_counter,
                            "subject": subj,
                            "year": year,
                            "topic": "General",
                            "question": f"[{subj} {year}] Fallback Q{id_counter}: What is correct for {subj} {year}?",
                            "options": {"A": f"Correct {subj}", "B": "Option B", "C": "Option C", "D": "Option D"},
                            "answer": "A",
                            "explanation": f"Answer A is correct for {subj} {year}."
                        })
                        id_counter += 1
        
        from collections import Counter
        subj_counts = Counter([q.get('subject') for q in self.db])
        year_counts = Counter([str(q.get('year')) for q in self.db])
        print(f"CBTEngine v13 FINAL: {len(self.db)} Qs | Subjects: {dict(subj_counts)}", flush=True)
        print(f"Years: {dict(year_counts)}", flush=True)
        
        # Critical checks
        for subj in SUBJECTS:
            for yr in [2020, 2019, 2024]:
                count = len([q for q in self.db if q.get('subject','').lower()==subj.lower() and str(q.get('year'))==str(yr)])
                if count < 100:
                    print(f"⚠️ {subj} {yr}: only {count} Qs", flush=True)
        
        chem_2020 = [q for q in self.db if q.get('subject','').lower()=='chemistry' and str(q.get('year'))=='2020']
        print(f"✅ CRITICAL: Chemistry 2020 = {len(chem_2020)} Qs - {'PASS' if len(chem_2020) >= 400 else 'FAIL'}", flush=True)
        
        self.active_exams={}

    def get_questions(self, subject=None, year=None, limit=40, exclude_ids=None, exclude_texts=None):
        """v13 - Guaranteed no repetition, exact year+subject match"""
        exclude_ids=set(exclude_ids or [])
        exclude_texts=set([t.strip().lower() for t in (exclude_texts or []) if t])
        filtered=self.db
        
        if subject:
            subj_lower = subject.lower().strip()
            filtered=[q for q in filtered if q.get('subject','').lower().strip()==subj_lower]
        
        if year is not None and str(year).strip() != "" and str(year).lower() != "all":
            year_str = str(year).strip()
            # STRICT year match - no fallback here, exact match only
            filtered=[q for q in filtered if str(q.get('year','')).strip()==year_str]
            print(f"STRICT Filter: {subject} {year_str} -> {len(filtered)} found", flush=True)
        
        # Apply excludes for zero repetition
        filtered=[q for q in filtered if q.get('id') not in exclude_ids]
        filtered=[q for q in filtered if q.get('question','').strip().lower() not in exclude_texts]
        
        random.shuffle(filtered)
        
        # Ensure no duplicates in returned list itself (by ID and text)
        seen_ids=set()
        seen_texts=set()
        result=[]
        for q in filtered:
            qid = q.get('id')
            qtext = q.get('question','').strip().lower()
            if qid not in seen_ids and qtext not in seen_texts and qid not in exclude_ids and qtext not in exclude_texts:
                seen_ids.add(qid)
                seen_texts.add(qtext)
                result.append(q)
                if len(result) >= limit:
                    break
        
        print(f"get_questions {subject} {year} limit={limit} exclude={len(exclude_ids)} -> returning {len(result)} UNIQUE", flush=True)
        return result

    def get_years(self, subject=None):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower().strip()]
        years=sorted(set([str(q.get('year')) for q in filtered if q.get('year')]), reverse=True)
        if not years:
            years = [str(y) for y in range(2024,2014,-1)]
        print(f"get_years {subject}: {years}", flush=True)
        return years

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=10, year=None):
        """v13 - ZERO repetition guarantee for entire mock"""
        all_selected=[]
        used_ids=set()
        used_texts=set()
        
        print(f"\n=== Starting Mock v13 ZERO REPETITION ===", flush=True)
        print(f"User={user_id} Subjects={subjects} Year={year} LimitPerSubj={limit_per_subject}", flush=True)
        
        if year is not None and len(subjects)==1:
            # Past question mode - strict year
            print(f"PAST QUESTION MODE: {subjects[0]} {year}", flush=True)
            qs=self.get_questions(subject=subjects[0], year=year, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
            if not qs:
                print(f"❌ No Qs for {subjects[0]} {year}, fallback to all years for that subject", flush=True)
                qs=self.get_questions(subject=subjects[0], year=None, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
            
            for q in qs:
                qid = q.get('id')
                qtext = q.get('question','').strip().lower()
                if qid not in used_ids and qtext not in used_texts:
                    used_ids.add(qid)
                    used_texts.add(qtext)
                    all_selected.append(q)
            
            print(f"Past Qs selected: {len(all_selected)} unique for {subjects[0]} {year}", flush=True)
        else:
            # Full mock mode - multiple subjects, ensure zero repetition across all
            for subj in subjects:
                qs=self.get_questions(subject=subj, year=None, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
                print(f"Subject {subj}: got {len(qs)} unique (excluded {len(used_ids)} already used)", flush=True)
                for q in qs:
                    qid = q.get('id')
                    qtext = q.get('question','').strip().lower()
                    if qid not in used_ids and qtext not in used_texts:
                        used_ids.add(qid)
                        used_texts.add(qtext)
                        all_selected.append(q)
                    else:
                        print(f"⚠️ Skipped duplicate ID {qid}", flush=True)
        
        # Final shuffle and final dedup check
        random.shuffle(all_selected)
        
        # Absolute final check - no duplicates by ID or text
        seen_final_ids=set()
        seen_final_texts=set()
        deduped=[]
        for q in all_selected:
            qid = q.get('id')
            qtext = q.get('question','').strip().lower()
            if qid not in seen_final_ids and qtext not in seen_final_texts:
                seen_final_ids.add(qid)
                seen_final_texts.add(qtext)
                deduped.append(q)
        
        all_selected=deduped
        
        # Verify zero repetition
        if len(all_selected) != len(set(q.get('id') for q in all_selected)):
            print(f"❌ CRITICAL: Duplicate IDs found in final mock!", flush=True)
        if len(all_selected) != len(set(q.get('question','').strip().lower() for q in all_selected)):
            print(f"❌ CRITICAL: Duplicate texts found in final mock!", flush=True)
        
        print(f"✅ Mock started for {user_id}: {len(all_selected)} UNIQUE Qs, ZERO repetition verified", flush=True)
        print(f"IDs: {[q.get('id') for q in all_selected[:5]]}... (first 5)", flush=True)
        
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
        # Verify no repetition in finished exam
        ids = [q.get('id') for q in exam['questions']]
        if len(ids) != len(set(ids)):
            print(f"❌ Finished exam had duplicate IDs!", flush=True)
        return {"raw_score":score,"total":total,"jamb_score":jamb,"answers":exam['answers'],"questions":exam['questions'],"subjects":exam['subjects'],"year":exam.get('year')}

    def get_time_left(self, user_id):
        exam=self.active_exams.get(user_id)
        if not exam:
            return 0
        elapsed=time.time()-exam['start_time']
        return max(0,int(exam['duration']-elapsed))
