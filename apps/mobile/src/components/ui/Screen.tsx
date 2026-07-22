/** Contenedor de pantalla: safe area, encabezado y scroll con espacio para el tab bar. */
import type { ReactNode } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";

const TAB_BAR_SPACE = 108;

type RightAction = {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
};

type Props = {
  kicker?: string;
  title: string;
  rightAction?: RightAction;
  children: ReactNode;
};

export function Screen({ kicker, title, rightAction, children }: Props) {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ flex: 1, backgroundColor: palette.bg }}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + spacing.md,
          paddingHorizontal: spacing.lg,
          paddingBottom: TAB_BAR_SPACE + insets.bottom,
          gap: spacing.md,
        }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View style={{ flex: 1 }}>
            {kicker ? (
              <Txt variant="mono" color={palette.gold}>
                {kicker.toUpperCase()}
              </Txt>
            ) : null}
            <Txt variant="hero" style={{ marginTop: spacing.xs }}>
              {title}
            </Txt>
          </View>
          {rightAction ? (
            <Pressable onPress={rightAction.onPress} hitSlop={8} style={styles.gear}>
              <Ionicons name={rightAction.icon} size={20} color={palette.dim} />
            </Pressable>
          ) : null}
        </View>
        {children}
      </ScrollView>
    </View>
  );
}

const styles = {
  header: {
    flexDirection: "row" as const,
    alignItems: "flex-start" as const,
    gap: spacing.md,
    marginBottom: spacing.xs,
  },
  gear: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.line,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    marginTop: spacing.lg,
  },
};
