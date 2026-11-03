/**
 * Egern Adapter Script for ddgksf2013 splash adblock module.
 *
 * Conforms to Egern Scripting ES Module specification:
 * - Default export async function(ctx)
 * - Returns modified object { body: string } on success
 * - Returns undefined on no modification, errors, or unknown modes
 * - Uses no Surge/Loon globals ($done, $response, etc.)
 */

export default async function (ctx) {
  const { response, env } = ctx ?? {};
  const mode = env?.MODE;

  // 缺少响应体或未匹配到已知处理模式时，直接返回 undefined（保持原样响应）
  if (!response?.body || (mode !== 'qeeniao_clear_data' && mode !== 'taobao_filter_marketing')) {
    return undefined;
  }

  try {
    const rawText = typeof response.body === 'string'
      ? response.body
      : new TextDecoder('utf-8').decode(response.body);

    const data = JSON.parse(rawText);

    // 必须确保是有效的非数组 JSON 对象
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return undefined;
    }

    let modified = false;

    // 模式 1: qeeniao_clear_data
    // 对应 JQ: .data={}
    // 仅清空根层级的 data 对象，完整保留根层级其他所有字段 (如 code, msg, extra 等)
    if (mode === 'qeeniao_clear_data') {
      if (Object.prototype.hasOwnProperty.call(data, 'data')) {
        data.data = {};
        modified = true;
      }
    }

    // 模式 2: taobao_filter_marketing
    // 对应 JQ: .data.model.children |= map(select(.name | contains("营销") | not))
    // 仅过滤 children 数组中 name 包含“营销”的元素，严格保留同级其他字段及其他所有兄弟节点
    else if (mode === 'taobao_filter_marketing') {
      const children = data?.data?.model?.children;
      if (Array.isArray(children)) {
        data.data.model.children = children.filter((item) => {
          if (!item || typeof item !== 'object') return true;
          const name = item.name;
          return typeof name === 'string' ? !name.includes('营销') : true;
        });
        modified = true;
      }
    }

    if (modified) {
      return { body: JSON.stringify(data) };
    }

    return undefined;
  } catch (_) {
    // 解析异常或非预期结构时，严格安全回退，返回 undefined 原样放行
    return undefined;
  }
}
