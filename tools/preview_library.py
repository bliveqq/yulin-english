"""Local UI verification only; Android production uses LibraryStore.java."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import json,sqlite3,pathlib,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'assets'),**kw)
 def do_POST(self):
  try:
   body=json.loads(self.rfile.read(int(self.headers.get('content-length','0'))) or '{}')
   with sqlite3.connect((ROOT/'assets/library-v110.sqlite').as_uri()+'?mode=ro',uri=True) as db:
    db.row_factory=sqlite3.Row
    kind=body.get('kind','words');id=str(body.get('id',''));q=body.get('query','').strip()
    if self.path=='/api/library/meta':result=json.loads(db.execute("select value from meta where key='manifest'").fetchone()[0])
    elif self.path=='/api/library/detail':
     row=db.execute('select payload from records where kind=? and id=?',(kind,id)).fetchone()
     if not row:raise ValueError('未找到资料')
     result={'record':json.loads(row[0]),'related':[dict(r) for r in db.execute('SELECT r.kind,r.id,r.title,r.subtitle,r.grade,r.difficulty,r.status FROM records r JOIN (SELECT to_kind kind,to_id id FROM links WHERE from_kind=? AND from_id=? UNION SELECT from_kind kind,from_id id FROM links WHERE to_kind=? AND to_id=?) l ON r.kind=l.kind AND r.id=l.id ORDER BY r.kind,r.title LIMIT 60',(kind,id,kind,id))],'children':[dict(r) for r in db.execute('select kind,id,title,subtitle,grade,difficulty,status from records where kind=? and parent=? order by id limit 100',(kind,id))]}
    elif self.path=='/api/library/query':
     where='kind=?';args=[kind]
     if q:
      where+=' AND (search LIKE ? ESCAPE "\\"';args+=['%'+q.lower().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%']
      if kind=='words':where+=' OR id in (select record_id from word_lookup where term=? COLLATE NOCASE)';args+=[q]
      where+=')'
     for key in ['grade','status','parent','category']:
      if body.get(key) and body[key]!='all':where+=' AND '+key+'=?';args+=[body[key]]
     total=db.execute('select count(*) from records where '+where,args).fetchone()[0];limit=min(40,max(1,int(body.get('limit',24))));offset=max(0,int(body.get('offset',0)))
     order='title COLLATE NOCASE,id';orderargs=[]
     if q and kind=='words':order='CASE WHEN title=? COLLATE NOCASE THEN 0 WHEN id IN (SELECT record_id FROM word_lookup WHERE term=? COLLATE NOCASE) THEN 1 ELSE 2 END,'+order;orderargs=[q,q]
     result={'total':total,'offset':offset,'limit':limit,'items':[dict(r) for r in db.execute('select kind,id,title,subtitle,grade,difficulty,status from records where '+where+' ORDER BY '+order+' LIMIT ? OFFSET ?',args+orderargs+[limit,offset])]}
    else:raise ValueError('此本地预览不提供AI服务')
   raw=json.dumps(result,ensure_ascii=False).encode();self.send_response(200)
  except Exception as e:raw=json.dumps({'error':str(e)},ensure_ascii=False).encode();self.send_response(400)
  self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8770),Handler).serve_forever()
