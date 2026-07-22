/** Botón primario/secundario con estado de carga. */
import { ActivityIndicator, Pressable, View } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";

type Props = {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary";
  loading?: boolean;
  disabled?: boolean;
};

export function Button({ label, onPress, variant = "primary", loading, disabled }: Props) {
  const isPrimary = variant === "primary";
  const blocked = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={blocked}
      style={({ pressed }) => [
        {
          backgroundColor: isPrimary ? palette.gold : palette.surface2,
          borderWidth: isPrimary ? 0 : 1,
          borderColor: palette.line,
          borderRadius: radius.md,
          paddingVertical: spacing.md + 2,
          alignItems: "center",
          opacity: blocked ? 0.55 : pressed ? 0.85 : 1,
        },
      ]}
    >
      <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
        {loading ? <ActivityIndicator size="small" color={isPrimary ? palette.onGold : palette.text} /> : null}
        <Txt variant="label" color={isPrimary ? palette.onGold : palette.text}>
          {label}
        </Txt>
      </View>
    </Pressable>
  );
}
