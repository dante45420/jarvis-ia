/** Tarjeta base: superficie, borde y esquinas del tema. */
import { View, type ViewProps } from "react-native";
import { palette, radius, spacing } from "@/theme";

type Props = ViewProps & {
  accent?: string;
};

export function Card({ accent, style, ...rest }: Props) {
  return (
    <View
      {...rest}
      style={[
        {
          backgroundColor: palette.surface,
          borderRadius: radius.lg,
          borderWidth: 1,
          borderColor: accent ?? palette.line,
          padding: spacing.lg,
        },
        style,
      ]}
    />
  );
}
