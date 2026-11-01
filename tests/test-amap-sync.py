#!/usr/bin/env python3
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[1]

class AmapSyncTest(unittest.TestCase):
    def test_good_bad_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'input').mkdir()
            for name in ['sync-amap.py', 'amap-base.yaml']:
                shutil.copy(SOURCE_ROOT / 'scripts' / name, root / 'scripts' / name)
            for name in ['updatable.jq', 'search_poi_detail.jq']:
                shutil.copy(SOURCE_ROOT / ('amap-' + name), root / 'input' / name)
            def run():
                return subprocess.run(['python3', str(root / 'scripts/sync-amap.py'),
                    '--source-dir', str(root / 'input'), '--upstream-ref', 'fixture'],
                    capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            good = yaml.safe_load((root / 'amap-adblock.yaml').read_text())
            self.assertEqual(len(good['rewrites']), 27)
            self.assertEqual(good['mitm']['hostnames']['includes'],
                yaml.safe_load((root / 'scripts/amap-base.yaml').read_text())['mitm']['hostnames']['includes'])
            for rule in good['rewrites']:
                for action in rule['actions']:
                    if 'response_body' in action:
                        self.assertIsInstance(action['response_body']['jq'], str)
            initial_meta = json.loads((root / 'amap-sync-status.json').read_text())
            self.assertEqual(run().returncode, 0)
            self.assertEqual(initial_meta['last_updated'], json.loads((root / 'amap-sync-status.json').read_text())['last_updated'])
            original = (root / 'input/updatable.jq').read_text()
            for bad in ['404: Not Found', '<html>Access denied</html>', 'def broken: [;']:
                (root / 'input/updatable.jq').write_text(bad)
                self.assertEqual(run().returncode, 1)
                failed = yaml.safe_load((root / 'amap-adblock.yaml').read_text())
                self.assertEqual(failed['rewrites'], good['rewrites'])
                self.assertEqual((root / 'amap-updatable.jq').read_text(), original)
                self.assertEqual(json.loads((root / 'amap-sync-status.json').read_text())['status'], 'failed')
            (root / 'input/updatable.jq').write_text(original)
            self.assertEqual(run().returncode, 0)
            self.assertEqual(json.loads((root / 'amap-sync-status.json').read_text())['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
