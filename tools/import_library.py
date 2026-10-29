"""Read supplied database without mutation; build a compact indexed Android library."""
import sqlite3,json,hashlib,pathlib,re,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];SOURCE=ROOT.parent/'1/db/eng_teach.sqlite';OUT=ROOT/'assets/library-v110.sqlite';AUDIT=ROOT/'data-audit'
AUDIT.mkdir(exist_ok=True);before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
src=sqlite3.connect(SOURCE.resolve().as_uri()+'?mode=ro',uri=True);src.row_factory=sqlite3.Row
assert src.execute('pragma integrity_check').fetchone()[0]=='ok';assert not src.execute('pragma foreign_key_check').fetchall()
def rows(table):return [dict(r) for r in src.execute('select * from '+table)]
def parsed(v):return json.loads(v) if isinstance(v,str) else v
words=rows('words');grammar=rows('grammar_points');points=rows('exam_points');papers={r['id']:r for r in rows('papers')};questions=rows('questions')
changes=[];groups={}
for table in ['word_senses','word_forms','word_relations','question_points','question_words']:
 groups[table]=collections.defaultdict(list)
 for r in rows(table):groups[table][r.get('word_id',r.get('question_id'))].append(r)
assert len({w['headword'].strip().casefold() for w in words})==len(words)
assert all(g['parent_code'] is None or g['parent_code'] in {x['code'] for x in grammar} for g in grammar)
assert all(p['grammar_code'] is None or p['grammar_code'] in {x['code'] for x in grammar} for p in points)
if OUT.exists():OUT.unlink()
db=sqlite3.connect(OUT)
db.executescript('''PRAGMA user_version=110;
CREATE TABLE records(kind TEXT NOT NULL,id TEXT NOT NULL,title TEXT NOT NULL,subtitle TEXT NOT NULL,grade TEXT,difficulty INTEGER,status TEXT NOT NULL,parent TEXT,category TEXT,search TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(kind,id));
CREATE INDEX records_grade ON records(kind,grade,title);
CREATE INDEX records_status ON records(kind,status,title);
CREATE INDEX records_parent ON records(kind,parent);
CREATE INDEX records_category ON records(kind,category);
CREATE TABLE word_lookup(term TEXT COLLATE NOCASE NOT NULL,record_id TEXT NOT NULL,PRIMARY KEY(term,record_id));
CREATE TABLE links(from_kind TEXT,from_id TEXT,to_kind TEXT,to_id TEXT,UNIQUE(from_kind,from_id,to_kind,to_id));
CREATE INDEX link_reverse ON links(to_kind,to_id,from_kind);
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
''')
def pack(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def put(kind,id,title,subtitle,payload,grade=None,difficulty=None,status='reference',parent=None,category=None,search=None):
 db.execute('insert into records values(?,?,?,?,?,?,?,?,?,?,?)',(kind,str(id),title,subtitle,str(grade) if grade else None,difficulty,status,parent,category,search or (title+' '+subtitle).lower(),pack(payload)))
def link(a,b,c,d):db.execute('insert or ignore into links values(?,?,?,?)',(a,str(b),c,str(d)))
wordkeys={w['headword']:str(w['id']) for w in words}
for w in words:
 for k in ['pos','tags']:w[k]=parsed(w[k]) or []
 w['senses']=groups['word_senses'][w['id']];w['forms']=groups['word_forms'][w['id']];w['relations']=groups['word_relations'][w['id']]
 for sense in w['senses']:
  sense['collocations']=parsed(sense['collocations']) or []
  if w['headword']=='about' and sense['definition_cn']=='大约' and sense['pos']=='prep':sense['pos']='adv';changes.append({'record':'word:about','field':'sense:2.pos','before':'prep','after':'adv','reason':'about 表示大约、修饰数量时为副词。'})
 for f in w['forms']:
  if w['headword']=='be' and f['form_type']=='past' and f['form']=='was':
   f['form']='was / were';f['note']='I/he/she/it 用 was；you/we/they 用 were。';changes.append({'record':'word:be','field':'past','before':'was','after':'was / were','reason':'补齐 be 的过去式，避免遗漏 were。'})
 # Do not invent missing phonetics, frequencies or textbook units.
 w['source_label']='用户提供词库（AI 辅助编写，未逐条人工校审）'
 put('words',w['id'],w['headword'],w['meaning_cn'],w,w['grade_level'],w['difficulty'],search=(w['headword']+' '+w['meaning_cn']+' '+w['meaning_en']+' '+' '.join(w['tags'])).lower())
 aliases=[w['headword']]+[v.strip() for f in w['forms'] for v in re.split(r'\s*/\s*|;|,',f['form'])]
 for alias in aliases:db.execute('insert or ignore into word_lookup values(?,?)',(alias.lower(),str(w['id'])))
 for r in w['relations']:
  if r['related_word'] in wordkeys:link('words',w['id'],'words',wordkeys[r['related_word']])
for g in grammar:
 for k in ['rules','examples','common_errors']:g[k]=parsed(g[k]) or []
 g['source_label']='用户提供语法库（AI 辅助编写，教学前请核对）'
 put('grammar',g['code'],g['name_cn'],g['name_en'],g,difficulty=g['difficulty'],parent=g['parent_code'],search=(g['code']+' '+g['name_cn']+' '+g['name_en']+' '+g['explain_cn']).lower())
for p in points:
 for k in ['appearance_years','question_types']:p[k]=parsed(p[k]) or []
 p['source_label']='用户提供考点库；频次、权重为来源标注，非本应用统计结论'
 put('points',p['code'],p['name_cn'],p['name_en'],p,difficulty=p['difficulty'],parent=p['grammar_code'],category=p['category'],search=(p['code']+' '+p['name_cn']+' '+p['name_en']+' '+(p['trap_cn'] or '')).lower())
 if p['grammar_code']:link('points',p['code'],'grammar',p['grammar_code'])
statuses=collections.Counter();fingerprints=collections.defaultdict(list)
for q in questions:
 q['options']=parsed(q['options']) or [];q['paper']=papers[q['paper_id']];q['words']=[r['headword'] for r in groups['question_words'][q['id']]];q['exam_point_codes']=[r['exam_point_code'] for r in groups['question_points'][q['id']]]
 q['quality_notes']=[];q['status']='has_answer' if q['answer'] else 'missing_answer'
 if not q['answer']:q['quality_notes'].append('原资料未提供答案，不能自动判分。')
 if not q['explain_cn']:q['quality_notes'].append('原资料未提供解析。')
 if q['section']=='听力':q['status']='incomplete';q['quality_notes'].append('缺少音频或听力原文，不纳入课堂选题。')
 if q['id'] in [35,36]:q['status']='incomplete';q['quality_notes'].append('最后一个选项混入下一道题，保留原文待核对。')
 if q['id']==10:q['status']='incomplete';q['quality_notes'].append('选项 Fake it easy 疑似转录错误，题干末尾混入字符，暂不纳入课堂选题。')
 if q['id']==2:q['status']='incomplete';q['quality_notes'].append('凭发色、眼睛颜色推断国籍并不成立，此题不纳入课堂选题。')
 if q['id']==382 and 'X.ART.001' in q['exam_point_codes']:
  q['exam_point_codes']=[('X.ART.003' if x=='X.ART.001' else x) for x in q['exam_point_codes']];changes.append({'record':'question:382','field':'exam_point_codes','before':'X.ART.001','after':'X.ART.003','reason':'open the door 的语境为特指，不是 a/an 读音辨析。只修正关联，不补造来源答案。'})
 q['source_label']='用户提供的历史试题摘录；出处与参考答案未重新回源核验'
 statuses[q['status']]+=1
 fingerprint=hashlib.sha256(pack([' '.join(q['stem'].split()),q['options']]).encode()).hexdigest();fingerprints[fingerprint].append(q['id'])
 put('questions',q['id'],q['stem'],q['paper']['paper_name'],q,difficulty=q['difficulty'],status=q['status'],parent=q['paper']['code'],category=q['section'],search=(q['stem']+' '+q['paper']['paper_name']+' '+' '.join(q['words'])).lower())
 for word in q['words']:
  if word in wordkeys:link('questions',q['id'],'words',wordkeys[word])
 for code in q['exam_point_codes']:
  link('questions',q['id'],'points',code)
  point=next((x for x in points if x['code']==code),None)
  if point and point['grammar_code']:link('questions',q['id'],'grammar',point['grammar_code'])
for p in papers.values():
 p['excerpt_count']=sum(q['paper_id']==p['id'] for q in questions);p['source_label']='历史试题来源分组，不代表收录完整试卷'
 put('papers',p['code'],p['paper_name'],str(p['excerpt_count'])+' 道摘录题',p)
meta={'version':'1.1.0','source_sha256':before,'counts':{'words':len(words),'grammar':len(grammar),'points':len(points),'questions':len(questions),'papers':len(papers)},'question_status':dict(statuses),'missing_answers':sum(not q['answer'] for q in questions),'missing_phonetics':sum(not w['phonetic_uk'] and not w['phonetic_us'] for w in words),'all_questions_need_review':True,'source_label':'用户提供数据库 · 2026-10-27导入','corrections':len(changes)}
db.execute('insert into meta values(?,?)',('manifest',pack(meta)));db.commit();db.execute('ANALYZE');db.execute('VACUUM');assert db.execute('pragma integrity_check').fetchone()[0]=='ok';db.close();src.close()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
report={**meta,'source_file':str(SOURCE),'output_file':str(OUT),'duplicate_complete_question_groups':[ids for ids in fingerprints.values() if len(ids)>1],'changes':changes,'excluded_paths':['data/_fixtures','db/pgsql','etl','tmp_*'],'quality_scope':'结构、关联、缺失检查及3处明确修正；未逐条校审全部知识内容，未补造缺失答案、音标、教材单元。'}
(AUDIT/'import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(ROOT/'assets/library-manifest.json').write_text(pack(meta))
print(pack(meta));print('SQLite bytes:',OUT.stat().st_size)
