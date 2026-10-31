/* 网易云音乐去广告：RuCu6 / Keywos 公开镜像的 Egern 原生适配。
 * Source: SOURCE_URL
 * 排除会员等级显示修改；只处理模块匹配的广告与界面响应。
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
