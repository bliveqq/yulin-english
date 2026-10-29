import unittest,json,hashlib,re,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];M=json.loads((R/'cloud-deploy/public/manifest.json').read_text());REPORT=json.loads((R/'cloud-deploy/build-report.json').read_text())
class CloudBundleTests(unittest.TestCase):
 def test_manifest_matches_every_file(self):
  ids=set()
  for x in M['files']:
   self.assertNotIn(x['id'],ids);ids.add(x['id']);self.assertRegex(x['id'],r'^[a-f0-9]{24}$');self.assertEqual(x['path'],'files/'+x['sha256']+'.'+x['extension']);p=R/'cloud-deploy/public'/x['path'];self.assertEqual(p.stat().st_size,x['bytes']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
 def test_audio_conversions_available_offline(self):
  mapping=json.loads((R/'assets/audio-compat.json').read_text());self.assertEqual(len(mapping),5)
  for x in M['files']:
   if x['convertedAudio']:
    self.assertEqual(x['extension'],'mp3');p=R/'assets/audio-compat'/mapping[x['sourcePath']];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
  self.assertTrue(REPORT['sourceUnchanged']);self.assertFalse(REPORT['published']);self.assertEqual(REPORT['failures'],[])
if __name__=='__main__':unittest.main()
