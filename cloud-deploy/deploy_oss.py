"""Publish the prepared library using separately configured ossutil credentials."""
import argparse,hashlib,json,re,subprocess,sys,urllib.parse
from pathlib import Path
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description='Upload files first, then publish manifest. No cloud resources or access permissions are changed.')
p.add_argument('--bucket',required=True);p.add_argument('--region',required=True);p.add_argument('--endpoint',required=True)
p.add_argument('--cname',action='store_true');p.add_argument('--profile',default='yulin');p.add_argument('--execute',action='store_true')
a=p.parse_args()
if not re.fullmatch('[a-z0-9][a-z0-9-]{1,61}[a-z0-9]',a.bucket):p.error('Invalid bucket name')
u=urllib.parse.urlsplit(a.endpoint)
if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):p.error('Endpoint must be a clean HTTPS origin')
manifest=json.loads((root/'public/manifest.json').read_text())
for x in manifest['files']:
 expected=f"files/{x['sha256']}.{x['extension']}"
 if x['path']!=expected or not re.fullmatch(r'files/[a-f0-9]{64}\.[a-z0-9]+',expected):raise ValueError('Invalid manifest path')
 f=root/'public'/expected
 if f.stat().st_size!=x['bytes'] or hashlib.file_digest(f.open('rb'),'sha256').hexdigest()!=x['sha256']:raise ValueError('Local file integrity failed: '+x['id'])
print('Local integrity verified:',len(manifest['files']),'files')
exe=root.parent/'tools/ossutil/ossutil-2.4.0-mac-arm64/ossutil'
base=[str(exe),'--profile',a.profile,'--region',a.region,'--endpoint',a.endpoint]
if a.cname:base+=['--addressing-style','cname']
dest=f'oss://{a.bucket}/english/'
commands=[base+['cp',str(root/'public/files')+'/',dest+'files/','--recursive','--force','--cache-control','public,max-age=31536000,immutable'],base+['cp',str(root/'public/manifest.json'),dest+'manifest.json','--force','--cache-control','public,max-age=300']]
if not a.execute:
 print('Preparation only. Nothing uploaded. Add --execute after configuring credentials locally.')
 for command in commands:print(json.dumps(command,ensure_ascii=False))
 sys.exit(0)
for command in commands:subprocess.run(command,check=True)
print('Upload finished. Public HTTPS access still needs verification with verify_host.py.')
