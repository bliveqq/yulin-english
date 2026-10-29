from pathlib import Path
import json,re,unittest,hashlib
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets'
class NationalDataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ASSETS/'national-catalog.json').read_text());cls.qs=json.loads((ASSETS/'national-questions.json').read_text());cls.docs={d['id']:d for d in cls.catalog['files']}
 def test_unique_sources_and_previews(self):
  self.assertEqual(len(self.docs),len(self.catalog['files']))
  for d in self.docs.values():
   if d['status']=='text':self.assertGreater(len(json.loads((ASSETS/'national'/(d['id']+'.json')).read_text())['text']),200)
 def test_every_question_has_source_answer_explanation_and_options(self):
  self.assertEqual(len({q['id'] for q in self.qs}),len(self.qs))
  for q in self.qs:
   self.assertIn(q['sourceDocument'],self.docs);self.assertIn(q['answer'],'ABCD'[:len(q['options'])]);self.assertTrue(q['explain_cn']);self.assertGreaterEqual(len(q['options']),3);self.assertLessEqual(len(q['options']),4)
   if q['status']!='incomplete':
    answers=re.findall(r'(?:故选|答案[为是]|选项为)\s*([ABCD])',q['explain_cn'])
    if answers:self.assertEqual(answers[-1],q['answer'])
 def test_no_detached_reading_or_audio_questions(self):
  for q in self.qs:self.assertIsNone(re.search('阅读理解|细节理解|推理判断|推断题|主旨大意|词义猜测|完形填空|原文图片',q['stem']+q['explain_cn']))
 def test_source_sample_unchanged(self):
  for d in list(self.docs.values())[::200]:
   p=ROOT.parent/'2015-2026英语中考真题'/d['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),d['sha256'])
 def test_topic_codes_exist(self):
  codes={g['code'] for g in json.loads((ASSETS/'study-data.json').read_text())['grammar']}
  for q in self.qs:self.assertTrue(set(q['topics'])<=codes)
if __name__=='__main__':unittest.main()
