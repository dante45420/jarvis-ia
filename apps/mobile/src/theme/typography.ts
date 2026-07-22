/**
 * Tipografía "Titular" (T4): Archivo para display, Figtree para cuerpo,
 * JetBrains Mono para datos y tiempos. Los nombres coinciden con las claves
 * que exportan los paquetes @expo-google-fonts.
 */
export const fontFamily = {
  display: "Archivo_800ExtraBold",
  bodyRegular: "Figtree_400Regular",
  bodySemibold: "Figtree_600SemiBold",
  mono: "JetBrainsMono_500Medium",
} as const;

export const fontSize = {
  hero: 30,
  title: 22,
  heading: 17,
  body: 15,
  small: 13,
  label: 11,
  micro: 10,
} as const;
