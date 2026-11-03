/**
 * Egern Adapter Script for 美图秀秀 (Meitu) posters init purification.
 * 
 * Compliant with Egern Scripting ES Module specification:
 * - Default export async function(ctx)
 * - Safely deletes data.vip while preserving all other configuration nodes
 * - Returns undefined on no-op or parsing errors
 */

export default async function (ctx) {
  const { response } = ctx ?? {};

  if (!response?.body) {
    return undefined;
  }

  try {
    const rawText = typeof response.body === 'string'
      ? response.body
      : new TextDecoder('utf-8').decode(response.body);

    const data = JSON.parse(rawText);

    if (data && typeof data === 'object' && data.data && typeof data.data === 'object') {
      if ('vip' in data.data) {
        delete data.data.vip;
        return { body: JSON.stringify(data) };
      }
    }

    return undefined;
  } catch (_) {
    return undefined;
  }
}
