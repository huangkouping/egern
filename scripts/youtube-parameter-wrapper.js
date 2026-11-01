/* 中文参数界面适配层；下方原作者脚本主体保持原样，由同步任务更新。 */
(function (initialArgument, env, nativeGlobal) {
  const spec = UI_SPEC;
  let base = {};
  if (initialArgument && typeof initialArgument === "object") base = {...initialArgument};
  else if (typeof initialArgument === "string" && !initialArgument.includes("{{{")) {
    try { base = JSON.parse(initialArgument); }
    catch (_) {
      for (const part of initialArgument.split("&")) {
        const at = part.indexOf("=");
        if (at < 0) continue;
        try {
          const key=decodeURIComponent(part.slice(0,at));
          let value=decodeURIComponent(part.slice(at+1).replace(/\+/g," "));
          if (value.startsWith('"') && value.endsWith('"')) value=value.slice(1,-1);
          base[key]=value;
        } catch (_) {}
      }
    }
  }
  if (!base || typeof base !== "object" || Array.isArray(base)) base={};
  base={...spec.defaults,...base};
  for (const [key,item] of Object.entries(spec.fields)) {
    const value=env?.[key];
    if (value===undefined || value===null || value==="") continue;
    if (item.type==="boolean") {
      if (value===true || value==="true") base[key]=true;
      else if (value===false || value==="false") base[key]=false;
    } else if (Object.hasOwn(item.values,String(value))) base[key]=item.values[String(value)];
    else if (Object.values(item.values).includes(value)) base[key]=value;
    else if (item.custom && /^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/.test(String(value))) base[key]=String(value);
  }
  let argument = spec.format==="json" ? JSON.stringify(base) :
    Object.entries(base).map(([key,value])=>encodeURIComponent(key)+"="+encodeURIComponent(String(value))).join("&");
  const request=nativeGlobal.$request;
  const restorePlayerBody=spec.hook==="request" && Object.hasOwn(spec.fields,"AutoCC") &&
    [false,"false"].includes(base.AutoCC) && /\/youtubei\/v1\/player(?:\?|$)/.test(request?.url||"");
  const previousBody=restorePlayerBody && request?.body instanceof Uint8Array ? request.body.slice() : request?.body;
  const originalDone=nativeGlobal.$done;
  function finish(result) {
    // Original player request hooks force caption bits even with AutoCC=false.
    // Keep the app's original body when that specific setting is off; other results and headers survive.
    if (restorePlayerBody && previousBody!==undefined && !result?.response) {
      result={...(result||{})};
      if(Object.hasOwn(result,"bodyBytes"))result.bodyBytes=previousBody;else result.body=previousBody;
    }
    return originalDone.call(nativeGlobal,result);
  }
  const proxy=new Proxy(nativeGlobal,{
    get(target,key){return key==="$argument"?argument:key==="$done"?finish:Reflect.get(target,key,target);},
    set(target,key,value){if(key==="$argument"){argument=value;return true;}return Reflect.set(target,key,value,target);},
    has(target,key){return key==="$argument" || Reflect.has(target,key);}
  });
  (function ($argument, globalThis, $done) {
SOURCE_CODE
  })(argument,proxy,finish);
})(typeof $argument==="undefined"?undefined:$argument,
   typeof ctx==="undefined"?{}:ctx.env||{},globalThis);
