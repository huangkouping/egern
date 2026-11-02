#!/usr/bin/env python3
"""Sync and sanitize ddgksf2013 splash adblock module for Egern."""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parents[1]
# 墨鱼开屏模块官方有效真实 raw 地址
URL = 'https://raw.githubusercontent.com/ddgksf2013/Rewrite/master/Html/StartUp.conf'
MODULE = ROOT / 'ddgksf2013-splash.yaml'
META = ROOT / 'ddgksf2013-splash-sync-status.json'

class EgernSafeDumper(yaml.SafeDumper):
    pass

def _str_representer(dumper, data):
    if '\\' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

EgernSafeDumper.add_representer(str, _str_representer)

def sanitize_mitm_hostnames(hostnames):
    cleaned = set()
    ip_pattern = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
    
    for host in hostnames:
        h = str(host).strip().lower()
        if not h:
            continue
        # 过滤裸 IP 与非法网段通配
        if ip_pattern.match(h) or h.endswith('.*') or h.startswith('120.241.'):
            continue
        # 补齐前缀漏掉的点 (*domain.com -> *.domain.com)
        if h.startswith('*') and not h.startswith('*.'):
            h = '*.' + h[1:]
        # 修复非法后缀与正则字符
        if h == '*.flyert.*':
            cleaned.update(['*.flyert.com', 'www.flyert.com'])
            continue
        if h == '*mangaapi.manhuaren.*':
            cleaned.add('*.manhuaren.com')
            continue
        if 'pangolin-sdk-toutiao' in h:
            cleaned.add('*.pangolin-sdk-toutiao.com')
            continue
        if 'pinggai*.caixin.com' in h:
            cleaned.add('*.caixin.com')
            continue
        if 'interface*.music.163.com' in h:
            cleaned.update(['interface.music.163.com', 'interface3.music.163.com'])
            continue
        if 'emdcad*.eastmoney.com' in h:
            cleaned.add('*.eastmoney.com')
            continue
        if 'mage*.if.qidian.com' in h:
            cleaned.add('*.qidian.com')
            continue
        if 'p*.meituan.net' in h:
            cleaned.add('*.meituan.net')
            continue
        if '?' in h:
            h = h.replace('?', '')
            
        cleaned.add(h)
    return sorted(list(cleaned))

def parse_conf_to_data(content):
    """解析 Loon/Surge 格式的文本，转为 Egern 标准数据结构"""
    rules = []
    rewrites = []
    scriptings = []
    mitm_hosts = []
    
    safe_empty = {
        'respond': {
            'status': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': '{}'
        }
    }
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # 提取域名拦截与直连
        if line.startswith('DOMAIN-SUFFIX,'):
            parts = line.split(',')
            if len(parts) >= 3:
                rules.append({'domain_suffix': {'match': parts[1].strip(), 'policy': parts[2].strip()}})
        elif line.startswith('DOMAIN,'):
            parts = line.split(',')
            if len(parts) >= 3:
                domain = parts[1].strip()
                policy = parts[2].strip()
            # 彻底剔除 12306 DIRECT
                if domain == 'ad.12306.cn' and policy == 'DIRECT':
                    continue
                rules.append({'domain': {'match': domain, 'policy': policy}})
            
        # 提取 Reject / Empty 重写
        elif 'url reject' in line or 'url 200' in line:
            parts = line.split()
            if len(parts) >= 2:
                pattern = parts[0].strip()
                rewrites.append({'match': pattern, 'actions': [safe_empty]})
                
        # 提取 JS 响应脚本
        elif 'script-path=' in line and 'type=http-response' in line:
            match_res = re.search(r'^(.*?)\s+url\s+script-response-body', line)
            script_res = re.search(r'script-path=([^\s,]+)', line)
            if match_res and script_res:
                scriptings.append({
                    'http_response': {
                        'name': 'adblock_script',
                        'match': match_res.group(1).strip(),
                        'script_url': script_res.group(1).strip(),
                        'body_required': True,
                        'timeout': 10,
                        'update_interval': 3600
                    }
                })
                
        # 提取 MitM
        elif line.startswith('hostname =') or line.startswith('hostname='):
            hosts_str = line.split('=', 1)[1]
            for h in hosts_str.split(','):
                h = h.strip()
                if h:
                    mitm_hosts.append(h)
                    
    return {
        'name': '墨鱼去开屏2.0 (Egern规范版)',
        'description': '400余应用开屏去广告，自动清洗规避崩溃与穿透缺陷。',
        'dns': {},
        'rules': rules,
        'rewrites': rewrites,
        'scriptings': scriptings,
        'mitm': {'hostnames': {'includes': sanitize_mitm_hostnames(mitm_hosts)}}
    }

def process_data(content):
    """自适应判断是 YAML 还是 Conf 格式并清洗"""
    if 'rewrites:' in content or 'rules:' in content:
        raw_data = yaml.safe_load(content)
        # 1. 过滤 12306 直连
        raw_data['rules'] = [
            r for r in raw_data.get('rules', [])
            if not (r.get('domain', {}).get('match') == 'ad.12306.cn' and r.get('domain', {}).get('policy') == 'DIRECT')
        ]
        # 2. 替换 body 为标准空 JSON，丢弃不支持的 jq
        safe_empty = {'status': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{}'}
        cleaned_rewrites = []
        for rw in raw_data.get('rewrites', []):
            actions = rw.get('actions', [])
            if any('response_body' in a and 'jq' in a['response_body'] for a in actions):
                continue
            for a in actions:
                if 'respond' in a:
                    if a['respond'].get('body') in (' ', '', None):
                        a['respond'] = safe_empty
            cleaned_rewrites.append(rw)
        raw_data['rewrites'] = cleaned_rewrites
        
        # 3. 压制脚本超时并设置更新间隔
        for s in raw_data.get('scriptings', []):
            for key in ['http_response', 'http_request']:
                if key in s:
                    s[key].pop('max_size', None)
                    s[key]['timeout'] = 10
                    s[key]['update_interval'] = 3600
                    
        # 4. 清洗 MitM
        if 'mitm' in raw_data and 'hostnames' in raw_data['mitm']:
            raw_hosts = raw_data['mitm']['hostnames'].get('includes', [])
            raw_data['mitm']['hostnames']['includes'] = sanitize_mitm_hostnames(raw_hosts)
            
        return raw_data
    else:
        return parse_conf_to_data(content)

def main():
    checked = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old_meta = json.loads(META.read_text()) if META.exists() else {}
    
    try:
        req = urllib.request.Request(URL, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
            })
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8')
            
        module_data = process_data(content)
        yaml_output = yaml.dump(module_data, Dumper=EgernSafeDumper, allow_unicode=True, sort_keys=False, width=1000)
        
        MODULE.write_text(yaml_output)
        meta = {
            'status': 'ok',
            'last_checked': checked,
            'last_updated': checked,
            'rules_count': len(module_data.get('rewrites', [])) + len(module_data.get('scriptings', []))
        }
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print(f"ddgksf2013 splash module sync OK: {meta['rules_count']} rules processed.")
        return 0
    except Exception as e:
        if MODULE.exists():
            meta = dict(old_meta, status='failed', last_checked=checked, error=str(e))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
            print(f"Sync failed; retained last-good version: {e}", file=sys.stderr)
            return 0
        print(f"Sync failed without existing fallback: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
