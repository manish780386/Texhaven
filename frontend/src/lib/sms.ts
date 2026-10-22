// Mirror of backend/apps/messaging/utils.py. The backend is the source of truth for price and limits.
const GSM7_BASIC =
  "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\u001bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà";
const GSM7_EXT = "^{}\\[~]|€";
export const TOKEN_LENGTH = 24;

export interface SmsInfo {
  encoding: "gsm7" | "ucs2";
  units: number;
  segments: number;
  perSegment: number;
}

export function smsInfo(text: string): SmsInfo {
  const chars = Array.from(text);
  if (chars.every((c) => GSM7_BASIC.includes(c) || GSM7_EXT.includes(c))) {
    const units = chars.reduce((n, c) => n + (GSM7_EXT.includes(c) ? 2 : 1), 0);
    const segments = units === 0 ? 0 : units <= 160 ? 1 : Math.ceil(units / 153);
    return { encoding: "gsm7", units, segments, perSegment: segments > 1 ? 153 : 160 };
  }
  const units = text.length; // JS strings are UTF-16, same as UCS-2 for counting
  const segments = units <= 70 ? 1 : Math.ceil(units / 67);
  return { encoding: "ucs2", units, segments, perSegment: segments > 1 ? 67 : 70 };
}

export const footerFor = (template: string) => template.replace("{token}", "x".repeat(TOKEN_LENGTH));

export const formatMoney = (cents: number, currency: string) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency: currency.toUpperCase() }).format(cents / 100);
