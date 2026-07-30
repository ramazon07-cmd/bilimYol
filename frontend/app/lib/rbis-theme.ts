export const RBIS_COLORS = {
  primary: "#65001F",
  deep: "#450417",
  hover: "#7A1233",
  cream: "#F5E8DC",
  surface: "#FFF9F4",
  text: "#29161C",
  white: "#FFFFFF",
  border: "#DEC8BE",
  success: "#287A55",
  warning: "#C68A22",
  error: "#B4233A",
} as const;

export const RBIS_CHART_COLORS = [
  RBIS_COLORS.primary,
  RBIS_COLORS.hover,
  RBIS_COLORS.deep,
] as const;

export function rbisChartColor(key: string | number, fallbackIndex = 0) {
  const source = String(key);
  const hash = [...source].reduce((total, character) => total + character.charCodeAt(0), fallbackIndex);
  return RBIS_CHART_COLORS[Math.abs(hash) % RBIS_CHART_COLORS.length];
}
