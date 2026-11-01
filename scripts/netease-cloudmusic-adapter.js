/* 网易云音乐去广告：Keywos 源脚本 wyres.js（致谢 RuCu6、kokoryh）的 Egern 原生适配。
 * Source: SOURCE_URL
 * 保留源脚本全部处理逻辑；仅适配 Egern 二进制响应、压缩和参数接口。
 */
export default async function(ctx) {
  let original;
  try {
    if (!ctx.request || !ctx.response) return;
    if (!/^https?:\/\/interface\d?\.music\.163\.com\/eapi\//i.test(ctx.request.url)) return;
    original = new Uint8Array(await ctx.response.arrayBuffer());
    const headers = {"x-aeapi": ctx.request.headers?.get?.("x-aeapi") ?? ctx.request.headers?.["x-aeapi"]};
    const $request = {url:ctx.request.url,headers};
    const $response = {body:original};
    const keys = ["MY","DT","FX","PRGG","PRRK","PRDRD","PRSCVPT","PRST","PRRR","HMPR","PRMST","PRCN"];
    const settings = Object.fromEntries(keys.map(k=>[k, /^(true|1)$/i.test(String(ctx.env?.[k] ?? "false"))]));
    const $argument = JSON.stringify(settings);
    let result;
    function $done(value) { result = value; }
    SOURCE_CODE
    return result?.body instanceof Uint8Array ? {body:result.body} : {body:original};
  } catch (_) {
    return original ? {body:original} : undefined;
  }
}
