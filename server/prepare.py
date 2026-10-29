"""Verify all files and generate public status metadata; never alters source data."""
import argparse,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);a=p.parse_args()
root=a.library.resolve();m=json.loads((root/'manifest.json').read_text());assert m['schema']==1
ids=set();total=0
for x in m['files']:
 assert re.fullmatch('[a-f0-9]{24}',x['id']) and x['id'] not in ids;ids.add(x['id'])
 assert re.fullmatch('[a-f0-9]{64}',x['sha256'])
 assert x['extension'] in ['doc','docx','pdf','mp3','wav','amr','jpg','jpeg','png','rar','zip']
 assert x['path']==f"files/{x['sha256']}.{x['extension']}"
 f=root/x['path'];assert f.is_file() and not f.is_symlink() and f.stat().st_size==x['bytes']
 with f.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==x['sha256'],x['id']
 total+=x['bytes']
status={'service':'yulin-english','release':m.get('release'),'files':len(ids),'bytes':total,'manifest':'/english/manifest.json','aiConfigured':False}
out=Path(__file__).resolve().parent/'site/status.json';out.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(f'已核验 {len(ids)} 个文件，共 {total} 字节。未上传到任何服务器。')
