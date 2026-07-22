/** Tarjeta de noticia por capas: gancho → línea → puntos → por qué. Se expande al tocar. */
import { useState } from "react";
import { LayoutAnimation, Platform, Pressable, UIManager, View } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";
import type { NewsCard } from "@/api/types";

if (Platform.OS === "android" && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

export function NewsCardView({ card }: { card: NewsCard }) {
  const [open, setOpen] = useState(false);

  function toggle() {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setOpen((prev) => !prev);
  }

  return (
    <Pressable onPress={toggle}>
      <View style={[styles.card, open && { borderColor: "rgba(245,184,65,0.5)" }]}>
        <Txt variant="heading">{card.hook}</Txt>
        <Txt variant="small" dim style={{ marginTop: spacing.sm }}>
          {card.one_line}
        </Txt>

        {open ? (
          <View style={{ marginTop: spacing.md, gap: spacing.sm }}>
            {card.key_points.map((point) => (
              <View key={point} style={{ flexDirection: "row", gap: spacing.sm }}>
                <Txt variant="small" color={palette.gold}>
                  →
                </Txt>
                <Txt variant="small" style={{ flex: 1 }}>
                  {point}
                </Txt>
              </View>
            ))}
            {card.why_it_matters ? (
              <View style={styles.why}>
                <Txt variant="mono" color={palette.gold}>
                  POR QUÉ TE IMPORTA
                </Txt>
                <Txt variant="small" style={{ marginTop: spacing.xs }}>
                  {card.why_it_matters}
                </Txt>
              </View>
            ) : null}
          </View>
        ) : null}

        <View style={styles.foot}>
          <Txt variant="mono" dim numberOfLines={1} style={{ flex: 1 }}>
            {card.sources.join(" · ")}
          </Txt>
          <Txt variant="mono" color={palette.gold}>
            {open ? "− CERRAR" : "+ PROFUNDIZAR"}
          </Txt>
        </View>
      </View>
    </Pressable>
  );
}

const styles = {
  card: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  why: {
    backgroundColor: "rgba(245,184,65,0.1)",
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.xs,
  },
  foot: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: spacing.sm,
    marginTop: spacing.md,
  },
};
