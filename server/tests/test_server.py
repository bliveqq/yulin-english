import hashlib,json,os,shutil,socket,subprocess,tempfile,time,unittest,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();lib=Path(cls.temp.name);(lib/'files').mkdir()
  cls.content=bytes(range(256))*40;sha=hashlib.sha256(cls.content).hexdigest();cls.key=f'files/{sha}.mp3';(lib/cls.key).write_bytes(cls.content)
  (lib/'manifest.json').write_text(json.dumps({'schema':1,'files':[{'path':cls.key}]}));(lib/'secret.txt').write_text('private')
  sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();cls.base=f'http://127.0.0.1:{port}'
  env=dict(os.environ,SITE_ADDRESS=cls.base,LIBRARY_ROOT=str(lib),SITE_ROOT=str(ROOT/'site'))
  cls.log=tempfile.TemporaryFile();cls.process=subprocess.Popen([os.environ.get('CADDY_BIN') or shutil.which('caddy') or str(ROOT.parent/'tools/caddy/caddy'),'run','--config',str(ROOT/'Caddyfile'),'--adapter','caddyfile'],env=env,stdout=cls.log,stderr=cls.log)
  for _ in range(50):
   try:
    with urllib.request.urlopen(cls.base+'/healthz',timeout=1) as r:assert r.status==200
    return
   except Exception:time.sleep(.1)
  cls.process.terminate();cls.process.wait();cls.log.seek(0);raise RuntimeError(cls.log.read().decode())
 @classmethod
 def tearDownClass(cls):cls.process.terminate();cls.process.wait(timeout=5);cls.log.close();cls.temp.cleanup()
 def request(self,path,**kwargs):
  try:return urllib.request.urlopen(urllib.request.Request(self.base+path,**kwargs),timeout=3)
  except urllib.error.HTTPError as e:return e
 def test_full_download(self):
  with self.request('/english/'+self.key) as r:self.assertEqual(r.status,200);self.assertEqual(r.read(),self.content)
 def test_resume_and_invalid_range(self):
  with self.request('/english/'+self.key,headers={'Range':'bytes=100-'}) as r:self.assertEqual(r.status,206);self.assertEqual(r.read(),self.content[100:]);self.assertEqual(r.headers['Content-Range'],f'bytes 100-10239/10240')
  with self.request('/english/'+self.key,headers={'Range':'bytes=20000-'}) as r:self.assertEqual(r.status,416)
 def test_partial_audio(self):
  with self.request('/english/'+self.key,headers={'Range':'bytes=0-3'}) as r:self.assertEqual(r.status,206);self.assertEqual(r.read(),self.content[:4])
 def test_manifest_and_head(self):
  with self.request('/english/manifest.json') as r:self.assertEqual(json.load(r)['schema'],1);self.assertIn('max-age=300',r.headers['Cache-Control'])
  with self.request('/english/'+self.key,method='HEAD') as r:self.assertEqual(int(r.headers['Content-Length']),len(self.content));self.assertEqual(r.read(),b'')
 def test_private_paths_and_upload_denied(self):
  for path in ['/english/secret.txt','/english/files/','/.env','/Caddyfile','/english/../secret.txt','/_upload/test']:
   with self.request(path) as r:self.assertEqual(r.status,404,path)
  with self.request('/english/manifest.json',method='PUT',data=b'bad') as r:self.assertEqual(r.status,405)
 def test_home_and_status(self):
  with self.request('/') as r:self.assertIn('雨林英语',r.read().decode())
  with self.request('/api/status') as r:self.assertFalse(json.load(r)['aiConfigured'])
if __name__=='__main__':unittest.main()
