/**
 * Egern: t.me / telegram.me → 指定 Telegram 客户端
 * Version: 1.1.0
 * Updated: 2026-10-06
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

function decode(value) {
  try {
    return decodeURIComponent(String(value || "").replace(/\+/g, " "));
  } catch (_) {
    return String(value || "");
  }
}

function qval(qs, key) {
  if (!qs) return "";
  const escapedKey = key.replace(/[.*+?^{}$()|[\]\\]/g, "\\$&");
  const re = new RegExp("(?:^|&)" + escapedKey + "=([^&]*)");
  const m = qs.match(re);
  return m ? decode(m[1]) : "";
}

function qhas(qs, key) {
  if (!qs) return false;
  const escapedKey = key.replace(/[.*+?^{}$()|[\]\\]/g, "\\$&");
  return new RegExp("(?:^|&)" + escapedKey + "(?:=|&|$)").test(qs);
}

function appendKnownQuery(base, qs, keys) {
  const out = [];
  for (const key of keys) {
    if (!qhas(qs, key)) continue;
    const value = qval(qs, key);
    out.push(value ? `${encodeURIComponent(key)}=${encodeURIComponent(value)}` : encodeURIComponent(key));
  }
  if (!out.length) return base;
  return base + (base.includes("?") ? "&" : "?") + out.join("&");
}

function deeplink(scheme, path, qs) {
  const parts = path.split("/").filter(Boolean).map(decode);
  if (!parts[0]) return "";

  const first = parts[0];

  if (first.startsWith("+")) {
    return `${scheme}://join?invite=${encodeURIComponent(first.slice(1))}`;
  }

  if (first === "joinchat" && parts[1]) {
    return `${scheme}://join?invite=${encodeURIComponent(parts[1])}`;
  }

  if (first === "addstickers" && parts[1]) {
    return `${scheme}://addstickers?set=${encodeURIComponent(parts[1])}`;
  }

  if (first === "addemoji" && parts[1]) {
    return `${scheme}://addemoji?set=${encodeURIComponent(parts[1])}`;
  }

  if (first === "addtheme" && parts[1]) {
    return `${scheme}://addtheme?slug=${encodeURIComponent(parts[1])}`;
  }

  if (first === "setlanguage" && parts[1]) {
    return `${scheme}://setlanguage?lang=${encodeURIComponent(parts[1])}`;
  }

  if (first === "share" && parts[1] === "url") {
    const url = qval(qs, "url");
    const text = qval(qs, "text");
    const params = [];
    if (url) params.push(`url=${encodeURIComponent(url)}`);
    if (text) params.push(`text=${encodeURIComponent(text)}`);
    return `${scheme}://msg_url${params.length ? "?" + params.join("&") : ""}`;
  }

  if ((first === "proxy" || first === "socks") && qs) {
    return `${scheme}://${first}?${qs}`;
  }

  if (first === "c" && /^\d+$/.test(parts[1] || "") && /^\d+$/.test(parts[2] || "")) {
    let target = `${scheme}://privatepost?channel=${encodeURIComponent(parts[1])}&post=${encodeURIComponent(parts[2])}`;
    return appendKnownQuery(target, qs, ["single", "thread", "comment"]);
  }

  let target = `${scheme}://resolve?domain=${encodeURIComponent(first)}`;
  if (parts[1] && /^\d+$/.test(parts[1])) {
    target += `&post=${encodeURIComponent(parts[1])}`;
  }
  return appendKnownQuery(target, qs, [
    "start",
    "startgroup",
    "startchannel",
    "admin",
    "single",
    "thread",
    "comment",
    "boost",
  ]);
}

export default async function (ctx) {
  const url = ctx.request.url;
  const match = url.match(/^https?:\/\/(?:t\.me|telegram\.me)\/(.+)$/i);
  if (!match) return;

  const client = (ctx.env?.CLIENT || "Nagram").trim();

  // 官方 Telegram 直接处理原始 HTTPS Universal Link。
  if (client === "Telegram") return;

  const scheme = SCHEME[client];
  if (!scheme) return;

  let tail = match[1];
  if (tail.startsWith("s/")) tail = tail.slice(2);

  const hashIndex = tail.indexOf("#");
  if (hashIndex >= 0) tail = tail.slice(0, hashIndex);

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
