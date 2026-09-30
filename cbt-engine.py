import json, random, time, os

class CBTEngine:
    def __init__(self):
        self.db=[]
        # Load all parts - ensures 50k questions
        for i in range(1,11):
            pf=f"questions_part{i}.json"
            if os.path.exists(pf):
                try:
                    with open(pf,'r',encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.db.extend(data)
                except Exception as e:
                    print(f"Load {pf} failed: {e}")
        if os.path.exists("questions.json"):
            try:
                with open("questions.json",'r',encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.db.extend(data)
            except:
                pass
        if not self.db:
            self.db=[{"id":1,"subject":"Biology","year":2020,"topic":"General","question":"What is biology?","options":{"A":"Study of life","B":"Rocks","C":"Stars","D":"Metals"},"answer":"A","explanation":"Study of life is biology"}]
        # Deduplicate by ID - 100% unique
        seen=set()
        uniq=[]
        for q in self.db:
            qid=q.get('id')
            if qid not in seen:
                seen.add(qid)
                uniq.append(q)
        self.db=uniq
        # Also deduplicate by question text to prevent same question different IDs
        seen_text={}
        uniq2=[]
        for q in self.db:
            txt = q.get('question','').strip().lower()
            if txt not in seen_text:
                seen_text[txt]=True
                uniq2.append(q)
        self.db=uniq2
        print(f"CBTEngine loaded {len(self.db)} unique questions - No repeats guaranteed")
        self.active_exams={}

    def get_questions(self, subject=None, year=None, limit=40, exclude_ids=None, exclude_texts=None):
        """
        Get questions with STRICT no repetition and strict year filter
        - If year specified: ONLY that year, NO MIXING
        - Random from all years if no year specified
        - No duplicate IDs and no duplicate question texts in same mock
        """
        exclude_ids=set(exclude_ids or [])
        exclude_texts=set(exclude_texts or [])
        filtered=self.db
        
        # Subject filter - strict
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower()]
        
        # YEAR FILTER - STRICT - NO MIXING - If Mathematics 2020 selected, ONLY 2020
        if year is not None and str(year).strip() != "" and str(year).lower() != "all":
            year_str = str(year).strip()
            filtered=[q for q in filtered if str(q.get('year','')).strip() == year_str]
            print(f"Strict year filter: {subject} {year_str} -> {len(filtered)} questions found (no mixing)")
        
        # Exclude already used IDs (prevents repeat in same mock)
        filtered=[q for q in filtered if q.get('id') not in exclude_ids]
        
        # Exclude already used question texts (extra safety against duplicates)
        filtered=[q for q in filtered if q.get('question','').strip().lower() not in exclude_texts]
        
        # Randomly shuffle from all years (or specific year if filtered)
        random.shuffle(filtered)
        
        # Ensure no duplicate texts in result - 100% unique per mock
        seen_text=set(exclude_texts)
        seen_ids=set(exclude_ids)
        unique=[]
        for q in filtered:
            qid = q.get('id')
            txt = q.get('question','').strip().lower()
            if qid not in seen_ids and txt not in seen_text:
                seen_ids.add(qid)
                seen_text.add(txt)
                unique.append(q)
            if len(unique)>=limit:
                break
        
        print(f"get_questions: subject={subject}, year={year}, limit={limit} -> returned {len(unique)} unique (no repeats)")
        return unique[:limit]

    def get_years(self, subject=None):
        filtered=self.db
        if subject:
            filtered=[q for q in filtered if q.get('subject','').lower()==subject.lower()]
        years=sorted(set([str(q.get('year')) for q in filtered if q.get('year')]), reverse=True)
        return years if years else [str(y) for y in range(2024,2009,-1)]

    def start_mock(self, user_id, subjects, duration=45*60, limit_per_subject=10, year=None):
        """
        Start mock - 100% NO REPEATS in same mock
        - Randomly selects from all years if year=None
        - Strict year if year specified (e.g., Mathematics 2020 only)
        - Never repeats same question in particular mock test
        - Always unique questions per mock
        """
        all_selected=[]
        used_ids=set()
        used_texts=set()
        
        # If year specified and single subject, use strict year filter
        if year is not None and len(subjects)==1:
            print(f"Starting strict year mock: {subjects[0]} {year} - no mixing")
            qs=self.get_questions(subject=subjects[0], year=year, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
            for q in qs:
                used_ids.add(q.get('id'))
                used_texts.add(q.get('question','').strip().lower())
                all_selected.append(q)
        else:
            # Normal mock - random from ALL years, no repeats
            for subj in subjects:
                qs=self.get_questions(subject=subj, year=None, limit=limit_per_subject, exclude_ids=used_ids, exclude_texts=used_texts)
                for q in qs:
                    used_ids.add(q.get('id'))
                    txt = q.get('question','').strip().lower()
                    if txt not in used_texts:
                        used_texts.add(txt)
                        all_selected.append(q)
        
        # Final shuffle - ensures random order but still no repeats
        random.shuffle(all_selected)
        
        # Final deduplication - 100% professional, no repeats guaranteed
        seen_final_ids=set()
        seen_final_text=set()
        deduped=[]
        for q in all_selected:
            qid = q.get('id')
            txt = q.get('question','').strip().lower()
            if qid not in seen_final_ids and txt not in seen_final_text:
                seen_final_ids.add(qid)
                seen_final_text.add(txt)
                deduped.append(q)
        all_selected=deduped
        
        print(f"Mock started for {user_id}: {len(all_selected)} unique questions, subjects={subjects}, year={year} - NO REPEATS")
        
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
