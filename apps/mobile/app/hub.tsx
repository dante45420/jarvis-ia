import { Pressable, View } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Card } from "@/components/ui/Card";
import { Txt } from "@/components/ui/Txt";
import { modules, hubTabs } from "@/modules/registry";
import type { ModuleDef } from "@/modules/types";
import { useScreenContext } from "@/state/useScreenContext";

export default function Hub() {
  useScreenContext(null, hubTabs, "/hub");
  const router = useRouter();

  return (
    <Screen kicker="Tus módulos" title="Hola, Dante">
      <Txt dim style={{ marginTop: -spacing.xs }}>
        Elige en qué trabaja Jarvis. Toca el centro del menú para volver acá siempre.
      </Txt>

      {modules.map((module) => (
        <ModuleCard key={module.id} module={module} onPress={() => router.push(module.home as never)} />
      ))}

      <Txt variant="mono" dim style={{ marginTop: spacing.md }}>
        TRANSVERSAL
      </Txt>
      <View style={{ flexDirection: "row", gap: spacing.md }}>
        <Shortcut icon="stats-chart" label="Costos" onPress={() => router.push("/costos")} />
        <Shortcut icon="chatbubbles" label="Mensajes" onPress={() => router.push("/mensajes")} />
      </View>
    </Screen>
  );
}

function ModuleCard({ module, onPress }: { module: ModuleDef; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => pressed && { opacity: 0.85 }}>
      <Card style={{ flexDirection: "row", alignItems: "center", gap: spacing.lg }}>
        <View style={styles.badge}>
          <Txt variant="title" color={palette.onGold}>
            {module.glyph}
          </Txt>
        </View>
        <View style={{ flex: 1 }}>
          <Txt variant="heading">{module.name}</Txt>
          <Txt variant="small" dim style={{ marginTop: 2 }}>
            {module.tagline}
          </Txt>
        </View>
        <Ionicons name="chevron-forward" size={20} color={palette.dim} />
      </Card>
    </Pressable>
  );
}

function Shortcut({
  icon,
  label,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.shortcut, pressed && { opacity: 0.8 }]}>
      <Ionicons name={icon} size={22} color={palette.teal} />
      <Txt variant="label" style={{ marginTop: spacing.sm }}>
        {label}
      </Txt>
    </Pressable>
  );
}

const styles = {
  badge: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    backgroundColor: palette.gold,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
  shortcut: {
    flex: 1,
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
};
