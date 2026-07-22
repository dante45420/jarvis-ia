/** Punto único de acceso al tema: paleta, tipografía y espaciado. */
import { palette } from "./palette";
import { fontFamily, fontSize } from "./typography";

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = {
  sm: 10,
  md: 14,
  lg: 18,
  xl: 24,
  pill: 999,
} as const;

export const theme = {
  palette,
  fontFamily,
  fontSize,
  spacing,
  radius,
} as const;

export type Theme = typeof theme;
export { palette, fontFamily, fontSize };
