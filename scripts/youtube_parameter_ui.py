"""Chinese native Egern settings wired into unchanged upstream legacy scripts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OWN='https://raw.githubusercontent.com/huangkouping/egern/main/'
UI_VERSION='20261101-1'
def boolean(name,description,default):
    return {'type':'boolean','name':name,'description':description,'default':default}
def choice(name,description,default,values,custom=False):
    return {'type':'choice','name':name,'description':description,'default':default,'values':values,'custom':custom}
def fields(flavor,module):
    args=module.get('compat_arguments',{})
    if flavor=='enhance':
        b=lambda key:args.get(key,'false') in [True,'true']
        defaults={'blockUpload':b('屏蔽上传按钮'),'blockShorts':b('屏蔽Shorts按钮'),'blockImmersive':b('屏蔽选段按钮'),
                  'captionLang':args.get('字幕翻译语言','off'),'debug':b('启用调试模式')}
        return defaults,{
          'blockUpload':boolean('[底栏] 隐藏上传按钮','隐藏 YouTube 底栏的上传入口。',defaults['blockUpload']),
          'blockShorts':boolean('[底栏] 隐藏 Shorts 按钮','只控制底栏按钮，不承诺移除所有 Shorts 内容。',defaults['blockShorts']),
          'blockImmersive':boolean('[Music] 隐藏选段按钮','隐藏 YouTube Music 底栏的选段入口。',defaults['blockImmersive']),
          'captionLang':choice('[翻译] 字幕语言','同时使用双语翻译模块时建议选“关闭”，避免重复处理。',defaults['captionLang'],
             {'关闭':'off','简体中文':'zh-Hans','繁體中文':'zh-Hant','日语':'ja','韩语':'ko','英语':'en'},True),
          'debug':boolean('[调试] 输出日志','仅在排查异常时开启，正常使用可关闭。',defaults['debug'])
        }
    # Native controls are primary by default; the user can explicitly prefer the official web panel.
    defaults=dict(args);defaults['Storage']='Argument'
    return defaults,{
      'Type':choice('[字幕] 处理方式','官方字幕使用 YouTube 翻译轨道；翻译引擎模式另外调用翻译服务。',args.get('Type','Official'),
        {'官方字幕（双语合成）':'Official','翻译字幕（翻译引擎）':'Translate'}),
      'AutoCC':boolean('[字幕] 自动显示','开启后自动显示字幕；关闭后不强制开启，沿用App自己的选择。视频仍需提供字幕轨道。',args.get('AutoCC','true') in [True,'true']),
      'ShowOnly':boolean('[字幕] 仅显示译文','关闭为“原文＋译文”；开启后仅显示译文。',args.get('ShowOnly','false') in [True,'true']),
      'Position':choice('[字幕] 原文位置','仅在双语显示时区分原文与译文的上下顺序。',args.get('Position','Forward'),
        {'原文在上（第一行）':'Forward','原文在下（第二行）':'Reverse'}),
      'Vendor':choice('[翻译] 服务商','Google 通常无需密钥；Microsoft 的 API 信息在官方在线设置中填写。',args.get('Vendor','Google'),
        {'Google（免配置）':'Google','Microsoft（需 API）':'Microsoft'}),
      'Storage':choice('[设置] 优先使用哪处设置','默认使用本页设置；选“在线设置优先”后，官方设置面板或 BoxJS 保存的同名参数可覆盖本页。','Argument',
        {'模块设置优先':'Argument','官方在线设置优先':'PersistentStore','仅使用脚本默认值':'database'}),
      'LogLevel':choice('[调试] 日志等级','正常使用选“警告”或“关闭”；排查异常时再开启调试。',args.get('LogLevel','WARN'),
        {'关闭':'OFF','仅错误':'ERROR','警告':'WARN','信息':'INFO','调试':'DEBUG','全部':'ALL'})
    }
def schema_for(items):
    schema={}
    for key,item in items.items():
        if item['type']=='boolean':
            default='true' if item['default'] else 'false';options=['true','false']
        else:
            default=next((label for label,value in item['values'].items() if value==item['default']),str(item['default']))
            options=list(item['values'])
        schema[key]={'name':item['name'],'description':item['description'],'default_value':default,'options':options}
    return schema
def render(source,defaults,items,fmt,hook):
    wrapper=(ROOT/'scripts/youtube-parameter-wrapper.js').read_text()
    spec={'defaults':defaults,'fields':items,'format':fmt,'hook':hook}
    # str.replace is literal: original script bytes are not parsed or rewritten.
    return wrapper.replace('UI_SPEC',json.dumps(spec,ensure_ascii=False,separators=(',',':'))).replace('SOURCE_CODE',source)
def apply_ui(module,sources,flavor):
    defaults,items=fields(flavor,module)
    module['env_schema']=schema_for(items)
    if flavor=='subtitles':module['compat_arguments']['Storage']='Argument'
    module['compat_arguments_desc']+='\n\n中文参数界面：在 Egern 模块环境变量中使用上面的开关和选择器。未主动设置的项目沿用显示的默认值。双语模块默认“模块设置优先”，仍保留官方在线设置入口；切换优先级后同名配置按所选来源生效。原作者脚本主体保持原样，参数适配与上游更新分开维护。'
    outputs={};provenance={}
    for row in module['scriptings']:
        entry=next(iter(row.values()));upstream=entry['script_url']
        if flavor=='subtitles':
            if not any('/'+repo+'/' in upstream for repo in ['DualSubs/YouTube','DualSubs/Universal']) or not upstream.endswith('.js'):continue
            name=upstream.rsplit('/',1)[-1]
            kind={'request.bundle.js':'request','response.bundle.js':'response',
                  'Composite.Subtitles.response.bundle.js':'composite','Translate.response.bundle.js':'translate'}.get(name)
            if not kind:raise ValueError('Unknown DualSubs parameter script')
            filename='youtube-subtitles-ui-'+kind+'.js';fmt='query'
        else:
            name=upstream.rsplit('/',1)[-1];kind='request' if name=='youtube.request.js' else 'response'
            filename='youtube-enhance-ui-'+kind+'.js';fmt='json'
        if upstream not in sources:raise ValueError('Missing upstream source for parameter UI')
        source=sources[upstream];generated=render(source,defaults,items,fmt,kind)
        outputs[filename]=generated
        provenance[filename]={'upstream_url':upstream,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                              'script_sha256':hashlib.sha256(generated.encode()).hexdigest()}
        entry['script_url']=OWN+filename+'?v='+provenance[filename]['script_sha256'][:12]
        entry['update_interval']=21600
    return outputs,provenance
