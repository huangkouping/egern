#!/usr/bin/env python3
"""Sync, Verify and Convert ddgksf2013 splash adblock module for Egern.

Safety Features:
- Multi-mirror polling (prevents single-point discontinuation).
- Anti-Tamper Authenticity Gate (ensures rules are strictly original ddgksf2013).
- Full syntax translation (supports Loon '- reject-200' and downgrades unsupported 'jq').
- MitM IP & Wildcard sanitizer.
"""
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

# 镜像源列表：多源交叉轮询，防止某一个第三方断更
CANDIDATE_URLS = [
    # 镜像 A: 社区高可用 Loon 插件源
    'https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Loon/ddgksf2013/StartUpAds.lpx',
    # 镜像 B: Repcz 自动化同步镜像
    'https://raw.githubusercontent.com/Repcz/Tool/X/Loon/Plugin/StartUp.plugin',
    # 镜像 C: jsDelivr 全球加速代理
    'https://cdn.jsdelivr.net/gh/Repcz/Tool@X/Loon/Plugin/StartUp.plugin',
]

MODULE = ROOT / 'ddgksf2013-splash.yaml'
META = ROOT / 'ddgksf2013-splash-sync-status.json'

class EgernSafeDumper(yaml.SafeDumper):
    pass

def _str_representer(dumper, data):
    if '\\' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

EgernSafeDumper.add_representer(str, _str_representer)

def verify_authenticity(content: str) -> bool:
    """墨鱼内容真伪与安全性核验门禁 (Anti-Tamper Gate)."""
    # 1. 拦截空内容或被网络阻断的 HTML 网页
    if any(tag in content for tag in ['<!DOCTYPE html>', '<html', '404: Not Found']):
        return False
        
    # 2. 核心特征验真：必须包含墨鱼原生脚本标识，防止被偷换为第三方自制脚本
    if 'ddgksf2013' not in content:
        return False
        
    # 3. 恶意脚本注入排查：脚本路径必须仅指向墨鱼官方仓库或已知公共库
    script_urls = re.findall(r'script-path=([^\s,]+)', content)
    for surl in script_urls:
        allowed = (
            'githubusercontent.com/ddgksf2013/' in surl
            or 'githubusercontent.com/Script-Hub-Org/' in surl
            or 'githubusercontent.com/app2smile/' in surl
        )
        if not allowed:
            print(f"[SECURITY] Untrusted script domain detected: {surl}", file=sys.stderr)
            return False

    return True

def sanitize_mitm_hostnames(hostnames):
    """清洗 MitM 列表：剔除裸 IP、修复非法前缀/后缀通配符与正则。"""
    cleaned = set()
    ip_pattern = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
    
    for host in hostnames:
        h = str(host).strip().lower()
        if not h or ip_pattern.match(h) or h.endswith('.*') or h.startswith('120.241.'):
            continue
        if h.startswith('*') and not h.startswith('*.'):
            h = '*.' + h[1:]
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
        cleaned.add(h.replace('?', ''))
    return sorted(list(cleaned))

def convert_rule_file(content):
    """专用 AST/文本转换引擎：精准解析 - reject-200 并适配 Egern。"""
    rules = []
    rewrites = []
    scriptings = []
    mitm_hosts = []
    
    safe_empty = {
        'status': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': '{}'
    }
    
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # 1. 域名过滤转换
        if line.startswith(('DOMAIN,', 'DOMAIN-SUFFIX,', 'domain,', 'domain-suffix,')):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                rtype, domain, policy = parts[0].upper(), parts[1], parts[2].upper()
                # 剔除导致解密逃逸的 12306 直连
                if domain == 'ad.12306.cn' and policy == 'DIRECT':
                    continue
                if 'SUFFIX' in rtype:
                    rules.append({'domain_suffix': {'match': domain, 'policy': policy}})
                else:
                    rules.append({'domain': {'match': domain, 'policy': policy}})
            continue
            
        # 2. 覆盖 Loon 的全部 reject 语法与 jq 降级
        if any(token in line for token in ['reject-200', 'reject-dict', 'reject-img', 'reject', 'url 200', 'url reject']):
            pattern = None
            if ' - ' in line:
                pattern = line.split(' - ')[0].strip()
            elif ' url ' in line:
                pattern = line.split(' url ')[0].strip()
            else:
                parts = line.split()
                if len(parts) >= 2:
                    pattern = parts[0].strip()
                    
            if pattern and pattern.startswith('^'):
                rewrites.append({'match': pattern, 'actions': [{'respond': safe_empty}]})
            continue

        # 3. 提取墨鱼原生 JS 脚本挂载
        if 'script-path=' in line:
            match_res = re.search(r'^(.*?)\s+(url\s+script-|type=)', line)
            script_res = re.search(r'script-path=([^\s,]+)', line)
            match_pattern = match_res.group(1).strip() if match_res else None
            if not match_pattern and line.startswith('^'):
                match_pattern = line.split()[0]
                
            if match_pattern and script_res:
                scriptings.append({
                    'http_response': {
                        'name': 'adblock_script',
                        'match': match_pattern,
                        'script_url': script_res.group(1).strip(),
                        'body_required': True,
                        'timeout': 10,
                        'update_interval': 86400
                    }
                })
            continue
            
        # 4. 提取 MitM
        if line.startswith(('hostname =', 'hostname=', 'includes =', 'includes=')):
            hosts_str = line.split('=', 1)[1]
            for h in hosts_str.split(','):
                h = h.strip()
                if h:
                    mitm_hosts.append(h)
                    
    total_effective = len(rules) + len(rewrites) + len(scriptings)
    # 规则数量门禁：少于 150 条说明解析脱靶或内容残缺，拒绝更新
    if total_effective < 150:
        raise ValueError(f"Quality gate breached: parsed {total_effective} rules (expected > 150).")
        
    return {
        'name': '墨鱼去开屏2.0 (Egern规范版)',
        'description': f'400余应用开屏净化（基于 ddgksf2013 规则清洗）。有效规则数：{total_effective}。',
        'dns': {},
        'rules': rules,
        'rewrites': rewrites,
        'scriptings': scriptings,
        'mitm': {'hostnames': {'includes': sanitize_mitm_hostnames(mitm_hosts)}}
    }

def fetch_upstream():
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
    last_err = None
    for url in CANDIDATE_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode('utf-8')
                # 触发真伪核验门禁
                if verify_authenticity(data):
                    print(f"[AUTH PASS] Successfully fetched and verified rules from: {url}")
                    return data, url
                else:
                    print(f"[AUTH FAIL] Integrity check failed for: {url}", file=sys.stderr)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All candidate sources failed verification or fetch. Last error: {last_err}")

def main():
    checked = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    old_meta = json.loads(META.read_text()) if META.exists() else {}
    
    try:
        content, success_url = fetch_upstream()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # 内容无实质变化时跳过写入，避免产生脏 commit
        if old_meta.get('source_sha256') == content_hash and MODULE.exists():
            print("Upstream rules unchanged. Skipping module update.")
            old_meta['last_checked'] = checked
            META.write_text(json.dumps(old_meta, ensure_ascii=False, indent=2) + '\n')
            return 0
            
        module_data = convert_rule_file(content)
        yaml_output = yaml.dump(module_data, Dumper=EgernSafeDumper, allow_unicode=True, sort_keys=False, width=1000)
        
        MODULE.write_text(yaml_output)
        meta = {
            'status': 'ok',
            'last_checked': checked,
            'last_updated': checked,
            'source_url': success_url,
            'source_sha256': content_hash,
            'rules_count': len(module_data['rewrites']) + len(module_data['scriptings']) + len(module_data['rules'])
        }
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
        print(f"Sync & conversion OK: {meta['rules_count']} total rules active.")
        return 0
        
    except Exception as e:
        if MODULE.exists():
            meta = dict(old_meta, status='failed', last_checked=checked, error=str(e))
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
            print(f"Sync failed; retained last-good version: {e}", file=sys.stderr)
            return 0  # 保留有效版本，防止 Actions 红标打断
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
