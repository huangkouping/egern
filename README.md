# Egern 规则与模块©️

本仓库收录 Egern 分流规则、去广告模块、自动签到和链接跳转模块。当前提供 **3 个规则集、5 个模块**，以及配套脚本与定时同步任务。

模块名称统一使用 **©️** 标识。下面的「订阅」和「安装」链接均为 Raw 文件地址，可复制到 Egern 中使用；「源码」用于查看配置。

## 目录

- [规则集](#规则集)
- [去广告模块](#去广告模块)
- [签到模块](#签到模块)
- [链接跳转模块](#链接跳转模块)
- [安装与使用](#安装与使用)
- [定时更新与同步状态](#定时更新与同步状态)
- [上游来源](#上游来源)
- [配套文件](#配套文件)

## 规则集

规则集用于指定流量走哪个策略，不包含完整的节点配置，也不会自动创建策略组。

| 名称 | 用途与范围 | 建议策略 | 链接 |
| --- | --- | --- | --- |
| 苹果服务规则©️ | Apple News、部分地区受限服务及指定 Apple 服务入口。排除 `icloud.com` 及其子域名，让这部分继续由直连规则处理。 | 苹果服务，或自行选择的代理策略组 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/apple-service-proxy.list) · [源码](https://github.com/huangkouping/egern/blob/main/apple-service-proxy.list) |
| 直连规则集©️ | 微信、抖音、小红书的正常内容防误杀，以及 Apple 推送、账号、下载、CDN、iCloud 等基础服务直连。 | DIRECT | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/custom-direct.list) · [源码](https://github.com/huangkouping/egern/blob/main/custom-direct.list) |
| Ai&US规则集©️ | 合并海外 AI 服务、Muse / Meta AI、自定义 AI 补充及 Google Voice 上游规则。包含 ChatGPT、Claude、Gemini、Copilot、Perplexity、Manus、Cue 等相关域名。 | 美国节点，或自己的 US 策略组 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/us.list) · [源码](https://github.com/huangkouping/egern/blob/main/us.list) |

### 分流说明

- **苹果服务规则**包含 `itunes.com`、`iphonesubmissions.apple.com`、`kt-prod.ess.apple.com`、`humb.apple.com` 等自定义代理项；并非全部 Apple 流量都走代理。
- **直连规则集**用于恢复正常服务，不能代替完整的国内分流规则集；部分规则覆盖整个域名及子域名。
- **Ai&US规则集**包含上游提供的公共依赖域名，因此部分匹配范围会超过单一 AI 产品；选择美国节点也不等于保证服务账号具备地区资格。
- 多个规则集可能覆盖相同域名，例如 `sentry.io`。请根据实际用途安排优先级，并在 Egern 的连接记录中确认最终命中策略。

## 去广告模块

| 名称 | 功能 | 设置与范围 | 链接 |
| --- | --- | --- | --- |
| 小红书去直播广告©️ | 过滤开屏、首页「发现」商业广告、直播卡片，以及作者正在直播的普通笔记；支持疑似医美推广过滤。 | 各功能可独立开关；保留未命中过滤条件的普通图文、视频及商品笔记。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaohongshu-homefeed-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.yaml) |
| 小羞片网站去广告©️ | 合并指定网站的网页广告清理、CMS 视频播放列表插播过滤，以及 Pornhub 网页过滤与广告接口处理。 | 包含自编网页脚本及同步适配的上游脚本；仅处理配置中匹配的网址或播放资源。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/attract-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/attract-adblock.yaml) |
| 京东全方位去广告（增强版）©️ | 用户提供的开屏、浮层、搜索推广及物料拦截配置；包含指定 HTTPDNS 入口与 API UDP 443 阻断。 | 未实机验证；整体拦截 welcomeHome 可能影响正常首页。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/jd-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/jd-adblock.yaml) |

### 小红书去直播广告©️

模块内可设置以下开关，当前默认均为开启：

| 开关 | 作用 |
| --- | --- |
| 屏蔽首页广告 | 过滤首页「发现」信息流中的商业投放广告。 |
| 屏蔽首页直播 | 过滤直播卡片，以及带作者直播状态的普通笔记。 |
| 屏蔽疑似医美推广 | 组合账号与内容特征识别；可能误删，可关闭。 |
| 屏蔽开屏广告 | 处理开屏素材与投放决策。 |
| 屏蔽广告素材库 | 清理广告素材接口中的图片与视频链接。 |
| 屏蔽广告互动内容 | 清理广告互动接口中的图片与跳转信息。 |

适用范围为配置中匹配的 App 接口，并非所有页面或所有商业内容。查看脚本日志可了解单次请求的过滤数量。

### 小羞片网站去广告©️

**网页部分**覆盖 911 爆料网、黑料网等已收录入口及镜像：

| 类型 | 当前匹配范围 |
| --- | --- |
| 指定入口 | `attract.gaqwvqor.cc`、`ancient.gaqwvqor.cc`、`asleep.gaqwvqor.cc` |
| 域名及可选一层子域名 | `blw66.com`、`911bla.com`、`911aa2.com`、`911bg20.com`、`ckspzdnd.cc`、`fytdugpm.cc`、`91jq508.com`、`lgyggwws.cc`、`pjitqyei.cc`、`hlwf22.com`、`heiliao.com`、`91cg1.com`、`lhrkglii.cc`、`iadapjby.cc`、`qxrguuar.cc`、`lhxgoxlj.cc`、`heiliao88.com` |
| 指定 CloudFront 镜像 | `d9altmxkp5q0i.cloudfront.net`、`d169l2tv32yjx4.cloudfront.net` |
| Pornhub | `cn.pornhub.com`、`www.pornhub.com` |

**视频部分**同步 CMS 上游的资源匹配规则及脚本，处理符合条件的 M3U8 播放列表。页面是否使用已匹配的播放器资源，会影响过滤效果；新增镜像也需要收录到配置中。

### 京东全方位去广告（增强版）©️

基于用户提供的配置发布，仅修正 Egern 的域名、UDP、443 端口组合规则写法，不沿用此前已删除的京东过滤脚本。此版本无远程 JavaScript，也未配置上游定时同步。

- `welcomeHome` 返回空对象会影响整个首页响应，不是只删除广告楼层；可能出现内容缺失或加载异常。
- 当前正则沿用原配置，仅匹配 `functionId` 紧随问号的 URL；不覆盖参数位于其他位置或 POST 正文中的请求。
- HTTPDNS 入口及 IP 沿用提供内容，未核验完整性；阻断后不保证回落系统 DNS，阻断 UDP 也不保证一定能解密 HTTPS。
- 未承诺去除「我的」推荐区、消息 AI 推荐或底部「逛」。效果需要实机验证；出现页面异常时先停用模块。

## 签到模块

| 名称 | 功能 | 默认设置 | 链接 |
| --- | --- | --- | --- |
| PingMe签到©️ | 定时执行 PingMe 签到，并支持抓取签到参数。 | 每 4 小时执行一次；代理策略为「美国节点」；抓取签到参数开启。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/pingme.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/pingme.yaml) |

在模块设置中，将「代理策略」填写为主配置中实际存在的策略组名称，名称需要完全一致。签到时间可通过 Cron 表达式调整，默认是 `0 */4 * * *`。

启用抓取后，模块匹配 `api.pingmeapp.net/app/queryBalanceAndBonus` 请求。关闭抓取开关后的行为由上游脚本实现；模块设置说明为每次运行随机生成设备 ID。是否签到成功应以任务日志和账户实际结果为准。

## 链接跳转模块

| 名称 | 功能 | 可选客户端 | 链接 |
| --- | --- | --- | --- |
| Telegram跳转©️ | 将经过 Egern HTTP 请求处理的 `t.me`、`telegram.me` 链接转换为所选客户端的深链接。 | Telegram、Nagram、Swiftgram、Turrit、iMe、Nicegram、Lingogram；默认 Nagram。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/telegram-redirect.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/telegram-redirect.yaml) |

脚本包含公开用户名、帖子、邀请入群、贴纸、表情、主题、语言、分享及代理链接的转换逻辑。实际支持情况取决于所安装客户端。

**适用边界：** 如果 iOS 或来源 App 在发起网页请求前直接唤起 Telegram，模块就没有可拦截的 HTTP 请求，无法强制改为第三方客户端。直接的 `tg://` 链接也不在此模块匹配范围内。因此本模块不保证所有 Telegram 链接都进入所选客户端。

## 安装与使用

1. **规则集：** 在 Egern 中添加远程规则集，复制对应「订阅」地址，并指定 DIRECT 或所需代理策略。
2. **模块：** 添加远程模块，复制对应「安装」地址，启用后检查模块内的参数设置。
3. **HTTPS 处理：** 网页和 App 的 HTTPS 改写需要相关主机进入 MITM 范围，并安装、信任 Egern 证书。签到的定时任务与参数抓取是不同环节。
4. **更新：** 更新远程模块或规则集后，再检查实际配置及日志；配套脚本由模块自动引用，无需逐个安装。

仓库内容删除不会自动卸载手机中的已安装模块；需在 Egern 中手动删除。此前的京东脚本版已移除；当前目录中的京东模块为另行提供的纯规则增强版。

## 定时更新与同步状态

以下任务均配置为 **每 6 小时检查一次**，也支持从 GitHub Actions 手动运行。实际执行时间以 GitHub Actions 记录为准。

| 内容 | 同步方式 | 运行状态 |
| --- | --- | --- |
| 苹果服务规则 | 同步 AppleService 上游，排除 iCloud 并补充自定义项。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-apple-service-proxy.yml) |
| 直连规则集 | 下载多个上游并合并、去重，加入自定义基础服务规则。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-custom-direct.yml) |
| Ai&US规则集 | 合并可莉 AI、DDGKSF AI、Google Voice 及自定义规则，按规则文本去重。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-ai.yml) |
| PingMe签到 | 同步上游模块，保留本仓库的标题、简介和默认参数定制。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-pingme.yml) |
| 小羞片网站去广告 | 检查 CMS 插件、CMS 脚本与 Pornhub 脚本，合并规则并记录同步状态。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-cms-adblock.yml) |
| 小红书去直播广告、Telegram跳转、京东增强版 | 手动维护；京东增强版来自用户提供配置，未配置上游自动同步任务。 | [提交记录](https://github.com/huangkouping/egern/commits/main/) |

### 如何判断更新与同步

- **模块更新时间：** 查看 YAML 的介绍；自编模块显示更新时间，同步模块还显示同步状态。
- **规则集更新时间：** 查看 `.list` 文件顶部的「规则内容更新时间」。
- **最近是否执行成功：** 点击上表「查看任务」，检查最近一次运行及失败步骤。文件里已有的“同步正常”不代表之后每次定时任务都成功。
- **准确的文件修改时间：** 查看 GitHub 对应文件的提交记录。介绍中的时间是文件写入的文本，不会随浏览设备自动转换时区；GitHub 提交时间与 Actions 记录可用于核对。
- **上游失败：** PingMe、CMS 和 Pornhub 同步逻辑包含沿用现有版本的处理；规则集生成失败时也应以 Actions 日志判断，不要只看文件是否仍能下载。

仓库同步和手机更新是两个步骤：仓库生成了新文件后，Egern 还需要拉取远程配置及相关脚本。脚本的更新间隔通常配置为 3600 秒，模块和规则集的订阅拉取间隔以客户端设置为准。

## 上游来源

### 规则集

| 目标 | 上游 |
| --- | --- |
| 苹果服务规则 | [Bwy999 / AppleService.list](https://raw.githubusercontent.com/Bwy999/Surge/master/Ruleset/AppleService.list) |
| Ai&US规则集 | [可莉 AI.lsr](https://kelee.one/Tool/Loon/Lsr/AI.lsr)、[DDGKSF Ai.yaml](https://ddgksf2013.top/filter/Ai.yaml)、[blackmatrix7 GoogleVoice.list](https://github.com/blackmatrix7/ios_rule_script/raw/master/rule/Loon/GoogleVoice/GoogleVoice.list) |
| 直连 · 微信 | [blackmatrix7 WeChat.list](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/WeChat/WeChat.list) |
| 直连 · 抖音 | [fmz200 Douyin.list](https://raw.githubusercontent.com/fmz200/wool_scripts/main/Loon/rule/Douyin.list)、[takoyakiwhite douyin_pcdn.list](https://raw.githubusercontent.com/takoyakiwhite/asoul_mirror/main/douyin_pcdn.list) |
| 直连 · 小红书 | [blackmatrix7 XiaoHongShu.list](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/XiaoHongShu/XiaoHongShu.list) |
| 直连 · Apple | [ApplePush.list](https://raw.githubusercontent.com/Bwy999/Surge/master/Ruleset/ApplePush.list)、[AppStore.list](https://raw.githubusercontent.com/Bwy999/Surge/master/Ruleset/AppStore.list)、[AppleDirect.list](https://raw.githubusercontent.com/Bwy999/Surge/master/Ruleset/AppleDirect.list) |

### 模块与脚本

| 目标 | 上游 |
| --- | --- |
| PingMe签到 | [mickeu / pingme.yaml](https://raw.githubusercontent.com/mickeu/Egern/main/pingme.yaml)、[PingMeSignin.js](https://raw.githubusercontent.com/mickeu/Egern/main/PingMeSignin.js)、[pingme_capture.js](https://raw.githubusercontent.com/mickeu/Egern/main/pingme_capture.js) |
| CMS 视频过滤 | [Yswag / cmsAdblock.plugin](https://raw.githubusercontent.com/Yswag/for-own-use/main/loon-plugin/cmsAdblock.plugin)、[cmsAdblock.js](https://raw.githubusercontent.com/Yswag/for-own-use/main/js/cmsAdblock.js) |
| Pornhub 网页过滤 | [ddgksf2013 / pornhub.ads.js](https://ddgksf2013.top/scripts/pornhub.ads.js) |

感谢上述上游作者。同步、适配与本仓库的定制逻辑见下方配套文件；第三方内容的授权以其原仓库说明为准。

## 配套文件

这些文件由模块引用或由 GitHub Actions 使用，通常不需要在手机中单独安装。

| 文件 | 用途 |
| --- | --- |
| [xiaohongshu-homefeed-adblock.js](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.js) | 小红书接口过滤脚本。 |
| [attract-adblock.js](https://github.com/huangkouping/egern/blob/main/attract-adblock.js) | 指定网站的网页广告清理脚本。 |
| [cms-adblock.js](https://github.com/huangkouping/egern/blob/main/cms-adblock.js) | 从 CMS 上游同步适配的视频过滤脚本。 |
| [pornhub-adblock.js](https://github.com/huangkouping/egern/blob/main/pornhub-adblock.js) | 同步保存的 Pornhub 网页过滤脚本。 |
| [telegram-redirect.js](https://github.com/huangkouping/egern/blob/main/telegram-redirect.js) | Telegram 链接解析与客户端深链接转换。 |
| [cms-adblock-source.json](https://github.com/huangkouping/egern/blob/main/cms-adblock-source.json) | CMS 上游地址、摘要和匹配主机等同步元数据。 |
| [pornhub-adblock-source.json](https://github.com/huangkouping/egern/blob/main/pornhub-adblock-source.json) | Pornhub 上游地址、脚本摘要及同步状态。 |
| [scripts/sync-ai.py](https://github.com/huangkouping/egern/blob/main/scripts/sync-ai.py) | 生成 Ai&US 规则集。 |
| [scripts/sync-apple-service-proxy.py](https://github.com/huangkouping/egern/blob/main/scripts/sync-apple-service-proxy.py) | 生成苹果服务规则。 |
| [scripts/merge-direct-rules.py](https://github.com/huangkouping/egern/blob/main/scripts/merge-direct-rules.py) | 生成直连规则集。 |
| [scripts/sync-cms-adblock.py](https://github.com/huangkouping/egern/blob/main/scripts/sync-cms-adblock.py) | 同步 CMS 插件、适配脚本并更新模块。 |
| [scripts/sync-pornhub-adblock.py](https://github.com/huangkouping/egern/blob/main/scripts/sync-pornhub-adblock.py) | 检查 Pornhub 脚本并合并过滤配置。 |
| [.github/workflows/](https://github.com/huangkouping/egern/blob/main/.github/workflows) | 定时同步任务配置。 |

自动生成的规则集应修改对应生成脚本；同步模块应修改同步流程中的定制逻辑，避免下一次同步覆盖手工修改。自编模块可直接维护 YAML 与配套 JavaScript。
