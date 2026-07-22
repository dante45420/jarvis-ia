/** Chip seleccionable (opción única o múltiple). */
import { Pressable } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";

type Props = {
  label: string;
  selected: boolean;
  onPress: () => void;
};

export function Chip({ label, selected, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        {
          borderWidth: 1,
          borderColor: selected ? palette.gold : palette.line,
          backgroundColor: selected ? "rgba(245,184,65,0.16)" : palette.surface,
          borderRadius: radius.pill,
          paddingHorizontal: spacing.md,
          paddingVertical: spacing.sm,
          opacity: pressed ? 0.8 : 1,
        },
      ]}
    >
      <Txt variant="small" color={selected ? palette.gold : palette.text}>
        {label}
      </Txt>
    </Pressable>
  );
}
