import fs from "node:fs";
import assert from "node:assert/strict";
import zlib from "node:zlib";
const dir=process.env.BILI_DIR||new URL("../",import.meta.url);
const path=name=>typeof dir==="string"?dir+"/"+name:new URL(name,dir);
const load=async kind=>(await import("data:text/javascript;base64,"+Buffer.from(fs.readFileSync(path("bilibili-"+kind+".js"),"utf8")).toString("base64"))).default;
const json=await load("json"),response=await load("response"),request=await load("request");
const map=new Map(),storage={get:k=>map.get(k)??null,set:(k,v)=>map.set(k,v)};
const compress={gunzip:async b=>new Uint8Array(zlib.gunzipSync(b))};
const buffer=b=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
function frame(b,gz=false){const data=gz?zlib.gzipSync(b):b;const out=Buffer.alloc(5+data.length);out[0]=gz?1:0;out.writeUInt32BE(data.length,1);data.copy(out,5);return out;}
let out=await json({request:{method:"GET",url:"https://api.live.bilibili.com/xlive/app-interface/v2/index/feed?x=1",headers:new Headers()},response:{status:200,headers:new Headers(),text:async()=>JSON.stringify({code:0,data:{card_list:[{card_type:"banner_v2"},{card_type:"normal"}]}})},storage});
assert.deepEqual(JSON.parse(out.body).data.card_list,[{card_type:"normal"}]);
const unknown=Buffer.from([0x98,0x06,0x01]);
for(const endpoint of ["bilibili.community.service.dm.v1.DM/DmView","bilibili.main.community.reply.v1.Reply/MainList","bilibili.app.view.v1.View/ViewProgress"])for(const gz of [false,true]){
 let body=unknown;
 if(endpoint.endsWith("/DmView"))body=Buffer.concat([Buffer.from([0x92,0x01,0x02,0x61,0x64]),unknown]); // activity_meta advertisement
 const b=frame(body,gz);
 const r=await response({request:{method:"POST",url:"https://grpc.biliapi.net/"+endpoint,headers:new Headers({"x-bili-moss-engine-type":"1"})},response:{status:200,headers:new Headers({"content-type":"application/grpc"}),arrayBuffer:async()=>buffer(b)},storage,compress,env:{logLevel:"off",sponsorBlock:"false"}});
 assert.equal(r.body[0],0);assert.equal(Buffer.from(r.body).readUInt32BE(1),r.body.length-5);
 assert.equal(r.headers["grpc-status"],"0");assert.deepEqual(Buffer.from(r.body).subarray(5),unknown);
}
let calls=0;const empty=frame(Buffer.alloc(0));
const req={method:"POST",url:"https://grpc.biliapi.net/bilibili.main.community.reply.v1.Reply/MainList",headers:new Headers({"x-bili-moss-engine-type":"1"}),body:{},arrayBuffer:async()=>buffer(empty)};
const http={post:async()=>{calls++;return {status:200,headers:new Headers({"content-type":"application/grpc"}),arrayBuffer:async()=>buffer(empty)}}};
out=await request({request:req,storage,compress,env:{logLevel:"off"},http,respond:r=>({responded:r})});
assert.equal(calls,1);assert.equal(out.responded.status,200);assert.ok(out.responded.body instanceof Uint8Array);
const dmUrl="https://grpc.biliapi.net/bilibili.community.service.dm.v1.DM/DmSegMobile";
assert.equal(await request({request:{...req,url:dmUrl},env:{sponsorBlock:"false"}}),undefined);
assert.equal(await request({request:req,env:{optimizeRequest:"false"}}),undefined);
const dmBody=frame(Buffer.from([0x08,0x01,0x10,0x02,0x18,0x01]));
let sponsorCalls=0;
out=await request({request:{...req,url:dmUrl,arrayBuffer:async()=>buffer(dmBody)},storage,compress,env:{sponsorBlock:"true",logLevel:"off"},
 http:{...http,get:async(url)=>{assert.match(url,/bsbsb\.top\/api\/skipSegments/);sponsorCalls++;return {status:200,headers:new Headers(),text:async()=>JSON.stringify([{actionType:"skip",segment:[10,25]}])}}},
 respond:r=>r});
assert.equal(sponsorCalls,1);assert.ok(out.body.length>5);assert.ok(Buffer.from(out.body).includes(Buffer.from("airborne:25000")));
const bad=Buffer.from([0xff,0,0,0,1,0xff]);
out=await response({request:{method:"POST",url:"https://grpc.biliapi.net/bilibili.community.service.dm.v1.DM/DmView",headers:new Headers()},response:{status:200,headers:new Headers(),arrayBuffer:async()=>buffer(bad)},storage,compress,env:{logLevel:"off"}});
assert.deepEqual(Buffer.from(out.body),bad);
console.log("PASS: live filtering; Protobuf ad removal/unknown fields; gzip framing; gRPC status; redispatch; option gates; SponsorBlock segments; malformed body retention");
