#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

AI_UPSTREAM = "https://kelee.one/Tool/Loon/Lsr/AI.lsr"
GOOGLEVOICE_UPSTREAM = "https://github.com/blackmatrix7/ios_rule_script/raw/master/rule/Loon/GoogleVoice/GoogleVoice.list"
OUTPUT = Path("us.list")

EXTRA_AI_RULES = [
    # Midjourney
    "DOMAIN-SUFFIX,midjourney.com",
    "DOMAIN-SUFFIX,midjourneycdn.com",
    # Runway
    "DOMAIN-SUFFIX,runwayml.com",
    "DOMAIN-SUFFIX,runwayml.cloud",
    # ElevenLabs
    "DOMAIN-SUFFIX,elevenlabs.io",
    # Suno
    "DOMAIN-SUFFIX,suno.com",
    # Cursor
    "DOMAIN-SUFFIX,cursor.com",
    "DOMAIN-SUFFIX,cursor.sh",
    # Character.AI
    "DOMAIN-SUFFIX,character.ai",
    # Ideogram
    "DOMAIN-SUFFIX,ideogram.ai",
    # Leonardo
    "DOMAIN-SUFFIX,leonardo.ai",
    # Replit
    "DOMAIN-SUFFIX,replit.com",
    "DOMAIN-SUFFIX,replit.dev",
    # Luma
    "DOMAIN-SUFFIX,lumalabs.ai",
    # Pika
    "DOMAIN-SUFFIX,pika.art",
    # Gamma
    "DOMAIN-SUFFIX,gamma.app",
    # Cohere
    "DOMAIN-SUFFIX,cohere.com",
    "DOMAIN-SUFFIX,cohere.ai",
]

MUSE_RULES = [
    "DOMAIN-SUFFIX,meta.ai",
    "DOMAIN-SUFFIX,ai.meta.com",
    "DOMAIN-SUFFIX,muse.com",
    "DOMAIN-SUFFIX,muse.ai",
    "DOMAIN,api.meta.ai",
    "DOMAIN,graph.meta.ai",
    "DOMAIN,www.meta.ai",
    "DOMAIN-KEYWORD,meta-ai",
    "DOMAIN-KEYWORD,metaai",
]

def fetch(url, referer=None):
    headers = {
        "User-Agent": "Loon/852 CFNetwork/3860.300.31 Darwin/25.2.0",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8-sig")

def collect(raw, seen):
    rules = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            rules.append(line)
    return rules

seen = set()
ai_rules = collect(fetch(AI_UPSTREAM, "https://kelee.one/"), seen)
googlevoice_rules = collect(fetch(GOOGLEVOICE_UPSTREAM, "https://github.com/"), seen)

custom_rules = []
for rule in EXTRA_AI_RULES + MUSE_RULES:
    if rule not in seen:
        seen.add(rule)
        custom_rules.append(rule)

now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")

lines = [
    "# US 服务代理规则集",
    "# 本文件由 GitHub Actions 自动同步生成，请勿直接编辑",
    f"# 规则内容更新时间（北京时间）：{now}",
    f"# AI 上游：{AI_UPSTREAM}",
    f"# Google Voice 上游：{GOOGLEVOICE_UPSTREAM}",
    '# 使用方法：在 Egern 中订阅本文件，并将策略设置为“美国节点”或你的 US 策略组',
    "# 同步策略：AI + 海外主流 AI 补充 + Muse + Google Voice",
    "",
    "# ===== AI 服务（可莉上游同步） =====",
    *ai_rules,
    "",
    "# ===== 海外主流 AI + Muse 自定义补充规则 =====",
    *custom_rules,
    "",
    "# ===== Google Voice（Blackmatrix7 上游同步） =====",
    *googlevoice_rules,
    "",
]
OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(
    f"已生成 {OUTPUT}：AI {len(ai_rules)} 条，"
    f"自定义 {len(custom_rules)} 条，Google Voice {len(googlevoice_rules)} 条"
)
