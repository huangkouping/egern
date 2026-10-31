/* PDD pickup: public KeLee mirror + darkings vendored chunk.
 * Main: https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/JavaScript/Kelee/PinDuoDuo_remove_ads/kelee_PinDuoDuo_remove_ads.js
 * Chunk: https://raw.githubusercontent.com/darkings/lat3ncy-proxy-configs/main/loon/vendor/pinduoduo/9410-b8806e870a26db7d.js
 */
(function(complete){let finished=false;const $done=value=>{if(!finished){finished=true;complete(value);}};try{
const url=String($request.url||"");
if(url.split("?")[0]==="https://pfile.pddpic.com/mdkd/mdkd/_next/static/chunks/9410-b8806e870a26db7d.js")return $done({status:200,headers:{"Content-Type":"application/javascript; charset=utf-8","Cache-Control":"no-store"},body:"// 2026-07-11 20:21:39\n(self.webpackChunk_N_E = self.webpackChunk_N_E || []).push([\n  [9410],\n  {\n    82115: function (e, n, t) {\n      \"use strict\";\n      t.d(n, {\n        F: function () {\n          return c;\n        },\n      });\n      t(80545);\n\n      var r = t(3643),\n        o = t.n(r),\n        c = {\n          success: function (e, n, t) {\n            o().info(e || \"\\u64cd\\u4f5c\\u6210\\u529f\", n || 2, t);\n          },\n          fail: function (e) {\n            o().info(e || \"\\u64cd\\u4f5c\\u6210\\u529f\");\n          },\n        };\n    },\n\n    75637: function (e, n, t) {\n      \"use strict\";\n      t.d(n, {\n        d: function () {\n          return b;\n        },\n      });\n\n      var r = t(14795),\n        o = t(18042),\n        c = t(26508),\n        a = t(41115),\n        i = t.n(a),\n        u = t(45948),\n        s = t(77678),\n        l = t(31182),\n        d = (function () {\n          var e = (0, o.Z)(\n            i().mark(function e(n) {\n              var t;\n              return i().wrap(function (e) {\n                for (;;) {\n                  switch ((e.prev = e.next)) {\n                    case 0:\n                      if (((t = n.number), !l.IP.isHarmonyNativePlatform)) {\n                        e.next = 5;\n                        break;\n                      }\n                      return e.abrupt(\"return\", (0, s.Q6)(\"JSPhone\", \"call\", { number: t }));\n\n                    case 5:\n                      return e.abrupt(\"return\", Promise.reject());\n\n                    case 6:\n                    case \"end\":\n                      return e.stop();\n                  }\n                }\n              }, e);\n            })\n          );\n\n          return function (n) {\n            return e.apply(this, arguments);\n          };\n        })(),\n        p = t(80469),\n        f = t(63992),\n        _ = [\"number\", \"children\", \"onClick\", \"onRiskCheck\"];\n\n      function v(e, n) {\n        var t = Object.keys(e);\n        if (Object.getOwnPropertySymbols) {\n          var o = Object.getOwnPropertySymbols(e);\n          n &&\n            (o = o.filter(function (n) {\n              return Object.getOwnPropertyDescriptor(e, n).enumerable;\n            })),\n            t.push.apply(t, o);\n        }\n        return t;\n      }\n\n      function g(e) {\n        for (var n = 1; n < arguments.length; n++) {\n          var t = null != arguments[n] ? arguments[n] : {};\n          n % 2\n            ? v(Object(t), true).forEach(function (n) {\n                (0, r.Z)(e, n, t[n]);\n              })\n            : Object.getOwnPropertyDescriptors\n            ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t))\n            : v(Object(t)).forEach(function (n) {\n                Object.defineProperty(e, n, Object.getOwnPropertyDescriptor(t, n));\n              });\n        }\n        return e;\n      }\n\n      var b = function (e) {\n        var n = e.number,\n          t = e.children,\n          r = e.onClick,\n          a = e.onRiskCheck,\n          s = (0, c.Z)(e, _),\n          v = (0, u.useCallback)(\n            (0, o.Z)(\n              i().mark(function e() {\n                var t;\n                return i().wrap(function (e) {\n                  for (;;) {\n                    switch ((e.prev = e.next)) {\n                      case 0:\n                        if (!a) {\n                          e.next = 6;\n                          break;\n                        }\n                        return (e.next = 3), a();\n\n                      case 3:\n                        if (e.sent) {\n                          e.next = 6;\n                          break;\n                        }\n                        return e.abrupt(\"return\", false);\n\n                      case 6:\n                        return l.IP.isHarmonyNativePlatform\n                          ? d({ number: n })\n                          : (((t = document.createElement(\"a\")).href = \"tel:\".concat(n)), t.click()),\n                          r && r(),\n                          e.abrupt(\"return\", true);\n\n                      case 9:\n                      case \"end\":\n                        return e.stop();\n                    }\n                  }\n                }, e);\n              })\n            ),\n            [n, r, a]\n          );\n\n        return (0, f.jsx)(p.S, {\n          onAsyncClick: v,\n          children: (0, f.jsx)(\n            \"a\",\n            g(\n              g({}, s),\n              {},\n              {\n                children: t,\n              }\n            )\n          ),\n        });\n      };\n    },\n\n    43435: function (e) {\n      e.exports = {\n        \"goods-list-big-container\": \"index_goods-list-big-container__05Se6\",\n      };\n    },\n\n    70242: function (e) {\n      e.exports = {\n        container: \"index_container__3ARqx\",\n        hidden: \"index_hidden__kbZnj\",\n        countdown: \"index_countdown__V7fdw\",\n        \"gif-container\": \"index_gif-container__lZMA8\",\n        \"container-type1\": \"index_container-type1__lD1cV\",\n        content: \"index_content__58ab9\",\n        \"red-pocket-ic\": \"index_red-pocket-ic__g52HU\",\n        \"type1-text\": \"index_type1-text__Mafrp\",\n        btn: \"index_btn__vPONm\",\n      };\n    },\n  },\n]);\n"});
if(!/^https:\/\/m\.pinduoduo\.net\/mdkd\/package\?from_app_scan/i.test(url)||typeof $response.body!=="string")return $done({});
/*
https://t.me/ibilibili
2026-07-11 20:05:34
*/
let body = $response.body || "";

const oldChunk = "https://pfile.pddpic.com/mdkd/mdkd/_next/static/chunks/9410-b8806e870a26db7d.js";
const newChunk = oldChunk;

function replaceAllText(text, from, to) {
  let pos = text.indexOf(from);
  while (pos !== -1) {
    text = text.slice(0, pos) + to + text.slice(pos + from.length);
    pos = text.indexOf(from, pos + to.length);
  }
  return text;
}

function removeGifContainer(html) {
  const marker = "index_gif-container";
  let pos = html.indexOf(marker);

  while (pos !== -1) {
    const open = html.lastIndexOf("<div", pos);
    if (open === -1) break;

    let i = open;
    let depth = 0;
    let end = -1;

    while (i < html.length) {
      const nextOpen = html.indexOf("<div", i);
      const nextClose = html.indexOf("</div>", i);
      if (nextClose === -1) break;

      if (nextOpen !== -1 && nextOpen < nextClose) {
        depth++;
        i = nextOpen + 4;
      } else {
        depth--;
        i = nextClose + 6;
        if (depth === 0) {
          end = i;
          break;
        }
      }
    }

    if (end === -1) break;

    html = html.slice(0, open) + html.slice(end);
    pos = html.indexOf(marker, open);
  }

  return html;
}

function trimNextData(html) {
  const idNeedle = 'id="__NEXT_DATA__"';
  const idPos = html.indexOf(idNeedle);
  if (idPos === -1) return html;

  const tagStart = html.lastIndexOf("<script", idPos);
  if (tagStart === -1) return html;

  const contentStart = html.indexOf(">", tagStart);
  if (contentStart === -1) return html;

  const tagEnd = html.indexOf("</script>", contentStart);
  if (tagEnd === -1) return html;

  const jsonText = html.slice(contentStart + 1, tagEnd);

  try {
    const data = JSON.parse(jsonText);
    const serverData = data &&
      data.props &&
      data.props.pageProps &&
      data.props.pageProps.serverData;

    if (Array.isArray(serverData)) {
      data.props.pageProps.serverData = serverData.filter(item =>
        item &&
        (item.key === "fastBindCMobilePreCheck" ||
         item.key === "queryStationPackageInfo")
      );
    }

    return html.slice(0, contentStart + 1) +
      JSON.stringify(data) +
      html.slice(tagEnd);
  } catch (e) {
    return html;
  }
}

body = replaceAllText(body, oldChunk, newChunk);
body = removeGifContainer(body);
body = trimNextData(body);

$done({ body });
}catch(_){$done({});}})($done);
