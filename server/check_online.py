"""Read-only public HTTPS verification after deployment. No credentials required."""
import argparse,hashlib,json,ssl,urllib.request,urllib.parse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('url',help='HTTPS origin of the server');a=p.parse_args();u=urllib.parse.urlsplit(a.url)
if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):p.error('Provide a clean HTTPS origin')
base=a.url.rstrip('/')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
ctx=ssl.create_default_context(cafile='/etc/ssl/cert.pem' if Path('/etc/ssl/cert.pem').is_file() else None)
client=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ctx))
def read(path,limit,headers=None):
 with client.open(urllib.request.Request(base+path,headers=headers or {}),timeout=30) as r:
  data=r.read(limit+1)
  if len(data)>limit:raise ValueError('Response exceeds expected size')
  return r.status,r.headers,data
assert json.loads(read('/healthz',1024)[2])['status']=='ok'
m=json.loads(read('/english/manifest.json',12000000)[2]);assert m['schema']==1 and m['files']
x=min(m['files'],key=lambda f:f['bytes']);path=x['path']
assert path==f"files/{x['sha256']}.{x['extension']}" and '..' not in path and x['bytes']>0
code,headers,data=read('/english/'+path,x['bytes']);assert code==200 and hashlib.sha256(data).hexdigest()==x['sha256']
end=min(31,x['bytes']-1);code,headers,part=read('/english/'+path,end+1,{'Range':f'bytes=0-{end}'})
assert code==206 and part==data[:end+1] and headers['Content-Range']==f"bytes 0-{end}/{x['bytes']}"
print('HTTPS、公开目录、样本文件 SHA-256、断点下载检查通过。')
print('资料数：',len(m['files']));print('应用云端地址：',base+'/english/')
print('最后还需在安卓设备验证下载和离线音频播放。')
