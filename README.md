# Egern 规则与模块🅗

本仓库收录 Egern 分流规则、去广告模块、自动签到和链接跳转模块。提供分流规则、DNS 规则、去广告及功能模块，并配有上游同步和更新检查任务。

模块保留维护来源标识：可莉改版使用 **🅥**，自行维护使用 **🅗**。**标识不是版权或原创性证明**；原创与非原创的判定及署名见下方「作者与原创声明」。下方模块索引中的名称与 Egern 安装后显示的 `name` 保持一致；下面的「订阅」和「安装」链接均为 Raw 文件地址，可复制到 Egern 中使用；「源码」用于查看配置。

## 作者与原创声明

- **仓库维护者：** [huangkouping](https://github.com/huangkouping)；**项目主页：** https://github.com/huangkouping/egern
- **🅗 自主维护：** 包括本人原创、独立编写，以及基于他人开源规则进行转换、整合、增强的作品。**🅗 不等于全部原创**；涉及上游代码或规则的，属于**非原创 / 二次开发**，应同时署名原作者与 huangkouping。
- **🅥 上游改编：** 基于可莉（Kelee）版本转换、适配或同步的模块，统一标注**非原创 / 二次开发**；可莉若引用其他原始项目，仍以真实原作者和源项目为准，huangkouping 为适配与维护者。
- **原创判定原则：** 只有代码、规则确由本人独立创作、且未直接改编他人作品时才标记**原创**；其他一律如实标注**非原创 / 二次开发**。具体作者请以对应模块的 `author` 字段及上游来源说明为准，不因维护、转换或同步而改变原作归属。
- **署名格式：** 原创作品：`huangkouping`；非原创作品：`原作者, huangkouping`。模块 `homepage` 统一指向本仓库，原始来源另行保留。

## 模块说明统一规范

所有 Egern 模块说明均采用「功能简介 → 同步状态及必要补充 → 更新时间」的顺序，**更新时间必须在说明最后一行**，格式为 `YYYY-MM-DD HH:mm`（精确到分钟，采用仓库维护时区）。上游自动同步脚本生成模块时也必须遵守此规范；更新时间应为实际文件更新或同步时间，不得仅在未发生更新时伪造更新时间。模块标识统一使用 🅗（自行维护）或 🅥（可莉改版）。

## 目录

- [作者与原创声明](#作者与原创声明)
- [模块安装索引](#模块安装索引)
- [规则集](#规则集)
- [去广告模块](#去广告模块)
- [签到模块](#签到模块)
- [链接跳转模块](#链接跳转模块)
- [安装与使用](#安装与使用)
- [自动化维护与配套任务（无需安装）](#自动化维护与配套任务无需安装)
- [定时更新与同步状态](#定时更新与同步状态)
- [上游来源](#上游来源)
- [配套文件](#配套文件)


## 模块安装索引

**先选模块，再点击「安装」；以下均为可安装的 Egern 模块。** 自主维护 🅗 排在前，改编模块 🅥 排在后；自动化同步、检查任务在页面最下方，**无需安装**。

### 签到模块

| 名称 | 功能 | 默认设置 | 链接 |
| --- | --- | --- | --- |
| PingMe签到🅗 | 定时执行 PingMe 签到，并支持抓取签到参数。 | 每 4 小时执行一次；代理策略为「美国节点」；抓取签到参数开启。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/pingme.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/pingme.yaml) |

在模块设置中，将「代理策略」填写为主配置中实际存在的策略组名称，名称需要完全一致。签到时间可通过 Cron 表达式调整，默认是 `0 */4 * * *`。

启用抓取后，模块匹配 `api.pingmeapp.net/app/queryBalanceAndBonus` 请求。关闭抓取开关后的行为由上游脚本实现；模块设置说明为每次运行随机生成设备 ID。是否签到成功应以任务日志和账户实际结果为准。

## 链接跳转模块

| 名称 | 功能 | 可选客户端 | 链接 |
| --- | --- | --- | --- |
| Telegram跳转🅗 | 将经过 Egern HTTP 请求处理的 `t.me`、`telegram.me` 链接转换为所选客户端的深链接。 | Telegram、Nagram、Swiftgram、Turrit、iMe、Nicegram、Lingogram；默认 Nagram。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/telegram-redirect.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/telegram-redirect.yaml) |

脚本包含公开用户名、帖子、邀请入群、贴纸、表情、主题、语言、分享及代理链接的转换逻辑。实际支持情况取决于所安装客户端。

**适用边界：** 如果 iOS 或来源 App 在发起网页请求前直接唤起 Telegram，模块就没有可拦截的 HTTP 请求，无法强制改为第三方客户端。直接的 `tg://` 链接也不在此模块匹配范围内。因此本模块不保证所有 Telegram 链接都进入所选客户端。

## 安装与使用

1. **规则集：** 在 Egern 中添加远程规则集，复制对应「订阅」地址，并指定 DIRECT 或所需代理策略。
2. **模块：** 添加远程模块，复制对应「安装」地址，启用后检查模块内的参数设置。
3. **HTTPS 处理：** 网页和 App 的 HTTPS 改写需要相关主机进入 MITM 范围，并安装、信任 Egern 证书。签到的定时任务与参数抓取是不同环节。
4. **更新：** 更新远程模块或规则集后，再检查实际配置及日志；配套脚本由模块自动引用，无需逐个安装。

仓库内容删除不会自动卸载手机中的已安装模块；需在 Egern 中手动删除。

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
| 555 电影网网页过滤 | [可莉 / luestr userscript](https://raw.githubusercontent.com/luestr/userscripts/main/adblock/555Movie_adblock.user.js)（v1.2.0 快照，MIT） |
| Pornhub 网页过滤 | [ddgksf2013 / pornhub.ads.js](https://ddgksf2013.top/scripts/pornhub.ads.js) |

感谢上述上游作者。同步、适配与本仓库的定制逻辑见下方配套文件；第三方内容的授权以其原仓库说明为准。

## 配套文件

这些文件由模块引用或由 GitHub Actions 使用，通常不需要在手机中单独安装。

| 文件 | 用途 |
| --- | --- |
| [xiaohongshu-homefeed-adblock.js](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.js) | 小红书接口过滤脚本。 |
| [xiaohongshu-watermark.js](https://github.com/huangkouping/egern/blob/main/xiaohongshu-watermark.js) | 两个小红书模块共用的媒体保存与去水印脚本。 |
| [movie555-adblock.js](https://github.com/huangkouping/egern/blob/main/movie555-adblock.js) | 555 电影网 userscript 的 Egern HTML 注入适配，内含源脚本及 MIT 授权。 |
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

---

## 自动化维护与配套任务（无需安装）

**以下内容不是 Egern 模块安装列表。** GitHub Actions、Muse 检查和同步脚本用于维护仓库文件；普通使用者只需在前面的模块表格点击「安装」，无需运行这些任务。

### 自动化任务速查

| 任务 | 执行方式 | 管理入口 |
| --- | --- | --- |
| 美团、淘宝 | GitHub 每 6 小时拉取、转换、校验、提交 | [同步工作流](https://github.com/huangkouping/egern/actions/workflows/validate-muse-migration.yml) |
| luestr 脚本变更 | GitHub 检查上游，按工作流逻辑通知，不直接覆盖模块 | [检查工作流](https://github.com/huangkouping/egern/actions/workflows/check-luestr-updates.yml) |
| 京东比价、大麦 | Muse 检查上游变化并通知，不自动覆盖仓库 | [相关模块](https://github.com/huangkouping/egern/blob/main/jd-price.yaml) |
| 其他自动同步 | GitHub Actions 独立任务 | [全部工作流](https://github.com/huangkouping/egern/actions) |

**维护提示：** 自动同步文件应修改对应 `scripts/` 下的转换脚本，避免直接修改生成文件后被覆盖。GitHub Actions 的成功表示流程执行完成，实际过滤效果仍需在 Egern 中验证。

## 定时更新与同步状态

以下为主要维护任务。不同工作流的执行周期以各自配置为准；GitHub Actions 实际执行时间以运行记录为准。

| 内容 | 同步方式 | 运行状态 |
| --- | --- | --- |
| 苹果服务规则 | 同步 AppleService 上游，排除 iCloud 并补充自定义项。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-apple-service-proxy.yml) |
| 直连规则集 | 下载多个上游并合并、去重，加入自定义基础服务规则。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-custom-direct.yml) |
| Ai&US规则集 | 合并可莉 AI、DDGKSF AI、Google Voice 及自定义规则，按规则文本去重。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-ai.yml) |
| PingMe签到 | 同步上游模块，保留本仓库的标题、简介和默认参数定制。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-pingme.yml) |
| 小羞片网站去广告 | 检查 CMS 插件、CMS 脚本与 Pornhub 脚本，合并规则并记录同步状态。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-cms-adblock.yml) |
| 美团、淘宝 | GitHub 每 6 小时自动拉取美团、淘宝上游、转换、校验并提交。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/validate-muse-migration.yml) |
| 京东去广告🅗 | 每 6 小时检查上游 v2 脚本并保留本地适配。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-jd-adblock.yml) |
| luestr 脚本检查 | GitHub 检查上游更新；不自动覆盖模块。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/check-luestr-updates.yml) |
| 京东比价、大麦 | Muse 检查上游变化并通知，不自动改动仓库。 | [京东比价](https://github.com/huangkouping/egern/blob/main/jd-price.yaml) · [大麦](https://github.com/huangkouping/egern/blob/main/damai-adblock.yaml) |
| 小红书去直播广告（原版与增强版）、Telegram跳转、京东去开屏广告 | 手动维护，未配置上游自动同步任务。 | [提交记录](https://github.com/huangkouping/egern/commits/main/) |

### 如何判断更新与同步

- **模块更新时间：** 查看 YAML 的介绍；自编模块显示更新时间，同步模块还显示同步状态。
- **规则集更新时间：** 查看 `.list` 文件顶部的「规则内容更新时间」。
- **最近是否执行成功：** 点击上表「查看任务」，检查最近一次运行及失败步骤。文件里已有的“同步正常”不代表之后每次定时任务都成功。
- **准确的文件修改时间：** 查看 GitHub 对应文件的提交记录。介绍中的时间是文件写入的文本，不会随浏览设备自动转换时区；GitHub 提交时间与 Actions 记录可用于核对。
- **上游失败：** PingMe、CMS 和 Pornhub 同步逻辑包含沿用现有版本的处理；规则集生成失败时也应以 Actions 日志判断，不要只看文件是否仍能下载。

仓库同步和手机更新是两个步骤：仓库生成了新文件后，Egern 还需要拉取远程配置及相关脚本。脚本的更新间隔通常配置为 3600 秒，模块和规则集的订阅拉取间隔以客户端设置为准。
