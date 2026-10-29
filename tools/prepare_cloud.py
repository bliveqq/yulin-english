"""Build static HTTPS cloud release without uploading or changing supplied source files."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT.parent/'2015-2026英语中考真题';OUT=ROOT/'cloud-deploy';FILES=OUT/'public/files';FILES.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/.deps'))
import imageio_ffmpeg
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();catalog=json.loads((ROOT/'assets/national-catalog.json').read_text());entries=[];converted=[];failures=[]
for i,item in enumerate(catalog['files']):
 source=SOURCE/item['path'];ext=source.suffix.lower().lstrip('.');temp=None
 if ext in ['wav','wma','amr']:
  temp=OUT/(item['id']+'.mp3');cmd=[ffmpeg,'-v','error','-y','-i',str(source),'-vn','-map','0:a:0','-codec:a','libmp3lame','-q:a','2','-ar','44100','-ac','2',str(temp)]
  result=subprocess.run(cmd,capture_output=True,timeout=600)
  if result.returncode:failures.append({'source':item['path'],'error':result.stderr.decode(errors='replace')[:500]});continue
  upload=temp;ext='mp3';converted.append(item['path'])
 else:upload=source
 sha=hashlib.sha256(upload.read_bytes()).hexdigest();target=FILES/(sha+'.'+ext)
 if not target.exists():shutil.copyfile(upload,target)
 if temp:temp.unlink()
 entries.append({'id':item['id'],'title':item['title'],'path':'files/'+target.name,'extension':ext,'sha256':sha,'bytes':target.stat().st_size,'sourceSha256':item['sha256'],'sourcePath':item['path'],'year':item['year'],'province':item['province'],'city':item['city'],'convertedAudio':source.suffix.lower() in ['.wav','.wma','.amr']})
 if i%400==0:print('Prepared',i,'/',len(catalog['files']),flush=True)
manifest={'schema':1,'release':'1.3.0','name':'雨林英语全国真题云资料','files':entries};(OUT/'public/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')))
report={'published':False,'files':len(entries),'bytes':sum(e['bytes'] for e in entries),'convertedAudio':converted,'failures':failures,'sourceUnchanged':all(hashlib.sha256((SOURCE/p['path']).read_bytes()).hexdigest()==p['sha256'] for p in catalog['files'])};(OUT/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='convertedAudio'},ensure_ascii=False),flush=True)
