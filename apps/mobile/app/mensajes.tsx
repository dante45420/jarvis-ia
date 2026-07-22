import { View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Card } from "@/components/ui/Card";
import { Txt } from "@/components/ui/Txt";
import { hubTabs } from "@/modules/registry";
import { useScreenContext } from "@/state/useScreenContext";

type Message = {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  title: string;
  body: string;
  when: string;
  unread?: boolean;
};

const MESSAGES: Message[] = [
  {
    id: "m1",
    icon: "headset",
    tint: palette.teal,
    title: "Tu podcast está listo",
    body: "El superpoder del desarrollador · 3:04, voz Charon.",
    when: "hace 2 min",
    unread: true,
  },
  {
    id: "m2",
    icon: "sparkles",
    tint: palette.gold,
    title: "Hallazgo en tu tema",
    body: "Apareció algo relevante sobre 'emprender con IA'.",
    when: "hace 1 h",
    unread: true,
  },
  {
    id: "m3",
    icon: "pause",
    tint: palette.coral,
    title: "Pausé 'Criptomonedas'",
    body: "3 días sin abrir. Lo retomo apenas lo abras.",
    when: "ayer",
  },
];

export default function Mensajes() {
  useScreenContext(null, hubTabs, "/mensajes");
  return (
    <Screen kicker="Bandeja" title="Mensajes">
      {MESSAGES.map((message) => (
        <MessageRow key={message.id} message={message} />
      ))}
    </Screen>
  );
}

function MessageRow({ message }: { message: Message }) {
  return (
    <Card style={{ flexDirection: "row", gap: spacing.md, alignItems: "flex-start" }}>
      <View style={[styles.icon, { backgroundColor: withAlpha(message.tint) }]}>
        <Ionicons name={message.icon} size={18} color={message.tint} />
      </View>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
          <Txt variant="label" style={{ flex: 1 }}>
            {message.title}
          </Txt>
          {message.unread ? <View style={styles.unread} /> : null}
        </View>
        <Txt variant="small" dim style={{ marginTop: 3 }}>
          {message.body}
        </Txt>
        <Txt variant="mono" dim style={{ marginTop: spacing.sm }}>
          {message.when.toUpperCase()}
        </Txt>
      </View>
    </Card>
  );
}

function withAlpha(color: string): string {
  return color === palette.gold
    ? "rgba(245,184,65,0.16)"
    : color === palette.coral
      ? "rgba(240,112,94,0.16)"
      : "rgba(70,211,196,0.16)";
}

const styles = {
  icon: {
    width: 34,
    height: 34,
    borderRadius: radius.sm,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
  unread: { width: 8, height: 8, borderRadius: 4, backgroundColor: palette.gold },
};
