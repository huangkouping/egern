# Egern 规则与模块🅗

本仓库收录 Egern 分流规则、去广告模块、自动签到和链接跳转模块。提供分流规则、DNS 规则、去广告及功能模块，并配有上游同步和更新检查任务。

模块保留来源标识：可莉改版使用 **🅥**，自行维护使用 **🅗**。下方模块索引中的名称与 Egern 安装后显示的 `name` 保持一致；下面的「订阅」和「安装」链接均为 Raw 文件地址，可复制到 Egern 中使用；「源码」用于查看配置。

## 目录

- [完整文件索引](#完整文件索引按用途)
- [规则集](#规则集)
- [去广告模块](#去广告模块)
- [签到模块](#签到模块)
- [链接跳转模块](#链接跳转模块)
- [安装与使用](#安装与使用)
- [定时更新与同步状态](#定时更新与同步状态)
- [上游来源](#上游来源)
- [配套文件](#配套文件)


## 完整文件索引（按用途）

> 以仓库实际文件为准。🅥 表示可莉改版，🅗 表示自行维护；标识以模块文件内的名称为准。此表不改变模块内容。

### 同步模块（GitHub 每 6 小时）

| 模块名称 | 功能说明 | Egern 安装地址 | 查看源码 |
| --- | --- | --- | --- |
| 搜索去广告&自动翻页🅗 | 过滤搜索结果广告，并提供自动翻页功能。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/baidu-search-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/baidu-search-adblock.yaml) |
| 美团去广告🅗 | 清理美团 App 内匹配的广告及推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/meituan-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/meituan-adblock.yaml) |
| 淘宝去广告🅥 | 过滤淘宝 App 的部分广告与推广入口。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/taobao-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/taobao-adblock.yaml) |

### 辅助与功能模块

| 模块名称 | 功能说明 | Egern 安装地址 | 查看源码 |
| --- | --- | --- | --- |
| PingMe签到🅗 | 定时签到，并支持签到参数抓取与设置。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/pingme.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/pingme.yaml) |
| Telegram跳转🅗 | 将 Telegram 网页链接转换为指定第三方客户端链接。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/telegram-redirect.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/telegram-redirect.yaml) |
| 微信外部链接解锁🅗 | 优化微信内外部链接的打开与跳转限制。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/wechat-external-links.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/wechat-external-links.yaml) |
| 微信小程序去广告🅥 | 过滤已适配微信小程序中的广告请求及展示内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/weixin-mini-programs-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/weixin-mini-programs-adblock.yaml) |

### 广告过滤及其他模块

| 模块名称 | 功能说明 | Egern 安装地址 | 查看源码 |
| --- | --- | --- | --- |
| 广告平台拦截器🅥 | 拦截常见广告平台域名与相关请求。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/ad-platform-blocker.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/ad-platform-blocker.yaml) |
| 阿里云盘去广告🅥 | 过滤阿里云盘中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/aliyundrive-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/aliyundrive-adblock.yaml) |
| 高德地图去广告🅥 | 过滤高德地图中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/amap-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/amap-adblock.yaml) |
| 小羞片网站去广告🅗 | 清理指定网站的网页广告及部分视频播放广告。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/attract-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/attract-adblock.yaml) |
| 百度网盘去广告🅥 | 过滤百度网盘中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/baidu-netdisk-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/baidu-netdisk-adblock.yaml) |
| 百度翻译去广告🅥 | 过滤百度翻译中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/baidu-translate-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/baidu-translate-adblock.yaml) |
| 贝壳找房去广告🅥 | 过滤贝壳找房中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/beike-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/beike-adblock.yaml) |
| 哔哩哔哩去广告🅥 | 过滤哔哩哔哩中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/bilibili-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/bilibili-adblock.yaml) |
| 中国联通去开屏广告🅥 | 过滤中国联通中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/china-unicom-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/china-unicom-adblock.yaml) |
| 彩云天气去广告🅥 | 过滤彩云天气中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/colorfulclouds-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/colorfulclouds-adblock.yaml) |
| 大麦去广告🅥 | 过滤大麦中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/damai-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/damai-adblock.yaml) |
| 得物去广告🅥 | 过滤得物中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/dewu-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/dewu-adblock.yaml) |
| 滴滴去广告🅥 | 过滤滴滴中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/didi-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/didi-adblock.yaml) |
| 叮咚买菜去广告🅥 | 过滤叮咚买菜中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/dingdong-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/dingdong-adblock.yaml) |
| e充电去广告🅥 | 过滤e充电中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/echarge-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/echarge-adblock.yaml) |
| 闲鱼去广告🅥 | 过滤闲鱼中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/goofish-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/goofish-adblock.yaml) |
| 盒马去广告🅥 | 过滤盒马中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/hema-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/hema-adblock.yaml) |
| HTTPDNS拦截器🅥 | 拦截部分 App 内置 HTTPDNS 请求，保留配置中的例外规则。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/httpdns-blocker.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/httpdns-blocker.yaml) |
| 凤凰新闻去广告🅥 | 过滤凤凰新闻中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/ifeng-news-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/ifeng-news-adblock.yaml) |
| 京东去广告🅗 | 过滤京东开屏及部分页面推广内容，兼容新协议。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/jd-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/jd-adblock.yaml) |
| 京东比价🅗 | 查询京东商品历史价格，展示比价信息。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/jd-price.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/jd-price.yaml) |
| Keep去广告🅥 | 过滤Keep中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/keep-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/keep-adblock.yaml) |
| 可莉广告过滤器🅥 | 集中拦截可莉规则覆盖的广告与追踪请求。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/kelee-adfilter.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/kelee-adfilter.yaml) |
| 快手去广告🅥 | 过滤快手中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/kuaishou-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/kuaishou-adblock.yaml) |
| 网易邮箱大师去广告🅥 | 过滤网易邮箱大师中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/mailmaster-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/mailmaster-adblock.yaml) |
| 美图秀秀去广告🅥 | 过滤美图秀秀中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/meitu-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/meitu-adblock.yaml) |
| 芒果TV去广告🅥 | 过滤芒果TV中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/mgtv-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/mgtv-adblock.yaml) |
| 摩天轮去广告🅥 | 过滤摩天轮中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/motianlun-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/motianlun-adblock.yaml) |
| 网易云音乐去广告🅥 | 过滤网易云音乐中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/netease-cloudmusic-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/netease-cloudmusic-adblock.yaml) |
| 网易新闻去广告🅥 | 过滤网易新闻中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/netease-news-kelee.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/netease-news-kelee.yaml) |
| 拼多多去广告🅥 | 过滤拼多多中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/pinduoduo-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/pinduoduo-adblock.yaml) |
| QQ音乐去广告🅥 | 过滤QQ音乐中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/qqmusic-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/qqmusic-adblock.yaml) |
| 12306去广告🅥 | 过滤12306中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/railway12306-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/railway12306-adblock.yaml) |
| 汽水音乐去广告🅥 | 过滤汽水音乐中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/soda-music-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/soda-music-adblock.yaml) |
| 汽水音乐净化·墨鱼版🅗 | 基于墨鱼规则净化汽水音乐相关广告内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/soda-music-ddgksf2013.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/soda-music-ddgksf2013.yaml) |
| 航旅纵横去广告🅥 | 过滤航旅纵横中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/umetrip-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/umetrip-adblock.yaml) |
| 微信公众号去广告🅥 | 过滤微信公众号中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/wechat-article-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/wechat-article-adblock.yaml) |
| 威锋去广告🅥 | 过滤威锋中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/weifeng-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/weifeng-adblock.yaml) |
| 小红书去直播广告🅗 | 过滤小红书开屏、首页推广及直播卡片，可按需开关。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaohongshu-homefeed-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.yaml) |
| 小桔充电去广告🅥 | 过滤小桔充电中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaojukeji-charge-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/xiaojukeji-charge-adblock.yaml) |
| 小米音箱去广告🅥 | 过滤小米音箱中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaomi-speaker-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/xiaomi-speaker-adblock.yaml) |
| 小宇宙去广告🅥 | 过滤小宇宙中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaoyuzhou-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/xiaoyuzhou-adblock.yaml) |
| 喜马拉雅去广告🅥 | 过滤喜马拉雅中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/ximalaya-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/ximalaya-adblock.yaml) |
| 网易有道词典去广告🅥 | 过滤网易有道词典中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/youdao-dict-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/youdao-dict-adblock.yaml) |
| 有道翻译官去广告🅥 | 过滤有道翻译官中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/youdao-trans-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/youdao-trans-adblock.yaml) |
| 优酷视频去广告🅥 | 过滤优酷视频中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/youku-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/youku-adblock.yaml) |
| YouTube去广告🅗 | 过滤 YouTube 广告并提供相关播放增强功能。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/youtube-enhance.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/youtube-enhance.yaml) |
| YouTube双语翻译🅗 | 提供 YouTube 字幕翻译与双语字幕功能。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/youtube-subtitles-translation.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/youtube-subtitles-translation.yaml) |
| 知乎去广告🅥 | 过滤知乎中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/zhihu-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/zhihu-adblock.yaml) |
| 中华万年历去广告🅥 | 过滤中华万年历中匹配的广告或推广内容。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/zhwnl-adblock.yaml) | [源码](https://github.com/huangkouping/egern/blob/main/zhwnl-adblock.yaml) |

### DNS 规则与策略规则

| 文件 | 用途 | 链接 |
| --- | --- | --- |
| `dns-cn.list` | 国内 DNS 规则 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/dns-cn.list) |
| `dns-global.list` | 国外 DNS 规则 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/dns-global.list) |
| `apple-service-proxy.list` | 苹果服务代理规则 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/apple-service-proxy.list) |
| `custom-direct.list` | 自定义直连规则 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/custom-direct.list) |
| `us.list` | AI 与美国服务代理规则 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/us.list) |

### 自动化任务速查

| 任务 | 执行方式 | 管理入口 |
| --- | --- | --- |
| 美团、搜索、淘宝 | GitHub 每 6 小时拉取、转换、校验、提交 | [同步工作流](https://github.com/huangkouping/egern/actions/workflows/validate-muse-migration.yml) |
| luestr 脚本变更 | GitHub 检查上游，按工作流逻辑通知，不直接覆盖模块 | [检查工作流](https://github.com/huangkouping/egern/actions/workflows/check-luestr-updates.yml) |
| 京东比价、大麦 | Muse 检查上游变化并通知，不自动覆盖仓库 | [相关模块](https://github.com/huangkouping/egern/blob/main/jd-price.yaml) |
| 其他自动同步 | GitHub Actions 独立任务 | [全部工作流](https://github.com/huangkouping/egern/actions) |

**维护提示：** 自动同步文件应修改对应 `scripts/` 下的转换脚本，避免直接修改生成文件后被覆盖。GitHub Actions 的成功表示流程执行完成，实际过滤效果仍需在 Egern 中验证。

## 规则集

规则集用于指定流量走哪个策略，不包含完整的节点配置，也不会自动创建策略组。

| 名称 | 用途与范围 | 建议策略 | 链接 |
| --- | --- | --- | --- |
| 苹果服务规则🅗 | Apple News、部分地区受限服务及指定 Apple 服务入口。排除 `icloud.com` 及其子域名，让这部分继续由直连规则处理。 | 苹果服务，或自行选择的代理策略组 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/apple-service-proxy.list) · [源码](https://github.com/huangkouping/egern/blob/main/apple-service-proxy.list) |
| 直连规则集🅗 | 微信、抖音、小红书的正常内容防误杀，以及 Apple 推送、账号、下载、CDN、iCloud 等基础服务直连。 | DIRECT | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/custom-direct.list) · [源码](https://github.com/huangkouping/egern/blob/main/custom-direct.list) |
| Ai&US规则集🅗 | 合并海外 AI 服务、Muse / Meta AI、自定义 AI 补充及 Google Voice 上游规则。包含 ChatGPT、Claude、Gemini、Copilot、Perplexity、Manus、Cue 等相关域名。 | 美国节点，或自己的 US 策略组 | [订阅](https://raw.githubusercontent.com/huangkouping/egern/main/us.list) · [源码](https://github.com/huangkouping/egern/blob/main/us.list) |

### 分流说明

- **苹果服务规则**包含 `itunes.com`、`iphonesubmissions.apple.com`、`kt-prod.ess.apple.com`、`humb.apple.com` 等自定义代理项；并非全部 Apple 流量都走代理。
- **直连规则集**用于恢复正常服务，不能代替完整的国内分流规则集；部分规则覆盖整个域名及子域名。
- **Ai&US规则集**包含上游提供的公共依赖域名，因此部分匹配范围会超过单一 AI 产品；选择美国节点也不等于保证服务账号具备地区资格。
- 多个规则集可能覆盖相同域名，例如 `sentry.io`。请根据实际用途安排优先级，并在 Egern 的连接记录中确认最终命中策略。

## 去广告模块

| 名称 | 功能 | 设置与范围 | 链接 |
| --- | --- | --- | --- |
| 小红书去直播广告🅗 | 过滤开屏、首页「发现」商业广告、直播卡片，以及作者正在直播的普通笔记；支持疑似医美推广过滤。 | 各功能可独立开关；保留未命中过滤条件的普通图文、视频及商品笔记。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/xiaohongshu-homefeed-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.yaml) |
| 小羞片网站去广告🅗 | 合并指定网站的网页广告清理、CMS 视频播放列表插播过滤，以及 Pornhub 网页过滤与广告接口处理。 | 包含自编网页脚本及同步适配的上游脚本；仅处理配置中匹配的网址或播放资源。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/attract-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/attract-adblock.yaml) |
| 京东去广告🅗 | 采用上游 v2 响应脚本清理开屏、首页、我的、订单及物流页广告。 | 保留额外开屏请求拦截及本地异常保护；实际效果取决于 App 版本。 | [安装](https://raw.githubusercontent.com/huangkouping/egern/main/jd-adblock.yaml) · [源码](https://github.com/huangkouping/egern/blob/main/jd-adblock.yaml) |

### 小红书去直播广告🅗

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

### 小羞片网站去广告🅗

**网页部分**覆盖 911 爆料网、黑料网等已收录入口及镜像：

| 类型 | 当前匹配范围 |
| --- | --- |
| 指定入口 | `attract.gaqwvqor.cc`、`ancient.gaqwvqor.cc`、`asleep.gaqwvqor.cc` |
| 域名及可选一层子域名 | `blw66.com`、`911bla.com`、`911aa2.com`、`911bg20.com`、`ckspzdnd.cc`、`fytdugpm.cc`、`91jq508.com`、`lgyggwws.cc`、`pjitqyei.cc`、`hlwf22.com`、`heiliao.com`、`91cg1.com`、`lhrkglii.cc`、`iadapjby.cc`、`qxrguuar.cc`、`lhxgoxlj.cc`、`heiliao88.com` |
| 指定 CloudFront 镜像 | `d9altmxkp5q0i.cloudfront.net`、`d169l2tv32yjx4.cloudfront.net` |
| Pornhub | `cn.pornhub.com`、`www.pornhub.com` |
| 555 电影网 | `555k06.com`、`www.555k06.com` |

**视频部分**同步 CMS 上游的资源匹配规则及脚本，处理符合条件的 M3U8 播放列表。页面是否使用已匹配的播放器资源，会影响过滤效果；新增镜像也需要收录到配置中。

**555 电影网适配：** 使用 [luestr/userscripts 的 555Movie_adblock.user.js](https://github.com/luestr/userscripts/blob/main/adblock/555Movie_adblock.user.js) v1.2.0 快照，保留 MIT 授权并封装为 Egern 原生响应脚本。仅对上述两个域名的 HTML 注入浏览器端逻辑，处理源脚本识别的广告请求、弹窗、图标墙、浮动推广和播放器横幅。不是视频 M3U8 去插播规则，也不扩展到其他站点。

此项为 **2026-10-24 手动适配快照，未加入定时同步**，现有 CMS / Pornhub 同步任务不负责更新它。已完成离线注入和部分浏览器 API 模拟测试，未实站验证；网页 CSP 可能阻止注入，不会为此移除或放宽安全策略。实际效果请以设备测试为准。

### 京东去广告🅗

基于 zbsdsb 的京东去广告 v2 脚本适配 Egern，覆盖开屏、首页、我的、订单及物流页的部分推广内容，并保留启动广告物料接口拦截。上游脚本通过 GitHub Actions 每 6 小时检查更新；更新失败时保留现有脚本。实际过滤效果以 Egern 日志和 App 页面为准。

## 签到模块

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

## 定时更新与同步状态

以下为主要维护任务。不同工作流的执行周期以各自配置为准；GitHub Actions 实际执行时间以运行记录为准。

| 内容 | 同步方式 | 运行状态 |
| --- | --- | --- |
| 苹果服务规则 | 同步 AppleService 上游，排除 iCloud 并补充自定义项。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-apple-service-proxy.yml) |
| 直连规则集 | 下载多个上游并合并、去重，加入自定义基础服务规则。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-custom-direct.yml) |
| Ai&US规则集 | 合并可莉 AI、DDGKSF AI、Google Voice 及自定义规则，按规则文本去重。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/update-ai.yml) |
| PingMe签到 | 同步上游模块，保留本仓库的标题、简介和默认参数定制。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-pingme.yml) |
| 小羞片网站去广告 | 检查 CMS 插件、CMS 脚本与 Pornhub 脚本，合并规则并记录同步状态。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-cms-adblock.yml) |
| 美团、搜索去广告与自动翻页、淘宝 | GitHub 每 6 小时自动拉取上游、转换、校验并提交；2026-11-01 已完成首次正式运行。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/validate-muse-migration.yml) |
| 京东去广告🅗 | 每 6 小时检查上游 v2 脚本并保留本地适配。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/sync-jd-adblock.yml) |
| luestr 脚本检查 | GitHub 检查上游更新；不自动覆盖模块。 | [查看任务](https://github.com/huangkouping/egern/actions/workflows/check-luestr-updates.yml) |
| 京东比价、大麦 | Muse 检查上游变化并通知，不自动改动仓库。 | [京东比价](https://github.com/huangkouping/egern/blob/main/jd-price.yaml) · [大麦](https://github.com/huangkouping/egern/blob/main/damai-adblock.yaml) |
| 小红书去直播广告、Telegram跳转、京东去开屏广告 | 手动维护，未配置上游自动同步任务。 | [提交记录](https://github.com/huangkouping/egern/commits/main/) |

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
| 555 电影网网页过滤 | [可莉 / luestr userscript](https://raw.githubusercontent.com/luestr/userscripts/main/adblock/555Movie_adblock.user.js)（v1.2.0 快照，MIT） |
| Pornhub 网页过滤 | [ddgksf2013 / pornhub.ads.js](https://ddgksf2013.top/scripts/pornhub.ads.js) |

感谢上述上游作者。同步、适配与本仓库的定制逻辑见下方配套文件；第三方内容的授权以其原仓库说明为准。

## 配套文件

这些文件由模块引用或由 GitHub Actions 使用，通常不需要在手机中单独安装。

| 文件 | 用途 |
| --- | --- |
| [xiaohongshu-homefeed-adblock.js](https://github.com/huangkouping/egern/blob/main/xiaohongshu-homefeed-adblock.js) | 小红书接口过滤脚本。 |
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
