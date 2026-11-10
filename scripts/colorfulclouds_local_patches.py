"""Local Caiyun patches. Kept separate from upstream sync and Egern module generation.

The patch intentionally preserves the currently working A03 assistant removal.
Upstream structural changes must pass compatibility checks before publication.
"""
import subprocess
import tempfile

UPSTREAM_URL = 'https://raw.githubusercontent.com/ddgksf2013/Scripts/master/caiyun_json.js'

def adapt(source):
    if len(source) < 100 or len(source) > 200000:
        raise ValueError('Unexpected source size')
    if any(token in source for token in ['<html', '<!DOCTYPE', '404: Not Found', 'eval(', '$httpClient', '$task.fetch', 'import(']):
        raise ValueError('Unexpected upstream content or network code')
    # 本地精确修复：保留天气活动配置，仅禁用 A03 运营悬浮入口和 A08 双十一推广。
    legacy = "$request.url.includes(\"activity\")?responseBody=$request.url.includes(\"type_id=A03\")?{status:\"ok\",activities:[{type:\"tabbar\",name:\"aichat\",feature:!1}]}:{status:\"ok\",activities:[{items:[{}]}]}:"
    patched = '$request.url.includes("activity")?(responseBody=$request.url.includes("type_id=A03")?{status:"ok",activities:[{type:"tabbar",name:"aichat",feature:!1}]}:JSON.parse($response.body),$request.url.includes("type_id=A08")&&Array.isArray(responseBody.activities)&&(responseBody.activities=[]),Array.isArray(responseBody.activities)&&(responseBody.activities=responseBody.activities.map(e=>e&&["operational","operational_show"].includes(e.name)?Object.assign({},e,{feature:!1}):e))):'
    if legacy not in source:
        raise ValueError('Upstream activity handler changed; review before syncing')
    source = source.replace(legacy, patched)
    source = source.replace(':$done({}),$done({body:JSON.stringify(responseBody)})', ':responseBody=JSON.parse($response.body),$done({body:JSON.stringify(responseBody)})')
    source = source.replace('let responseBody={};$request.url.includes', 'let responseBody=JSON.parse($response.body);$request.url.includes')
    source = source.replace(':responseBody=JSON.parse($response.body),$done({body:JSON.stringify(responseBody)});', ':0,$done({body:JSON.stringify(responseBody)});')
    source = source.replace('$done({body:JSON.stringify(responseBody)});', '$done({body:JSON.stringify(hideWeatherFeedback(responseBody))});')
    feedback_helper = "function hideWeatherFeedback(root){const match=x=>{if(!x||typeof x!==\"object\")return false;const s=[x.name,x.title,x.text,x.label,x.key,x.id,x.action,x.url].filter(v=>typeof v===\"string\").join(\" \").toLowerCase();return /反馈天气|天气反馈|feedback.weather|weather.feedback|weather_feedback|feedback_weather|weatherfeedback/.test(s)};const walk=(x,d)=>{if(!x||typeof x!==\"object\"||d>8)return x;if(Array.isArray(x))return x.filter(v=>!match(v)).map(v=>walk(v,d+1));for(const k of Object.keys(x)){if(/^(weather_feedback|feedback_weather|weatherFeedback|feedbackWeather)$/.test(k)){if(typeof x[k]===\"boolean\")x[k]=false;else if(x[k]&&typeof x[k]===\"object\")x[k]={...x[k],enabled:false,visible:false,show:false}}else x[k]=walk(x[k],d+1)}return x};return walk(root,0)}\n"
    result = ('/* 墨鱼 ddgksf2013 彩云天气去广告脚本镜像；补充异常透传与单次完成包装。\n'
              ' * Source: ' + UPSTREAM_URL + '\n */\n'
              '(function (complete) {\nlet finished = false;\n'
              'const $done = value => { if (!finished) { finished = true; complete(value); } };\n'
              'try {\nif (typeof $response === "undefined" || typeof $response.body !== "string") return $done({});\n'
              + feedback_helper + source + '\n} catch (_) { $done({}); }\n})($done);\n')
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w') as handle:
        handle.write(result)
        handle.flush()
        check = subprocess.run(['node', '--check', handle.name], capture_output=True, text=True, timeout=15)
        if check.returncode:
            raise ValueError('JavaScript syntax check failed')
    return result
