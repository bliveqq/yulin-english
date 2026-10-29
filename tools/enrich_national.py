import json,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'assets/national-questions.json';qs=json.loads(p.read_text());d=json.loads((ROOT/'assets/study-data.json').read_text());gs=d['grammar']
patterns={'宾语从句':'G.CLAUSE.001','定语从句':'G.CLAUSE.002','时间状语从句':'G.CLAUSE.003','条件状语从句':'G.CLAUSE.004','让步状语从句':'G.CLAUSE.004','目的状语从句':'G.CLAUSE.005','原因状语从句':'G.CLAUSE.005','结果状语从句':'G.CLAUSE.005','主谓一致':'G.SPECIAL.001','情景交际':'G.SPECIAL.002','情境交际':'G.SPECIAL.002','反意疑问':'G.SENTENCE.004','祈使句':'G.SENTENCE.005','感叹句':'G.INVERSION.004','倒装':'G.INVERSION','非谓语':'G.NONFINITE','不定式':'G.NONFINITE.001','动名词':'G.NONFINITE.002','数词':'G.NUM','介词':'G.PREP','代词':'G.PRON','名词辨析':'G.NOUN','名词词义':'G.NOUN','形容词辨析':'G.ADJ','副词辨析':'G.ADV','比较级':'G.ADJ.002','最高级':'G.ADJ.002','冠词':'G.ART','被动语态':'G.VERB_VOICE','情态动词':'G.MODAL','连词':'G.CONJ','动词短语':'G.WORDCLASS.001','动词词义':'G.WORDCLASS.004','词义辨析':'G.WORDCLASS.004','时态':'G.VERB_TENSE','一般现在时':'G.VERB_TENSE.001','一般过去时':'G.VERB_TENSE.002','现在进行时':'G.VERB_TENSE.003','过去进行时':'G.VERB_TENSE.004','一般将来时':'G.VERB_TENSE.005','过去将来时':'G.VERB_TENSE.006','现在完成时':'G.VERB_TENSE.007','过去完成时':'G.VERB_TENSE.008'}
gmap={g['code']:g for g in gs};words={w['headword'].lower():str(w['id']) for w in d['words']};wordTopics=collections.defaultdict(set)
for q in qs:
 ex=q['explain_cn'];subjects=re.findall(r'考[查察]([^。\n]{2,100})',ex);subject=' '.join(subjects)
 tags=set(v for k,v in patterns.items() if k in subject)
 for g in gs:
  if len(g['name_cn'])>=4 and g['name_cn'] in subject:tags.add(g['code'])
 for code in list(tags):
  parent=gmap.get(code,{}).get('parent_code')
  while parent:tags.add(parent);parent=gmap.get(parent,{}).get('parent_code')
 q['topics']=sorted(tags);q['suggestedDifficulty']='3' if sum(x in subject for x in ['时态','被动语态','从句'])>=2 else '2' if any(x in subject for x in ['从句','完成时','被动语态','非谓语','反意疑问','比较级','最高级']) else '1';q['suggestedDifficulty']=q['suggestedDifficulty'] if tags else None;q['difficultyBasis']='依照解析考点给出的学习建议，非官方难度或得分率统计。'
 conclusions=re.findall(r'(?:故选|答案[为是]|选项为)\s*([ABCD])',ex)
 if conclusions and conclusions[-1]!=q['answer']:
  q['status']='incomplete';q['quality_notes'].append('答案字母与解析结论存在冲突，需核对原文件，暂不判分。')
 for token in set(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",q['stem']+' '+' '.join(q['options']))):
  wid=words.get(token.lower())
  if wid:wordTopics[wid].update(tags)
p.write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')))
(ROOT/'assets/national-word-topics.json').write_text(json.dumps({k:sorted(v) for k,v in wordTopics.items()},ensure_ascii=False,separators=(',',':')))
print('Questions',len(qs),'with suggested topics',sum(bool(q['topics']) for q in qs),'word associations',len(wordTopics))
