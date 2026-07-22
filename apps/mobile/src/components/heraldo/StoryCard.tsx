/** Tarjeta de una historia candidata del buscador: título, fuentes y extracto. */
import { Pressable, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";
import type { Story } from "@/api/types";

type Props = {
  story: Story;
  selected?: boolean;
  onToggle?: () => void;
  onOpen?: () => void;
};

export function StoryCard({ story, selected, onToggle, onOpen }: Props) {
  const selectable = onToggle !== undefined;
  return (
    <Pressable
      onPress={selectable ? onToggle : onOpen}
      style={[styles.card, selected && { borderColor: palette.gold }]}
    >
      <View style={{ flexDirection: "row", gap: spacing.md }}>
        {selectable ? <Checkbox on={!!selected} /> : null}
        <View style={{ flex: 1 }}>
          <Txt variant="label">{story.title}</Txt>
          {story.snippet ? (
            <Txt variant="small" dim style={{ marginTop: spacing.xs }} numberOfLines={2}>
              {story.snippet}
            </Txt>
          ) : null}
          <View style={styles.foot}>
            <Txt variant="mono" dim numberOfLines={1} style={{ flex: 1 }}>
              {story.sources.join(" · ")}
            </Txt>
            {onOpen ? <Ionicons name="open-outline" size={14} color={palette.teal} /> : null}
          </View>
        </View>
      </View>
    </Pressable>
  );
}

function Checkbox({ on }: { on: boolean }) {
  return (
    <View style={[styles.box, on && { backgroundColor: palette.gold, borderColor: palette.gold }]}>
      {on ? <Ionicons name="checkmark" size={14} color={palette.onGold} /> : null}
    </View>
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
  foot: { flexDirection: "row" as const, alignItems: "center" as const, gap: spacing.sm, marginTop: spacing.sm },
  box: {
    width: 22,
    height: 22,
    borderRadius: 7,
    borderWidth: 1.5,
    borderColor: palette.line,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    marginTop: 1,
  },
};
