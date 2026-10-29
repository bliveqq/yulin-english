import sqlite3,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
c=sqlite3.connect(root/'assets/library-v110.sqlite')
data={k:[json.loads(r[0]) for r in c.execute('select payload from records where kind=? order by id',(k,))] for k in ['words','grammar','questions']}
enrichment=json.loads((root/'assets/study-enrichment.json').read_text())
for q in data['questions']:
 if str(q['id']) in enrichment:
  q['supplement']=enrichment[str(q['id'])]
  if 42<=q['id']<=49 and q['options'][-1].endswith(' '+q['answer']):
   q['options'][-1]=q['options'][-1][:-2]
   q['quality_notes'].append('学习副本已移除末选项尾部混入的答案字母，原文保留在原数据库。')
# Word-to-grammar associations only where present in the imported database.
data['wordGrammar']={}
for wid,gid in c.execute("select distinct w.to_id,g.to_id from links w join links g on w.from_kind=g.from_kind and w.from_id=g.from_id where w.from_kind='questions' and w.to_kind='words' and g.to_kind='grammar'"):
 data['wordGrammar'].setdefault(wid,[]).append(gid)
(root/'assets/study-data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
print({k:len(v) for k,v in data.items()})
