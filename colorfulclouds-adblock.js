/* RuCu6 / 可莉公开镜像备份；源逻辑保持，补充异常透传与单次完成。
 * Source: https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/ColorfulClouds_remove_ads/kelee_ColorfulClouds_remove_ads.js
 */
(function (complete) {
let finished = false;
const $done = value => { if (!finished) { finished = true; complete(value); } };
try {
if (typeof $response === "undefined" || typeof $response.body !== "string") return $done({});
// 2024-09-05 11:06:15
const url = $request.url;
let obj = JSON.parse($response.body);
if (url.includes("/api.caiyunapp.com/v1/activity")) {
  if (url.includes("&type_id=A03&")) {
    // 底栏控制项目 主页图标 天气助手 彩云ai
    if (obj?.interval) {
      obj.interval = 2592000; // 30天===2592000秒
    }
    if (obj?.activities?.length > 0) {
      for (let item of obj.activities) {
        if (item?.name && item?.type && item?.feature) {
          item.feature = false;
        }
      }
    }
  } else {
    // 其他请求
    obj = { status: "ok", activities: [{ items: [] }] };
  }
} else if (url.includes("/wrapper.cyapi.cn/v1/activity")) {
  // 彩云推广
  if (["&type_id=A03&"]?.includes(url)) {
    // 天气助手 彩云ai
    if (obj?.interval) {
      obj.interval = 2592000; // 30天===2592000秒
    }
    if (obj?.activities?.length > 0) {
      obj.activities = [];
    }
  } else {
    // 其他请求
    obj = { status: "ok", activities: [{ items: [] }] };
  }
}
$done({ body: JSON.stringify(obj) });
} catch (_) { $done({}); }
})($done);
