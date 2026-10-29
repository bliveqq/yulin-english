import unittest,sqlite3,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LibraryTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(f'file:{ROOT}/assets/library-v110.sqlite?mode=ro',uri=True)
 def tearDown(self): self.db.close()
 def test_counts_integrity_and_links(self):
  self.assertEqual(self.db.execute('pragma integrity_check').fetchone()[0],'ok')
  self.assertEqual(dict(self.db.execute('select kind,count(*) from records group by kind')),dict(words=3918,grammar=311,points=423,questions=452,papers=37))
  self.assertEqual(self.db.execute('select count(*) from links l left join records r on r.kind=l.to_kind and r.id=l.to_id where r.id is null').fetchone()[0],0)
 def test_inflected_forms(self):
  for term,title in [('went','go'),('children','child'),('were','be')]:
   results=[r[0] for r in self.db.execute("select title from records where kind='words' and id in (select record_id from word_lookup where term=?)",(term,))]
   self.assertIn(title,results)
 def test_question_gaps_preserved(self):
  qs=[json.loads(r[0]) for r in self.db.execute("select payload from records where kind='questions'")]
  self.assertEqual(sum(not q['answer'] for q in qs),415)
  self.assertEqual(sum(q['status']=='incomplete' for q in qs),14)
  self.assertTrue(all(q['quality_notes'] for q in qs))
 def test_source_unchanged(self):
  report=json.loads((ROOT/'data-audit/import-report.json').read_text())
  self.assertEqual(hashlib.sha256(Path(report['source_file']).read_bytes()).hexdigest(),report['source_sha256'])
if __name__=='__main__':unittest.main()
