"""Verify the installed offline payload, not just its source directory."""
import hashlib,json,zipfile
from pathlib import Path
r=Path(__file__).resolve().parents[1];apk=r/'release/雨林英语-1.4.0-完整离线版.apk'
with zipfile.ZipFile(apk) as z:
 m=json.loads(z.read('assets/builtin-manifest.json'));catalog=json.loads(z.read('assets/national-catalog.json'))
 assert {x['path'] for x in catalog['files']}=={x['sourcePath'] for x in m['files']}
 assert len(m['files'])==2498
 for x in m['files']:
  name='assets/archive/'+x['sha256']+'.'+x['extension'];assert z.getinfo(name).file_size==x['bytes']
  with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256'],name
 for name in ['app.js','cloud.js','index.html']:
  assert z.read('assets/'+name)==(r/'assets'/name).read_bytes(),name
print('PASS: all 2498 built-in files match catalog, size and SHA-256; UI assets current.')
print('APK size:',apk.stat().st_size,'bytes')
