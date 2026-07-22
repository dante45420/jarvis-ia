import { useState } from "react";
import { View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Card } from "@/components/ui/Card";
import { Txt } from "@/components/ui/Txt";
import { Toggle } from "@/components/ui/Toggle";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";

type ModelTask = { task: string; model: string; free: boolean };

const TASKS: ModelTask[] = [
  { task: "Disección del tema", model: "Gemini Flash", free: true },
  { task: "Guion del podcast", model: "Gemini Flash", free: true },
  { task: "Tarjetas de noticias", model: "Gemini Flash · lote ½", free: true },
  { task: "Voz del podcast", model: "Charon · Gemini TTS", free: false },
];

export default function Config() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/config");
  const [tavily, setTavily] = useState(true);
  const [rss, setRss] = useState(true);

  return (
    <Screen kicker="Módulo Heraldo" title="Ajustes">
      <SectionLabel text="Modelo por tarea · gratis primero" />
      <Card style={{ gap: 0 }}>
        {TASKS.map((task, index) => (
          <ModelRow key={task.task} task={task} last={index === TASKS.length - 1} />
        ))}
      </Card>

      <SectionLabel text="Fuentes · ¿valen lo que cuestan?" />
      <Card style={{ gap: spacing.md }}>
        <SourceRow
          icon="globe"
          tint={palette.teal}
          title="Tavily · web real"
          meta="120 / 1.000 gratis este mes"
          value={tavily}
          onChange={setTavily}
        />
        <View style={styles.divider} />
        <SourceRow
          icon="newspaper"
          tint={palette.gold}
          title="Feeds RSS"
          meta="6 fuentes · siempre $0"
          value={rss}
          onChange={setRss}
        />
      </Card>
    </Screen>
  );
}

function ModelRow({ task, last }: { task: ModelTask; last: boolean }) {
  return (
    <View style={[styles.modelRow, !last && styles.rowBorder]}>
      <View style={{ flex: 1 }}>
        <Txt variant="label">{task.task}</Txt>
        <Txt variant="mono" dim style={{ marginTop: 2 }}>
          {task.model.toUpperCase()}
        </Txt>
      </View>
      <View style={styles.selectChip}>
        <View style={[styles.tag, { backgroundColor: task.free ? "rgba(70,211,196,0.16)" : "rgba(245,184,65,0.15)" }]}>
          <Txt variant="mono" color={task.free ? palette.teal : palette.gold} style={{ fontSize: 9 }}>
            {task.free ? "GRATIS" : "$/MIN"}
          </Txt>
        </View>
        <Txt variant="small">Cambiar</Txt>
        <Ionicons name="chevron-down" size={12} color={palette.dim} />
      </View>
    </View>
  );
}

function SourceRow({
  icon,
  tint,
  title,
  meta,
  value,
  onChange,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  title: string;
  meta: string;
  value: boolean;
  onChange: (next: boolean) => void;
}) {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
      <View style={[styles.sourceIcon, { backgroundColor: tint === palette.gold ? "rgba(245,184,65,0.16)" : "rgba(70,211,196,0.16)" }]}>
        <Ionicons name={icon} size={16} color={tint} />
      </View>
      <View style={{ flex: 1 }}>
        <Txt variant="label">{title}</Txt>
        <Txt variant="small" dim style={{ marginTop: 1 }}>
          {meta}
        </Txt>
      </View>
      <Toggle value={value} onChange={onChange} />
    </View>
  );
}

function SectionLabel({ text }: { text: string }) {
  return (
    <Txt variant="mono" dim style={{ marginTop: spacing.sm }}>
      {text.toUpperCase()}
    </Txt>
  );
}

const styles = {
  modelRow: { flexDirection: "row" as const, alignItems: "center" as const, paddingVertical: spacing.md },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: palette.line },
  selectChip: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: spacing.sm,
    backgroundColor: palette.surface2,
    borderWidth: 1,
    borderColor: palette.line,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  tag: { borderRadius: 5, paddingHorizontal: 6, paddingVertical: 2 },
  sourceIcon: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
  divider: { height: 1, backgroundColor: palette.line },
};
