/**
 * Egern: t.me / telegram.me → 指定 Telegram 客户端
 * 修复：Nagram 使用独立的 na://，避免被官方 Telegram 的 tg:// 接管。
 */

const SCHEME = {
  Telegram: "tg",
  Nagram: "na",
  Swiftgram: "sg",
  Turrit: "turrit",
  iMe: "ime",
  Nicegram: "ng",
  Lingogram: "lingo",
};

function qval(qs, key) {
  if (!qs) return "";
  const escapedKey = key.replace(/[.*+?^{}$()|[\]\\]/g, "\\$&");
  const re = new RegExp("(?:^|&)" + escapedKey + "=([^&]*)");
  const m = qs.match(re);
  return m ? decodeURIComponent(m[1]) : "";
}

function deeplink(scheme, path, qs) {
  const parts = path.split("/").filter(Boolean);
  if (!parts[0]) return "";

  if (parts[0][0] === "+") {
    return `${scheme}://join?invite=${encodeURIComponent(parts[0].slice(1))}`;
  }
  if (parts[0] === "joinchat" && parts[1]) {
    return `${scheme}://join?invite=${encodeURIComponent(parts[1])}`;
  }
  if (parts[0] === "addstickers" && parts[1]) {
    return `${scheme}://addstickers?set=${encodeURIComponent(parts[1])}`;
  }
  if (parts[0] === "share" && parts[1] === "url") {
    return `${scheme}://msg_url?url=${encodeURIComponent(qval(qs, "url"))}&text=${encodeURIComponent(qval(qs, "text"))}`;
  }
  if (parts[1] && /^\d+$/.test(parts[1])) {
    return `${scheme}://resolve?domain=${encodeURIComponent(parts[0])}&post=${encodeURIComponent(parts[1])}`;
  }
  return `${scheme}://resolve?domain=${encodeURIComponent(parts[0])}`;
}

export default async function (ctx) {
  const url = ctx.request.url;
  const match = url.match(/^https?:\/\/(?:t\.me|telegram\.me)\/(.+)$/i);
  if (!match) return;

  const client = (ctx.env?.CLIENT || "Telegram").trim();
  if (client === "Telegram") return;

  const scheme = SCHEME[client] || "tg";
  let tail = match[1];
  if (tail.startsWith("s/")) tail = tail.slice(2);

  const queryIndex = tail.indexOf("?");
  const path = queryIndex < 0 ? tail : tail.slice(0, queryIndex);
  const query = queryIndex < 0 ? "" : tail.slice(queryIndex + 1);
  const location = deeplink(scheme, path, query);
  if (!location) return;

  return ctx.respond({
    status: 302,
    headers: {
      Location: location,
      "Cache-Control": "no-store, no-cache",
    },
    body: "",
  });
}
