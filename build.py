#!/usr/bin/env python3
"""Build an offline universal Android APK with official Android build tools."""
import os, pathlib, subprocess, zipfile, secrets, hashlib, json
# APK uses classic ZIP, whose offsets are unsigned 32-bit. Python defaults to a conservative 2 GiB limit.
zipfile.ZIP64_LIMIT=0xffffffff
ROOT=pathlib.Path(__file__).resolve().parent
CACHE=pathlib.Path.home()/'.cache/yulin-android'
JDK=CACHE/'zulu17.70.111-ca-jdk17.0.21-macosx_aarch64/Contents/Home'
TOOLS=CACHE/'tools/android-15'; PLATFORM=CACHE/'platform/android-35/android.jar'
BUILD=ROOT/'build'; BUILD.mkdir(exist_ok=True)
OUT=ROOT/'release';OUT.mkdir(exist_ok=True)
SIGN=pathlib.Path.home()/'.local/share/yulin-english-signing';SIGN.mkdir(parents=True,exist_ok=True);SIGN.chmod(0o700)
PASS=SIGN/'store-password'; KEY=SIGN/'yulin-release.p12'
if not PASS.exists():PASS.write_text(secrets.token_urlsafe(36));PASS.chmod(0o600)
env=dict(os.environ,JAVA_HOME=str(JDK));env['PATH']=str(JDK/'bin')+':'+env.get('PATH','')
def run(*args):subprocess.run([str(a) for a in args],cwd=ROOT,env=env,check=True)
for name,digest in [('build-tools.zip','93ab8ce91230e067b5add4bfa79919c52b27f072'),('platform.zip','0bb560a90a7a2cbd0dd8348224d518b638fe7949')]:
 assert hashlib.sha1((CACHE/name).read_bytes()).hexdigest()==digest, 'SDK checksum mismatch: '+name
if not KEY.exists():
 run(JDK/'bin/keytool','-genkeypair','-keystore',KEY,'-storetype','PKCS12','-storepass:file',PASS,'-alias','yulin','-keyalg','RSA','-keysize','3072','-validity','10000','-dname','CN=Yulin English, OU=Personal App, O=Yulin English, C=CN')
 KEY.chmod(0o600)
run(TOOLS/'aapt2','compile','--dir',ROOT/'res','-o',BUILD/'resources.zip')
run(TOOLS/'aapt2','link','-o',BUILD/'unsigned.apk','-I',PLATFORM,'--manifest',ROOT/'AndroidManifest.xml','-A',ROOT/'assets',BUILD/'resources.zip')
classes=BUILD/'classes';classes.mkdir(exist_ok=True)
run(JDK/'bin/javac','--release','8','-encoding','UTF-8','-cp',PLATFORM,'-d',classes,*ROOT.glob('src/**/*.java'))
with zipfile.ZipFile(BUILD/'classes.jar','w') as z:
 for p in classes.rglob('*.class'):z.write(p,p.relative_to(classes))
run(JDK/'bin/java','-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26','--lib',PLATFORM,'--output',BUILD,BUILD/'classes.jar')
with zipfile.ZipFile(BUILD/'unsigned.apk','a',zipfile.ZIP_DEFLATED,allowZip64=False,compresslevel=6) as z:
 z.write(BUILD/'classes.dex','classes.dex')
 manifest=json.loads((ROOT/'assets/builtin-manifest.json').read_text())
 for i,item in enumerate(manifest['files']):
  source=ROOT/'cloud-deploy/public'/item['path']
  assert source.stat().st_size==item['bytes']
  z.write(source,'assets/archive/'+source.name)
  if i%250==0:print('Bundling originals:',i,'/',len(manifest['files']),flush=True)
run(TOOLS/'zipalign','-f','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
apk=OUT/'雨林英语-1.4.0-完整离线版.apk'
run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','sign','--ks',KEY,'--ks-key-alias','yulin','--ks-pass','file:'+str(PASS),'--out',apk,BUILD/'aligned.apk')
run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','verify','--verbose',apk)
run(TOOLS/'zipalign','-c','4',apk)
(OUT/'SHA256.txt').write_text(hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()+'  '+apk.name+'\n')
print('APK ready:',apk)
