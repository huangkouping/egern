/* RuCu6 / 可莉公开镜像备份；源逻辑保持，补充异常透传与单次完成。
 * Source: https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/AliYunDrive_remove_ads/kelee_AliYunDrive_remove_ads.js
 */
(function (complete) {
let finished = false;
const $done = value => { if (!finished) { finished = true; complete(value); } };
try {
if (typeof $response === "undefined" || typeof $response.body !== "string") return $done({});
/*
引用地址 https://raw.githubusercontent.com/RuCu6/QuanX/main/Scripts/adrive.js
*/
// 2024-07-15 22:28:47

const url = $request.url;
if (!$response.body) $done({});
let obj = JSON.parse($response.body);

if (url.includes("/v1/users/onboard_list")) {
  if (obj.result?.length > 0) {
    obj.result = obj.result.filter(
      (i) =>
        ![
          "backup_list_under_mydevice_banner",
          "backup_top_banner",
          "home_bulletin_board",
          "home_top_banner",
          "resource_top_banner",
          "video_top_banner"
        ]?.includes(i?.anchor)
    );
  }
} else if (url.includes("/v2/users/home/news")) {
  if (obj.result?.length > 0) {
    obj.result = obj.result.filter((i) => !i?.code?.includes("productUpdate"));
  }
} else if (url.includes("/v1/user/home/widgets") || url.includes("/v2/users/home/widgets")) {
  const item = [
    // "album", // 相册
    "banners", // 顶部奖励
    // "coreFeatures", // 横版图标
    "introduceAlipan", // 认识阿里云盘
    "mainBackup", // 手机备份
    "minorBackup", // 备份设备列表
    // "signIn" // 签到
  ];
  item.forEach((i) => {
    delete obj[i];
  });
}

$done({ body: JSON.stringify(obj) });
} catch (_) { $done({}); }
})($done);
