#!/usr/bin/env python3
"""Sync, Deep-Verify, and Convert ddgksf2013 splash module for Egern.

Hardened Implementation:
1. Strict Redirect-Aware HTTP Fetcher: Validates HTTPS, userinfo, port, host & path traversal.
2. Exact Host & Path Prefix Whitelist for external scripts (strictly disallows broad github.com).
3. Non-Destructive JQ Gate:
   - Strips single matching outer quote pair and unescapes internal '\\"' -> '"'.
   - Exact full-string matching of verified JQ expressions allowed.
   - Maps strictly to dedicated adapter script (scripts/ddgksf-splash-adapter.js) with env.MODE.
   - Unknown JQ causes immediate hard failure.
4. Adapter Integrity Gate:
   - Pinned SHA-256 hash: c3ccf3262e1c7e0c426c0f62cbd92ee819ad8940256b9dd9f828f37a272f2548.
   - Official production URL: https://raw.githubusercontent.com/huangkouping/egern/main/scripts/ddgksf-splash-adapter.js.
   - Local testing via --adapter-url file:// only validates content SHA-256; generated YAML ALWAYS writes the official production HTTPS URL.
5. Loss-Rate & Malformed Rule Auditing: Rejects malformed DOMAIN lines; loss triggers exit code 1.
6. Clean Failure Handling: Never mutates existing valid YAML on failure; status JSON only.
7. Embedded Regression Test Suite (--test).
"""
import argparse
import hashlib
import json
import posixpath
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError:
    print(
        "Error: Missing required dependency 'PyYAML'. Please install it using 'pip install pyyaml'.",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]

# 允许的规则源下载域名
ALLOWED_FETCH_HOSTS = (
    'raw.githubusercontent.com',
    'gist.githubusercontent.com',
    'cdn.jsdelivr.net',
    'fastly.jsdelivr.net',
)

# 候选抓取源
CANDIDATE_URLS = [
    'https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Loon/ddgksf2013/StartUpAds.lpx',
    'https://raw.githubusercontent.com/Repcz/Tool/X/Loon/Plugin/StartUp.plugin',
]

# 严格允许的外部 JS 脚本宿主与精准路径前缀（拒绝泛 github.com）
EXACT_SCRIPT_PREFIXES = (
    'https://raw.githubusercontent.com/ddgksf2013/',
    'https://raw.githubusercontent.com/Script-Hub-Org/',
    'https://raw.githubusercontent.com/app2smile/',
    'https://cdn.jsdelivr.net/gh/ddgksf2013/',
    'https://github.com/ifflagged/Romeo/raw/main/Modules/JavaScript/ddgksf2013/StartUpAds/',
    'https://raw.githubusercontent.com/huangkouping/egern/main/scripts/ddgksf-splash-adapter.js',
)

# 官方适配器生产地址及固定 SHA-256
OFFICIAL_ADAPTER_URL = 'https://raw.githubusercontent.com/huangkouping/egern/main/scripts/ddgksf-splash-adapter.js'
EXPECTED_ADAPTER_SHA256 = '3b2a1c55fa8843caf12b5b5da8a0d33cfed2b3b3e7df85ac35ea3741f35165a6'

MODULE = ROOT / 'ddgksf2013-splash.yaml'
META = ROOT / 'ddgksf2013-splash-sync-status.json'

class EgernSafeDumper(yaml.SafeDumper):
    pass

def _str_representer(dumper, data):
    if '\\' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

EgernSafeDumper.add_representer(str, _str_representer)

def validate_secure_url(url: str, allowed_hosts=None, allowed_prefixes=None):
    """校验 URL 安全性：强制 HTTPS、标准端口、禁止 userinfo 与路径遍历。"""
    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception as e:
        raise ValueError(f"Malformed URL '{url}': {e}")

    if parsed.scheme.lower() != 'https':
        raise ValueError(f"Non-HTTPS URL rejected: '{url}'")

    if parsed.username or parsed.password:
        raise ValueError(f"URL contains forbidden userinfo: '{url}'")

    if parsed.port not in (None, 443):
        raise ValueError(f"Non-standard HTTPS port '{parsed.port}' rejected: '{url}'")

    norm_path = posixpath.normpath(parsed.path)
    if '..' in parsed.path.split('/') or norm_path != parsed.path:
        raise ValueError(f"Path traversal detected in URL: '{url}'")

    if allowed_hosts and parsed.hostname.lower() not in allowed_hosts:
        raise ValueError(f"Host '{parsed.hostname}' not in allowed hosts: '{url}'")

    if allowed_prefixes:
        if not any(url.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"URL does not match any allowed exact prefix: '{url}'")

    return True

class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """验证重定向链上的每一个跳转目标是否合规。"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            validate_secure_url(newurl, allowed_hosts=ALLOWED_FETCH_HOSTS)
        except ValueError as err:
            raise urllib.error.HTTPError(
                newurl, code, f"[SECURITY ERROR] Insecure redirect: {err}", headers, fp
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def sanitize_mitm_hostnames(raw_hosts):
    """先规范化并展开特殊域名，再执行非法/IP过滤（时序保证）。"""
    expanded = set()
    for host in raw_hosts:
        h = str(host).strip().lower()
        if not h:
            continue

        if h == '*.flyert.*':
            expanded.update(['*.flyert.com', 'www.flyert.com'])
            continue
        if h == '*mangaapi.manhuaren.*':
            expanded.add('*.manhuaren.com')
            continue
        if 'pangolin-sdk-toutiao' in h:
            expanded.add('*.pangolin-sdk-toutiao.com')
            continue
        if 'pinggai*.caixin.com' in h:
            expanded.add('*.caixin.com')
            continue
        if 'interface*.music.163.com' in h:
            expanded.update(['interface.music.163.com', 'interface3.music.163.com'])
            continue
        if 'emdcad*.eastmoney.com' in h:
            expanded.add('*.eastmoney.com')
            continue
        if 'mage*.if.qidian.com' in h:
            expanded.add('*.qidian.com')
            continue
        if 'p*.meituan.net' in h:
            expanded.add('*.meituan.net')
            continue
        if h.startswith('*') and not h.startswith('*.'):
            h = '*.' + h[1:]
        h = h.replace('?', '')
        expanded.add(h)

    cleaned = set()
    ip_pattern = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')
    for h in expanded:
        if ip_pattern.match(h) or h.endswith('.*') or h.startswith('120.241.'):
            continue
        if '*' in h and not h.startswith('*.'):
            continue
        cleaned.add(h)

    return sorted(list(cleaned))

def verify_adapter_integrity(adapter_url: str):
    """校验适配器内容 SHA-256。
    - 若传入 file://，必须为绝对路径，仅验证本地文件内容散列。
    - 若未指定，则从 OFFICIAL_ADAPTER_URL 下载验证。
    - 禁止任意其它远程 URL 覆盖。
    """
    if adapter_url.startswith('file://'):
        parsed = urllib.parse.urlsplit(adapter_url)
        file_path_str = urllib.parse.unquote(parsed.path)
        if not posixpath.isabs(file_path_str):
            raise ValueError(f"Local test adapter must use an absolute path: '{adapter_url}'")
        norm_path = posixpath.normpath(file_path_str)
        if norm_path != file_path_str or '..' in file_path_str.split('/'):
            raise ValueError(f"Path traversal detected in file URI: '{adapter_url}'")

        path = Path(file_path_str)
        if not path.is_file():
            raise FileNotFoundError(f"Local test adapter file not found: {path}")
        content = path.read_bytes()
    elif adapter_url == OFFICIAL_ADAPTER_URL:
        validate_secure_url(adapter_url, allowed_prefixes=(OFFICIAL_ADAPTER_URL,))
        opener = urllib.request.build_opener(SafeRedirectHandler)
        req = urllib.request.Request(
            adapter_url,
            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
        )
        with opener.open(req, timeout=15) as resp:
            content = resp.read()
    else:
        raise ValueError(
            f"Arbitrary remote override is strictly forbidden. "
            f"Only the official HTTPS URL or a local 'file://' absolute path is accepted."
        )

    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != EXPECTED_ADAPTER_SHA256:
        raise ValueError(
            f"Adapter script SHA-256 mismatch!\n"
            f"Expected: {EXPECTED_ADAPTER_SHA256}\n"
            f"Actual:   {actual_hash}\n"
            f"Refusing to proceed with untrusted/modified adapter."
        )

def normalize_jq_expression(raw_jq: str) -> str:
    """仅剥去一对匹配的最外层单/双引号，并将 JQ 字符串中的 \\\" 规范化为 \"。"""
    expr = raw_jq.strip()
    if len(expr) >= 2 and (
        (expr.startswith("'") and expr.endswith("'")) or
        (expr.startswith('"') and expr.endswith('"'))
    ):
        expr = expr[1:-1].strip()
    return expr.replace(r'\"', '"')

def convert_rule_file(content: str, timestamp_str: str, public_script_url: str = OFFICIAL_ADAPTER_URL):
    """核心 AST/行级转换引擎。生产 YAML 恒定写入 public_script_url。"""
    rules = []
    rewrites = []
    scriptings = []
    mitm_hosts = []
    incompatible_rules = []
    unknown_rules = []

    stats = {
        'total_actionable': 0,
        'rules_converted': 0,
        'rewrites_json': 0,
        'rewrites_204': 0,
        'scripts_converted': 0,
        'jq_handled': 0,
        'unknown_rules_count': 0,
    }

    script_id = 0

    for idx, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//') or line.startswith(';'):
            continue
        if line.startswith(('#!name', '#!desc', '#!tag', '#!author', '#!date', '#!homepage', '#!icon')):
            continue
        if line.startswith('[') and line.endswith(']'):
            continue

        stats['total_actionable'] += 1
        handled = False

        # 1. DOMAIN / DOMAIN-SUFFIX
        if line.startswith(('DOMAIN,', 'DOMAIN-SUFFIX,', 'domain,', 'domain-suffix,')):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                rtype, domain, policy = parts[0].upper(), parts[1], parts[2].upper()
                if domain == 'ad.12306.cn' and policy == 'DIRECT':
                    handled = True
                    continue
                if 'SUFFIX' in rtype:
                    rules.append({'domain_suffix': {'match': domain, 'policy': policy}})
                else:
                    rules.append({'domain': {'match': domain, 'policy': policy}})
                stats['rules_converted'] += 1
                handled = True
            else:
                stats['unknown_rules_count'] += 1
                unknown_rules.append({'line_num': idx, 'raw': line, 'reason': 'Malformed DOMAIN rule'})
                continue

        # 2. JQ 转换（剥除外层匹配引号并转义后做严格全文比对）
        if 'response-body-json-jq' in line:
            match = re.search(r'^(\S+)\s+response-body-json-jq\s+(.+)$', line)
            if match:
                pattern = match.group(1).strip()
                raw_jq_expr = match.group(2).strip()
                norm_jq = normalize_jq_expression(raw_jq_expr)

                matched_mode = None
                if norm_jq in ('.data={}', '.data = {}'):
                    matched_mode = 'qeeniao_clear_data'
                elif norm_jq == '.data.model.children |= map(select(.name | contains("营销") | not))':
                    matched_mode = 'taobao_filter_marketing'

                if matched_mode:
                    script_id += 1
                    scriptings.append({
                        'http_response': {
                            'name': f'jq_adapter_{matched_mode}_{script_id}',
                            'match': pattern,
                            'script_url': public_script_url,
                            'env': {
                                'MODE': matched_mode
                            },
                            'body_required': True,
                            'timeout': 10,
                            'update_interval': 86400
                        }
                    })
                    stats['jq_handled'] += 1
                    handled = True
                else:
                    incompatible_rules.append({
                        'line_num': idx,
                        'raw': line,
                        'reason': f"Unrecognized JQ expression without semantic adapter: '{raw_jq_expr}' (normalized: '{norm_jq}')"
                    })
            continue

        # 3. 重写动作精准映射
        tokens = ['reject-200', 'reject-dict', 'reject-img', 'reject-drop', 'reject', 'url 200', 'url reject']
        matched_token = next((t for t in tokens if t in line), None)
        if matched_token:
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
                is_media = bool(re.search(r'\.(png|jpe?g|webp|gif|mp4)(\?|$)', pattern, re.IGNORECASE))
                if matched_token in ('reject-img', 'reject-drop', 'reject', 'url reject') or is_media:
                    rewrites.append({
                        'match': pattern,
                        'actions': [{'respond': {'status': 204}}]
                    })
                    stats['rewrites_204'] += 1
                else:
                    rewrites.append({
                        'match': pattern,
                        'actions': [{'respond': {'status': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{}'}}]
                    })
                    stats['rewrites_json'] += 1
                handled = True
            continue

        # 4. 外部脚本规则提取
        if 'script-response-body' in line or 'script-path=' in line:
            match_pattern = None
            script_url = None

            match_a = re.search(r'^(\S+)\s+url\s+script-response-body\s+(\S+)', line)
            if match_a:
                match_pattern = match_a.group(1).strip()
                script_url = match_a.group(2).strip()

            match_b = re.search(r'script-path=([^\s,]+)', line)
            if match_b:
                script_url = match_b.group(1).strip()
                target_part = re.sub(r'script-path=[^\s,]+', '', line)
                target_tokens = target_part.split()
                for token in target_tokens:
                    if token.startswith('^') or '://' in token:
                        match_pattern = token.strip()
                        break

            if match_pattern and script_url:
                validate_secure_url(script_url, allowed_prefixes=EXACT_SCRIPT_PREFIXES)

                script_id += 1
                scriptings.append({
                    'http_response': {
                        'name': f'adblock_script_{script_id}',
                        'match': match_pattern,
                        'script_url': script_url,
                        'body_required': True,
                        'timeout': 10,
                        'update_interval': 86400
                    }
                })
                stats['scripts_converted'] += 1
                handled = True
            continue

        # 5. MITM 域名列表行
        if line.startswith(('hostname =', 'hostname=', 'includes =', 'includes=')):
            hosts_str = line.split('=', 1)[1]
            for h in hosts_str.split(','):
                h = h.strip()
                if h:
                    mitm_hosts.append(h)
            handled = True
            continue

        if not handled:
            stats['unknown_rules_count'] += 1
            unknown_rules.append({'line_num': idx, 'raw': line, 'reason': 'Unrecognized rule syntax'})

    # 门禁 1: JQ 不兼容规则硬失败
    if incompatible_rules:
        details = "\n".join([f"  Line {r['line_num']}: {r['raw']}\n    -> {r['reason']}" for r in incompatible_rules])
        raise ValueError(f"Quality Gate Failed: Unresolved JQ rules detected. Refusing to release incomplete module:\n{details}")

    # 门禁 2: 审计丢失率
    converted_total = (
        stats['rules_converted']
        + stats['rewrites_json']
        + stats['rewrites_204']
        + stats['scripts_converted']
        + stats['jq_handled']
    )
    unhandled_count = stats['unknown_rules_count']
    loss_rate = (unhandled_count / stats['total_actionable']) if stats['total_actionable'] > 0 else 1.0

    print(f"[AUDIT] Total Actionable: {stats['total_actionable']}, Converted: {converted_total}, Unhandled: {unhandled_count} (Loss: {loss_rate:.2%})")

    if loss_rate > 0.01 or unhandled_count > 0:
        details = "\n".join([f"  Line {u['line_num']}: {u['raw']} ({u['reason']})" for u in unknown_rules[:5]])
        raise ValueError(f"Quality Gate Breached: Loss rate {loss_rate:.2%} ({unhandled_count} unhandled rules). Samples:\n{details}")

    sanitized_mitm = sanitize_mitm_hostnames(mitm_hosts)

    description = (
        f"全网 400+ 应用开屏净化（基于 ddgksf2013 规则清洗）。\n"
        f"有效拦截: {converted_total} 条 | MitM 域名: {len(sanitized_mitm)} 个\n"
        f"更新时间: {timestamp_str} | 同步状态: 成功"
    )

    module_data = {
        'name': '墨鱼去开屏 🅗',
        'icon': 'shield.lefthalf.filled',
        'description': description,
        'dns': {},
        'rules': rules,
        'rewrites': rewrites,
        'scriptings': scriptings,
        'mitm': {'hostnames': {'includes': sanitized_mitm}}
    }

    return module_data, stats

def verify_egern_yaml_structure(data: dict):
    """校验转换结果完全符合 Egern 规范。"""
    required = ['name', 'description', 'dns', 'rules', 'rewrites', 'scriptings', 'mitm']
    for key in required:
        if key not in data:
            raise KeyError(f"Missing mandatory Egern key: {key}")

    if not isinstance(data['rules'], list) or not isinstance(data['rewrites'], list) or not isinstance(data['scriptings'], list):
        raise TypeError("Fields 'rules', 'rewrites', and 'scriptings' must be lists.")

    if 'hostnames' not in data.get('mitm', {}) or 'includes' not in data['mitm']['hostnames']:
        raise KeyError("Egern structure requires 'mitm.hostnames.includes'.")

    for rw in data['rewrites']:
        if 'match' not in rw or 'actions' not in rw:
            raise ValueError(f"Malformed rewrite object: {rw}")
        for act in rw['actions']:
            if 'respond' in act and 'status' not in act['respond']:
                raise ValueError(f"Action respond missing status: {act}")

    for sc in data['scriptings']:
        key = next((k for k in ['http_response', 'http_request'] if k in sc), None)
        if not key:
            raise ValueError(f"Malformed scripting block: {sc}")
        if 'match' not in sc[key] or 'script_url' not in sc[key]:
            raise ValueError(f"Egern scripting missing 'match' or valid 'script_url': {sc}")
        if 'env' in sc[key] and not isinstance(sc[key]['env'], dict):
            raise TypeError(f"Scripting env must be a dictionary: {sc}")

    return True

def run_internal_tests():
    """内部单元与边界测试集。不依赖远端已存在的脚本。"""
    print(">>> Executing internal regression tests...")

    # 1. 验证本地文件 adapter 的 SHA-256 计算与校验
    local_adapter = ROOT / 'scripts' / 'ddgksf-splash-adapter.js'
    if local_adapter.is_file():
        file_uri = f"file://{local_adapter.resolve().as_posix()}"
        verify_adapter_integrity(file_uri)
    else:
        try:
            verify_adapter_integrity("file:///non_existent_adapter_file.js")
            assert False, "Non-existent file URI must fail"
        except FileNotFoundError:
            pass

    # 2. 禁止任意远程 override
    try:
        verify_adapter_integrity("https://raw.githubusercontent.com/evil/repo/main/adapter.js")
        assert False, "Arbitrary remote URL must be blocked"
    except ValueError as e:
        assert "Arbitrary remote override is strictly forbidden" in str(e)

    # 3. 验证真实带引号/转义形式与无引号形式的 JQ 规范化与严格匹配
    jq_conf_real_quoted = (
        r"^https?:\/\/api\.qeeniao\.com\/nap\/ad response-body-json-jq '.data={}'" "\n"
        r"^https?:\/\/acs\.m\.taobao\.com\/gw\/mtop\.alibaba.*mytab response-body-json-jq '.data.model.children |= map(select(.name | contains(\"营销\") | not))'" "\n"
    )
    mod, st = convert_rule_file(jq_conf_real_quoted, "2026-11-02 20:00:00")
    assert len(mod['scriptings']) == 2
    assert mod['scriptings'][0]['http_response']['env']['MODE'] == 'qeeniao_clear_data'
    assert mod['scriptings'][0]['http_response']['script_url'] == OFFICIAL_ADAPTER_URL
    assert mod['scriptings'][1]['http_response']['env']['MODE'] == 'taobao_filter_marketing'
    assert mod['scriptings'][1]['http_response']['script_url'] == OFFICIAL_ADAPTER_URL

    jq_conf_unquoted = (
        "^https://api.qeeniao.com/nap/ad response-body-json-jq .data={}\n"
        '^https://acs.m.taobao.com/gw/mtop.alibaba.*mytab response-body-json-jq .data.model.children |= map(select(.name | contains("营销") | not))\n'
    )
    mod2, st2 = convert_rule_file(jq_conf_unquoted, "2026-11-02 20:00:00")
    assert len(mod2['scriptings']) == 2
    assert mod2['scriptings'][0]['http_response']['env']['MODE'] == 'qeeniao_clear_data'
    assert mod2['scriptings'][1]['http_response']['env']['MODE'] == 'taobao_filter_marketing'

    # 4. 未知 JQ 规则必须 Hard Fail
    jq_conf_fail = "^https://api.unknown.com/ad response-body-json-jq '.data.unknown |= empty'"
    try:
        convert_rule_file(jq_conf_fail, "2026-11-02 20:00:00")
        assert False, "Unknown JQ must trigger Hard Fail"
    except ValueError as e:
        assert "Quality Gate Failed" in str(e)

    # 5. 畸形 DOMAIN 行不遗漏并触发质量门禁
    malformed_domain_conf = "DOMAIN,invalid_single_field\n"
    try:
        convert_rule_file(malformed_domain_conf, "2026-11-02 20:00:00")
        assert False, "Malformed DOMAIN rule must cause failure"
    except ValueError as e:
        assert "Quality Gate Breached" in str(e)

    # 6. MITM 时序：先规范化展开，再过滤非法 IP
    test_hosts = ['*ziben.com', '*.flyert.*', '120.241.*', '10.0.0.1', 'api.test.com']
    cleaned_hosts = sanitize_mitm_hostnames(test_hosts)
    assert '*.ziben.com' in cleaned_hosts
    assert '*.flyert.com' in cleaned_hosts and 'www.flyert.com' in cleaned_hosts
    assert '10.0.0.1' not in cleaned_hosts and '120.241.*' not in cleaned_hosts

    print(">>> All internal regression tests passed successfully.")
    return 0

def fetch_content_with_safe_redirects(url: str):
    """带重定向强校验的下载器。"""
    validate_secure_url(url, allowed_hosts=ALLOWED_FETCH_HOSTS)
    opener = urllib.request.build_opener(SafeRedirectHandler)
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
    )
    with opener.open(req, timeout=15) as resp:
        return resp.read().decode('utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='执行试运行验证')
    parser.add_argument('--test', action='store_true', help='执行内置回归单测')
    parser.add_argument(
        '--adapter-url',
        default=OFFICIAL_ADAPTER_URL,
        help='适配器 URL 校验源。生产默认从官方 HTTPS 下载；测试时仅接受 file:// 绝对路径以核验本地文件散列。'
    )
    args = parser.parse_args()

    if args.test:
        return run_internal_tests()

    # 适配器完整性与 SHA-256 门禁前置校验
    verify_adapter_integrity(args.adapter_url)

    now_shanghai = datetime.now(ZoneInfo('Asia/Shanghai'))
    timestamp_str = now_shanghai.strftime('%Y-%m-%d %H:%M:%S (Asia/Shanghai)')
    old_meta = json.loads(META.read_text(encoding='utf-8')) if META.exists() else {}

    try:
        content = None
        success_url = None

        for url in CANDIDATE_URLS:
            try:
                data = fetch_content_with_safe_redirects(url)
                if 'ddgksf2013' in data and not any(tag in data for tag in ['<!DOCTYPE html>', '<html']):
                    content = data
                    success_url = url
                    break
            except Exception as e:
                print(f"[FETCH FAILED] {url}: {e}", file=sys.stderr)
                continue

        if not content:
            raise RuntimeError("All candidate sources failed fetching or security verification.")

        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # 生成模块；无论测试时 adapter 是不是通过 file:// 验证，输出的 YAML 恒定写 OFFICIAL_ADAPTER_URL
        module_data, stats = convert_rule_file(content, timestamp_str, public_script_url=OFFICIAL_ADAPTER_URL)
        verify_egern_yaml_structure(module_data)

        print("\n=================== 规则转换与质量审计报告 ===================")
        print(f"数据来源: {success_url}")
        print(f"原始可执行指令行: {stats['total_actionable']}")
        print(f"|- 域名过滤规则 (Rules): {stats['rules_converted']}")
        print(f"|- 重写规则 (Rewrites):")
        print(f"   |- 空 JSON (API 阻断): {stats['rewrites_json']} 条")
        print(f"   |- 204 No Content (媒体/纯网络阻断): {stats['rewrites_204']} 条")
        print(f"|- JQ 规则适配 (Dedicated Adapter Scripts): {stats['jq_handled']} 条")
        print(f"|- 外部 JS 脚本规则: {stats['scripts_converted']} 条")
        print(f"|- MitM 域名总数: {len(module_data['mitm']['hostnames']['includes'])} 个")
        print("==============================================================")

        if args.dry_run:
            print("[DRY-RUN] 校验全部通过，试运行成功。")
            return 0

        if old_meta.get('source_sha256') == content_hash and MODULE.exists():
            print("Upstream unchanged. Updating check timestamp only.")
            old_meta['last_checked'] = timestamp_str
            META.write_text(json.dumps(old_meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            return 0

        yaml_output = yaml.dump(module_data, Dumper=EgernSafeDumper, allow_unicode=True, sort_keys=False, width=1000)
        yaml.safe_load(yaml_output)

        MODULE.write_text(yaml_output, encoding='utf-8')

        meta = {
            'status': 'ok',
            'last_checked': timestamp_str,
            'last_updated': timestamp_str,
            'source_url': success_url,
            'source_sha256': content_hash,
            'adapter_url': OFFICIAL_ADAPTER_URL,
            'rules_count': len(module_data['rules']) + len(module_data['rewrites']) + len(module_data['scriptings'])
        }
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"正式更新成功！模块已生成: {MODULE.name}")
        return 0

    except Exception as e:
        error_msg = str(e)
        print(f"\n[FATAL ERROR] 同步流程异常中断: {error_msg}", file=sys.stderr)
        if MODULE.exists():
            meta = dict(old_meta, status='failed', last_checked=timestamp_str, error=error_msg)
            META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print("现有 YAML 模块保持不变，失败记录已写入状态 JSON。", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
