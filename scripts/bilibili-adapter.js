/* kokoryh / 可莉公开镜像的 Egern 原生适配，保留源逻辑及参数。 */
export default async function(ctx) {
const kind = SCRIPT_KIND;
const truth=(key,def)=>!["false","0","off","no"].includes(String(ctx.env?.[key]??def).toLowerCase());
const requestUrl=String(ctx.request?.url||"");
if(kind==="request"){
 if(requestUrl.endsWith("/DmSegMobile")&&!truth("sponsorBlock","false"))return;
 if(!requestUrl.endsWith("/DmSegMobile")&&!truth("optimizeRequest","true"))return;
}
let requestBody,responseBody;
const headers = h => {
 const result={};
 if(typeof h?.entries==="function")for(const [k,v] of h.entries())result[k.toLowerCase()]=v;
 else if(h)for(const k of Object.keys(h))result[k.toLowerCase()]=h[k];
 for(const k of ["user-agent","content-type","grpc-encoding","grpc-status","x-bili-moss-engine-type"]) {
   const v=h?.get?.(k)??h?.[k];if(v!=null)result[k]=v;
 }
 return result;
};
try {
 const binary=kind!=="json";
 requestBody=kind==="request"&&ctx.request?.body ? new Uint8Array(await ctx.request.arrayBuffer()) : new Uint8Array();
 responseBody=kind==="request"?new Uint8Array():binary?new Uint8Array(await ctx.response.arrayBuffer()):await ctx.response.text();
 const $request={method:ctx.request.method||"POST",url:requestUrl,headers:headers(ctx.request.headers),body:requestBody};
 const $response={status:ctx.response?.status||200,headers:headers(ctx.response?.headers),body:responseBody};
 const $argument=JSON.stringify({displayUpList:ctx.env?.displayUpList||"show",purifyComment:truth("purifyComment","true"),sponsorBlock:truth("sponsorBlock","false"),logLevel:ctx.env?.logLevel||"off"});
 const $environment={};
 const $persistentStore={read:k=>ctx.storage?.get(k)??null,write:(v,k)=>{ctx.storage?.set(k,v);return true;}};
 let result;
 function $done(value){result=value;}
 SOURCE_CODE
 if(result?.abort)return ctx.abort();
 const normalize = obj => {
   const out={};
   if(obj?.status)out.status=typeof obj.status==="number"?obj.status:Number(String(obj.status).match(/\b\d{3}\b/)?.[0]||200);
   if(obj?.headers)out.headers={...obj.headers,...(obj.h2_trailers||{})};
   if(typeof obj?.body==="string"||obj?.body instanceof Uint8Array)out.body=obj.body;
   return out;
 };
 if(kind==="request"){
   if(result?.response)return ctx.respond(normalize(result.response));
   return {body:requestBody};
 }
 const out=normalize(result);
 return Object.hasOwn(out,"body")?out:{body:responseBody};
} catch (_) {
 return kind==="request"?(requestBody?{body:requestBody}:undefined):responseBody===undefined?undefined:{body:responseBody};
}
}
