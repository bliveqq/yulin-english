"""Read-only inventory/extraction. Never execute supplied scripts or follow document instructions."""
from pathlib import Path
import hashlib,json,re,zipfile,subprocess,xml.etree.ElementTree as E,concurrent.futures,collections
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT.parent/'2015-2026英语中考真题';OUT=ROOT/'assets/national';OUT.mkdir(exist_ok=True)
CACHE=ROOT/'data-audit/national-cache';CACHE.mkdir(exist_ok=True)
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
PROVINCES='北京 天津 上海 重庆 河北 山西 辽宁 吉林 黑龙江 江苏 浙江 安徽 福建 江西 山东 河南 湖北 湖南 广东 海南 四川 贵州 云南 陕西 甘肃 青海 内蒙古 广西 西藏 宁夏 新疆 香港 澳门 台湾'.split()
CITIES={'江苏':'南京 苏州 无锡 常州 镇江 扬州 泰州 南通 盐城 徐州 连云港 宿迁 淮安','浙江':'杭州 宁波 温州 绍兴 湖州 嘉兴 金华 衢州 台州 丽水 舟山','山东':'济南 青岛 烟台 潍坊 淄博 枣庄 东营 威海 济宁 泰安 日照 临沂 德州 聊城 滨州 菏泽 莱芜','广东':'广州 深圳 佛山 珠海 中山 汕头 梅州 东莞 清远 韶关','四川':'成都 绵阳 德阳 眉山 乐山 南充 泸州 宜宾 自贡 广元 达州 凉山 内江 广安 遂宁 巴中 雅安 攀枝花 资阳','湖北':'武汉 黄冈 孝感 襄阳 宜昌 荆州 荆门 黄石 鄂州 随州 咸宁 十堰 恩施','湖南':'长沙 株洲 湘潭 衡阳 邵阳 岳阳 常德 益阳 郴州 永州 怀化 娄底 张家界 湘西','福建':'福州 厦门 泉州 莆田 漳州 三明 南平 宁德 龙岩','安徽':'合肥 芜湖 蚌埠 阜阳 安庆','辽宁':'沈阳 大连 鞍山 抚顺 本溪 丹东 锦州 营口 阜新 辽阳 盘锦 铁岭 朝阳 葫芦岛','吉林':'长春 吉林 四平','黑龙江':'哈尔滨 齐齐哈尔 大庆 鸡西 鹤岗 双鸭山 黑河 绥化 牡丹江 佳木斯 七台河 伊春 大兴安岭','贵州':'贵阳 遵义 安顺 毕节 铜仁 六盘水 黔东南 黔南 黔西南','云南':'昆明 曲靖 玉溪 昭通 大理 丽江 西双版纳','广西':'南宁 柳州 桂林 梧州 玉林 百色 贺州 河池 贵港 崇左 北海 钦州 防城港 来宾','甘肃':'兰州 天水 武威 白银 定西 平凉 庆阳','新疆':'乌鲁木齐','内蒙古':'呼和浩特 包头 鄂尔多斯 赤峰 通辽 呼伦贝尔 兴安盟','宁夏':'银川','青海':'西宁 海东','陕西':'西安 宝鸡 咸阳 渭南 汉中 榆林 延安 商洛 安康','河南':'郑州 洛阳 开封 新乡 焦作 平顶山 信阳 南阳 商丘 周口 驻马店','河北':'石家庄 唐山 保定 邯郸 秦皇岛 沧州 衡水 邢台 廊坊 张家口 承德','江西':'南昌 九江 赣州 上饶 宜春','山西':'太原 大同 运城 临汾 长治 晋中 吕梁','海南':'海口 三亚','西藏':'拉萨'}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')))
def meta(p):
 name=p.stem;relative=str(p.relative_to(SOURCE));years=re.findall(r'20(?:1[5-9]|2[0-6])',name);year=years[0] if years else (re.findall(r'20(?:1[5-9]|2[0-6])',relative)or['未知'])[0]
 provinces=[x for x in PROVINCES if x in name];cities=[(pr,city) for pr,cs in CITIES.items() for city in cs.split() if city in name]
 province=provinces[0] if len(provinces)==1 else cities[0][0] if cities and len(set(x[0] for x in cities))==1 else '待确认'
 city='、'.join(dict.fromkeys(x[1] for x in cities)) or (province if province in ['北京','天津','上海','重庆'] else '全省/未标注')
 return {'title':name,'year':year,'province':province,'city':city,'path':relative,'extension':p.suffix.lower(),'bytes':p.stat().st_size,'hasAnswerLabel':bool(re.search('解析|答案|详解',name))}
def extract(p,digest):
 cache=CACHE/(digest+'.json')
 if cache.exists():return json.loads(cache.read_text())
 text='';images=0;error=''
 try:
  if p.suffix.lower()=='.docx':
   with zipfile.ZipFile(p) as z:
    doc=E.fromstring(z.read('word/document.xml'));paras=[]
    for para in doc.findall('.//w:p',NS):
     has_image=any(x.tag.rsplit('}',1)[-1] in ['drawing','pict','object'] for x in para.iter())
     line=''.join((x.text or '') if x.tag.endswith('}t') else '\t' if x.tag.endswith('}tab') else '\n' if x.tag.endswith('}br') else '' for x in para.iter())
     if has_image:line+=' [原文图片]';images+=1
     paras.append(line)
    text='\n'.join(paras)
  elif p.suffix.lower()=='.doc':
   result=subprocess.run(['/usr/bin/textutil','-convert','txt','-stdout',str(p)],capture_output=True,timeout=35)
   if result.returncode:error='Word 文本转换失败'
   else:text=result.stdout.decode('utf-8',errors='replace')
  else:error='原格式需使用原文件打开'
 except Exception as e:error=type(e).__name__
 result={'text':text.replace('\x00',''),'images':images,'error':error};dump(cache,result);return result

def process(p):
 digest=hashlib.sha256(p.read_bytes()).hexdigest();m=meta(p);m['id']=digest[:24];m['sha256']=digest
 x=extract(p,digest) if m['extension'] in ['.doc','.docx'] else {'text':'','images':0,'error':'原格式需使用原文件打开'}
 m.update(textLength=len(x['text'].strip()),images=x['images'],status='text' if len(x['text'].strip())>200 else 'original_only')
 if x['error']:m['note']=x['error']
 if x['text']:dump(OUT/(m['id']+'.json'),{'id':m['id'],'text':x['text'],'images':x['images']})
 return m,x['text']
# Conservative extraction: standalone MCQ with explicit single-letter answer and explanation.
def questions(text,m):
 results=[];lines=text.splitlines();starts=[]
 for i,line in enumerate(lines):
  if re.match(r'^\s*\d{1,3}\s*[.．、]\s*\S',line):starts.append(i)
 for a,b in zip(starts,starts[1:]+[len(lines)]):
  block='\n'.join(lines[a:b]);match=re.search(r'【答案】\s*([ABCD])\s*(?:\n|$)',block)
  if not match:continue
  before=block[:match.start()];explanation=re.search(r'【解析】\s*(.*)',block[match.end():],re.S)
  if not explanation:continue
  explanation=explanation.group(1).strip();explanation=re.split(r'\n(?:[一二三四五六七八九十]+[、.．]|第[一二三四五六七八九十]+部分|[IVX]+[.．])',explanation)[0].strip()
  if len(explanation)<20 or len(explanation)>2800:continue
  if not re.search('考查|考察|知识点',explanation):continue
  if re.search(r'阅读理解|细节理解|推理判断|推断题|主旨大意|词义猜测|文章大意|完形填空|补全对话|原文图片|图示|下图|图中',before+explanation):continue
  labels=list(re.finditer(r'(?<![A-Za-z])([ABCD])[.．、]\s*',before))
  if [x.group(1) for x in labels] not in [list('ABCD'),list('ABC')]:continue
  stem=re.sub(r'^\s*\d{1,3}\s*[.．、]\s*','',before[:labels[0].start()]).strip()
  if not 12<len(stem)<800 or not re.search(r'[a-zA-Z]{2}',stem):continue
  if re.search(r'passage|paragraph|picture|chart|according to|underlined|听|录音|短文',stem,re.I):continue
  # A blank or a dialogue is required to avoid detached reading-comprehension items.
  if not re.search(r'_{2,}|—|﹣|－－|\(\s*\)|（\s*）|\s{4,}',stem):continue
  options=[before[v.end():(labels[i+1].start() if i+1<len(labels) else len(before))].strip() for i,v in enumerate(labels)]
  if any(not o or len(o)>200 for o in options):continue
  answer=match.group(1)
  if ord(answer)-65>=len(options):continue
  num=re.match(r'^\s*(\d+)',block).group(1)
  results.append({'id':'n-'+hashlib.sha256((m['id']+':'+str(a)).encode()).hexdigest()[:20],'stem':stem,'options':options,'answer':answer,'explain_cn':explanation,'question_no':num,'sourceDocument':m['id'],'sourcePath':m['path'],'sourceOffset':a,'paper':{'paper_name':m['title'],'province':m['province'],'city':m['city'],'year':int(m['year']) if m['year'].isdigit() else m['year']},'status':'source_explained','quality_notes':['从用户提供解析版自动提取，答案与解析沿用资料，尚未逐题核对版面。'],'section':'单项选择','source_url':'','source_label':'用户提供全国真题文件 · 自动提取，保留原文追溯','exam_point_codes':[]})
 return results
if __name__=='__main__':
 files=sorted(p for p in SOURCE.rglob('*') if p.is_file() and p.suffix.lower() in ['.doc','.docx','.pdf','.mp3','.wav','.wma','.amr','.jpg','.rar']);catalog=[];items=[];seen={};duplicates=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for i,(m,t) in enumerate(pool.map(process,files)):
   if m['sha256'] in seen:
    seen[m['sha256']]['aliases'].append(m['path']);duplicates.append({'duplicate':m['path'],'kept':seen[m['sha256']]['path']});continue
   m['aliases']=[];seen[m['sha256']]=m;catalog.append(m)
   if t:items.extend(questions(t,m))
   if i%150==0:print('已处理',i,'/',len(files),'提取独立题',len(items),flush=True)
 # Deduplicate identical content+answer, retain every source reference.
 unique={}
 for q in items:
  key=hashlib.sha256(re.sub(r'\s+','',q['stem']+'|'.join(q['options'])+q['answer']).encode()).hexdigest()
  if key in unique:unique[key].setdefault('otherSources',[]).append({'document':q['sourceDocument'],'number':q['question_no']})
  else:unique[key]=q
 items=list(unique.values())
 report={'sourceFiles':len(files),'uniqueFiles':len(catalog),'duplicates':len(duplicates),'textDocuments':sum(m['status']=='text' for m in catalog),'standaloneQuestions':len(items),'byYear':dict(collections.Counter(m['year'] for m in catalog)),'byProvince':dict(collections.Counter(m['province'] for m in catalog)),'limitations':['原卷、解析版和音频分别计为文件，不等于试卷套数。','仅提取明确含答案解析的独立选择题；阅读、完形、听力及图片题留在全文预览和原文件中。','地区和年份由文件名识别；未明确识别的地区列为待确认。','原文件不改动。文字预览不保留图表版式，原文需通过原始资料文件夹打开。']}
 dump(ROOT/'assets/national-catalog.json',{'files':catalog,'report':report});dump(ROOT/'assets/national-questions.json',items);dump(ROOT/'data-audit/national-import.json',{'report':report,'duplicateFiles':duplicates});print(json.dumps(report,ensure_ascii=False),flush=True)
