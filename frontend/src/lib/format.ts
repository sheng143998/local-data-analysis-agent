/** 千分位格式化，最多保留 2 位小数。 */
export function formatNumber(value: number): string {
  if (!Number.isFinite(value)) return String(value);
  return value.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
}

/** 人民币金额格式化（¥ + 千分位，最多 2 位小数）。 */
export function formatCurrency(value: number): string {
  return `¥${formatNumber(value)}`;
}

/** 若字符串本身是纯数字，则按千分位格式化；否则原样返回。 */
export function formatNumericText(value: string): string {
  const trimmed = value.trim();
  if (trimmed !== '' && Number.isFinite(Number(trimmed))) return formatNumber(Number(trimmed));
  return value;
}
