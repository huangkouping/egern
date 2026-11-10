// Regression tests for the published Caiyun JS (also run after each sync).
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const script = fs.readFileSync('colorfulclouds-adblock.js', 'utf8');
function run(url, body) {
  let calls = [];
  const ctx = {$request:{url},$response:{body:JSON.stringify(body)},$done:x=>calls.push(x)};
  vm.runInNewContext(script,ctx,{timeout:1000});
  assert.strictEqual(calls.length,1,'must call $done exactly once');
  assert(calls[0].body,'response must be returned');
  return JSON.parse(calls[0].body);
}
const a03 = run('https://wrapper.cyapi.cn/v1/activity?type_id=A03',{status:'ok',activities:[{name:'aichat',feature:true}]});
assert.strictEqual(a03.activities[0].name,'aichat');
assert.strictEqual(a03.activities[0].feature,false);
const a08 = run('https://wrapper.cyapi.cn/v1/activity?type_id=A08',{status:'ok',activities:[{name:'promotion'}]});
assert.strictEqual(a08.activities.length,0);
const regular = run('https://wrapper.cyapi.cn/v1/activity?type_id=A09',{status:'ok',activities:[{name:'weather',feature:true},{name:'operational',feature:true}]});
assert.strictEqual(regular.activities[0].feature,true);
assert.strictEqual(regular.activities[1].feature,false);
const other = run('https://starplucker.cyapi.cn/v3/operation/homefeatures',{data:[{title:'ad'}]});
assert.strictEqual(other.data.length,0);
console.log('Caiyun JS runtime checks passed');
