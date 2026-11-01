/* DualSubs / VirgilClyne 公开镜像的 Egern 原生适配，保留字幕与歌词处理逻辑。 */
export default async function(ctx) {
const kind=SCRIPT_KIND, isRequest=kind==="request";
const binary=new URL(ctx.request.url).hostname==="youtubei.googleapis.com";
const head=h=>{
 const out={};
 if(typeof h?.entries==="function")for(const [k,v] of h.entries())out[k]=v;
 else if(h)for(const k of Object.keys(h))out[k]=h[k];
 for(const key of ["content-type","user-agent","accept","accept-language","authorization","content-encoding"]) {
  const value=h?.get?.(key)??h?.[key];if(value!=null)out[key]=value;
 }
 return out;
};
let requestBody,responseBody;
try {
 if(ctx.request.body)requestBody=binary?new Uint8Array(await ctx.request.arrayBuffer()):await ctx.request.text();
 if(!isRequest)responseBody=binary?new Uint8Array(await ctx.response.arrayBuffer()):await ctx.response.text();
 const $request={url:ctx.request.url,method:ctx.request.method||"GET",headers:head(ctx.request.headers),body:requestBody};
 const $response={status:ctx.response?.status||200,headers:head(ctx.response?.headers),body:responseBody};
 const $argument={Type:ctx.env?.Type||"Official",AutoCC:ctx.env?.AutoCC??"true",ShowOnly:ctx.env?.ShowOnly??"true",Position:ctx.env?.Position||"Forward"};
 const $persistentStore={
  read:key=>{
    const raw=ctx.storage?.get(key)??null;
    if(key!=="DualSubs")return raw;
    let profile={};try{profile=JSON.parse(raw||"{}");}catch(_){}
    for(const name of ["YouTube","Composite","Translate"]){
      profile[name]={...(profile[name]||{}),Settings:{...(profile[name]?.Settings||{}),...$argument}};
    }
    return JSON.stringify(profile);
  },
  write:(value,key)=>{ctx.storage?.set(key,String(value));return true;},
  remove:key=>{ctx.storage?.delete(key);return true;},
  clear:()=>false
 };
 // Universal composition/translation must receive the same controls as the player hooks.
 const Egern={},$environment={},$script={startTime:Date.now()/1000};
 let Database,body,sentences;
 const $httpClient={};
 for(const method of ["get","post","put","delete","head","patch","options"]){
  $httpClient[method]=(options,callback)=>{
   const opts=typeof options==="string"?{url:options}:options;
   const timeout=Number(opts.timeout||20); // Egern branch uses seconds.
   ctx.http[method](opts.url,{headers:opts.headers,body:opts.body??opts.bodyBytes,timeout:timeout*1000,
     ...(opts.policy?{policy:opts.policy}:{})})
    .then(async response=>{
      const body=opts["binary-mode"]?new Uint8Array(await response.arrayBuffer()):await response.text();
      callback(null,{status:response.status,statusCode:response.status,headers:head(response.headers)},body);
    },error=>callback(String(error),null,null)).catch(error=>callback(String(error),null,null));
  };
 }
 let complete,finished=false;
 const completion=new Promise(resolve=>{complete=resolve;});
 const $done=value=>{if(!finished){finished=true;complete(value);}};
 SOURCE_CODE
 const result=await completion;
 const normalize=obj=>{
  const out={};
  if(obj?.url)out.url=obj.url;
  if(obj?.method)out.method=obj.method;
  if(obj?.headers)out.headers=obj.headers;
  if(obj?.status)out.status=typeof obj.status==="number"?obj.status:Number(String(obj.status).match(/\b\d{3}\b/)?.[0]||200);
  const body=obj?.body??obj?.bodyBytes;
  if(typeof body==="string"||body instanceof Uint8Array)out.body=body;
  else if(body instanceof ArrayBuffer)out.body=new Uint8Array(body);
  return out;
 };
 if(isRequest){
  if(result?.response)return ctx.respond({status:200,...normalize(result.response)});
  const out=normalize(result);if(requestBody!==undefined&&!Object.hasOwn(out,"body"))out.body=requestBody;
  return out;
 }
 const out=normalize(result);
 return Object.hasOwn(out,"body")?out:{body:responseBody};
} catch (_) {
 return isRequest?(requestBody===undefined?undefined:{body:requestBody}):responseBody===undefined?undefined:{body:responseBody};
}
}
