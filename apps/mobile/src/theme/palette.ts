/**
 * Paleta "Vocero nocturno" (P1). Cada acento tiene un significado fijo:
 * oro = importante, teal = en vivo/en progreso, coral = requiere tu atención.
 */
export const palette = {
  bg: "#0C1416",
  surface: "#142023",
  surface2: "#1B292D",
  surface3: "#223438",
  line: "#294044",
  text: "#E8F0EE",
  dim: "#8DA2A2",
  gold: "#F5B841",
  teal: "#46D3C4",
  coral: "#F0705E",
  onGold: "#1A1204",
  onBg: "#E8F0EE",
} as const;

export type Palette = typeof palette;
