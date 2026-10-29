"""Read-only deployment check. Requires a deployed public HTTPS base URL."""
import sys,json,urllib.request,urllib.parse
base=sys.argv[1].rstrip('/')+'/'
u=urllib.parse.urlparse(base)
assert u.scheme=='https' and u.hostname and not u.username and not u.query and not u.fragment,'Use a clean HTTPS root URL'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
client=urllib.request.build_opener(NoRedirect)
with client.open(base+'manifest.json',timeout=20) as response:
 manifest=json.loads(response.read(12000001));assert manifest['schema']==1 and manifest['files']
item=manifest['files'][0];assert item['path']=='files/'+item['sha256']+'.'+item['extension']
request=urllib.request.Request(base+item['path'],headers={'Range':'bytes=0-1023'})
with client.open(request,timeout=20) as response:
 sample=response.read(1024);assert sample
 print('HTTPS manifest OK; files:',len(manifest['files']),'Range response:',response.status)
 if response.status==200:print('Server returns full files; interrupted downloads will restart.')
 elif response.status!=206:raise RuntimeError('Unexpected download status')
print('Read-only host checks passed. Finish with Android device playback/download checks.')
