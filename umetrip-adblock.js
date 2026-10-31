/* 佚名 / 可莉公开镜像备份；源逻辑保持，补充异常透传与单次完成。
 * Source: https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/Umetrip_remove_ads/kelee_Umetrip_remove_ads.js
 */
(function (complete) {
let finished = false;
const $done = value => { if (!finished) { finished = true; complete(value); } };
try {
if (typeof $request === "undefined" || !$request.headers) return $done({});
const version = 'V1.0.1';
var ua=$request.headers.rpid||$request.headers.Rpid;ua.includes("1000002")||ua.includes("1000019")?$done({status:"HTTP/1.1 404 Not Found"}):$done({});

} catch (_) { $done({}); }
})($done);
