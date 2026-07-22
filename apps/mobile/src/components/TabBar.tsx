/**
 * Tab bar del caparazón. El hub central es lo único fijo: lleva a la selección
 * de módulos (y desde ahí a costos, mensajes y lo transversal). Las pestañas
 * laterales las aporta el contexto activo: el módulo abierto, o el propio hub.
 */
import { Pressable, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { palette, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";
import { useNavStore } from "@/state/navStore";
import type { ModuleTab } from "@/modules/types";

export function TabBar() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { tabs, activeRoute, contextId } = useNavStore();

  const half = Math.ceil(tabs.length / 2);
  const left = tabs.slice(0, half);
  const right = tabs.slice(half);

  return (
    <View style={[styles.wrap, { paddingBottom: insets.bottom + spacing.sm }]}>
      <View style={styles.row}>
        <View style={styles.side}>
          {left.map((tab) => (
            <TabItem key={tab.key} tab={tab} active={tab.route === activeRoute} onPress={router} />
          ))}
        </View>

        <HubButton active={contextId === null} onPress={() => router.push("/hub")} />

        <View style={styles.side}>
          {right.map((tab) => (
            <TabItem key={tab.key} tab={tab} active={tab.route === activeRoute} onPress={router} />
          ))}
        </View>
      </View>
    </View>
  );
}

type Router = ReturnType<typeof useRouter>;

function TabItem({ tab, active, onPress }: { tab: ModuleTab; active: boolean; onPress: Router }) {
  const color = active ? palette.gold : palette.dim;
  return (
    <Pressable
      style={({ pressed }) => [styles.item, pressed && { opacity: 0.6 }]}
      onPress={() => onPress.push(tab.route as never)}
      hitSlop={6}
    >
      <Ionicons name={tab.icon} size={22} color={color} />
      <Txt variant="mono" color={color} style={{ fontSize: 9 }}>
        {tab.title}
      </Txt>
      {active ? <View style={styles.dot} /> : <View style={styles.dotGhost} />}
    </Pressable>
  );
}

function HubButton({ active, onPress }: { active: boolean; onPress: () => void }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.hub, pressed && { transform: [{ scale: 0.94 }] }]}
      onPress={onPress}
      hitSlop={8}
    >
      <View style={[styles.hubInner, active && styles.hubActive]}>
        <Ionicons name="grid" size={22} color={palette.onGold} />
      </View>
    </Pressable>
  );
}

const styles = {
  wrap: {
    position: "absolute" as const,
    left: 0,
    right: 0,
    bottom: 0,
    paddingTop: spacing.sm,
    paddingHorizontal: spacing.lg,
    backgroundColor: "rgba(10,16,18,0.94)",
    borderTopWidth: 1,
    borderTopColor: palette.line,
  },
  row: { flexDirection: "row" as const, alignItems: "center" as const, justifyContent: "space-between" as const },
  side: { flexDirection: "row" as const, flex: 1, justifyContent: "space-around" as const },
  item: { alignItems: "center" as const, gap: 3, paddingHorizontal: spacing.xs },
  dot: { width: 5, height: 5, borderRadius: 3, backgroundColor: palette.gold, marginTop: 1 },
  dotGhost: { width: 5, height: 5, marginTop: 1 },
  hub: { width: 74, alignItems: "center" as const, justifyContent: "center" as const },
  hubInner: {
    width: 58,
    height: 58,
    borderRadius: 29,
    marginTop: -22,
    backgroundColor: palette.gold,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    shadowColor: palette.gold,
    shadowOpacity: 0.45,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
    borderWidth: 3,
    borderColor: palette.bg,
  },
  hubActive: { borderColor: palette.teal },
};
