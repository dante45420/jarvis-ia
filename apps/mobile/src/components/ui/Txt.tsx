/** Texto temado. Un solo lugar decide fuente, tamaño y color por variante. */
import { Text, type TextProps, type TextStyle } from "react-native";
import { fontFamily, fontSize, palette } from "@/theme";

type Variant = "hero" | "title" | "heading" | "body" | "small" | "label" | "mono";

const VARIANTS: Record<Variant, TextStyle> = {
  hero: { fontFamily: fontFamily.display, fontSize: fontSize.hero, letterSpacing: -0.5 },
  title: { fontFamily: fontFamily.display, fontSize: fontSize.title, letterSpacing: -0.3 },
  heading: { fontFamily: fontFamily.display, fontSize: fontSize.heading },
  body: { fontFamily: fontFamily.bodyRegular, fontSize: fontSize.body, lineHeight: 21 },
  small: { fontFamily: fontFamily.bodyRegular, fontSize: fontSize.small, lineHeight: 18 },
  label: { fontFamily: fontFamily.bodySemibold, fontSize: fontSize.small },
  mono: { fontFamily: fontFamily.mono, fontSize: fontSize.label, letterSpacing: 0.3 },
};

type Props = TextProps & {
  variant?: Variant;
  color?: string;
  dim?: boolean;
};

export function Txt({ variant = "body", color, dim, style, ...rest }: Props) {
  const resolved = color ?? (dim ? palette.dim : palette.text);
  return <Text {...rest} style={[VARIANTS[variant], { color: resolved }, style]} />;
}
