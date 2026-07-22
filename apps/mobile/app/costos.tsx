import { View } from "react-native";
import { palette, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Card } from "@/components/ui/Card";
import { Txt } from "@/components/ui/Txt";
import { hubTabs } from "@/modules/registry";
import { useScreenContext } from "@/state/useScreenContext";

type Line = { name: string; amount: string; ratio: number; color: string };

const LINES: Line[] = [
  { name: "Heraldo · Voz", amount: "$0,30", ratio: 0.72, color: palette.gold },
  { name: "Heraldo · Guiones", amount: "$0,08", ratio: 0.2, color: palette.teal },
  { name: "Heraldo · Noticias", amount: "$0,04", ratio: 0.1, color: palette.teal },
];

export default function Costos() {
  useScreenContext(null, hubTabs, "/costos");
  return (
    <Screen kicker="Julio 2026" title="Costos">
      <Card>
        <View style={{ flexDirection: "row", alignItems: "baseline", justifyContent: "space-between" }}>
          <Txt variant="hero">$0,42</Txt>
          <Txt variant="mono" dim>
            DE $5 TOPE
          </Txt>
        </View>
        <View style={{ gap: spacing.md, marginTop: spacing.lg }}>
          {LINES.map((line) => (
            <CostBar key={line.name} line={line} />
          ))}
        </View>
      </Card>

      <Card>
        <Txt variant="mono" color={palette.teal}>
          VALOR ENTREGADO
        </Txt>
        <Txt variant="body" style={{ marginTop: spacing.sm }}>
          12 podcasts · 40 noticias · 3 búsquedas en vivo. Cada peso rinde: la IA solo se gasta
          en lo que tú eliges profundizar.
        </Txt>
      </Card>
    </Screen>
  );
}

function CostBar({ line }: { line: Line }) {
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
      <Txt variant="small" dim style={{ width: 110 }}>
        {line.name}
      </Txt>
      <View style={styles.track}>
        <View style={{ height: 6, borderRadius: 4, backgroundColor: line.color, width: `${line.ratio * 100}%` }} />
      </View>
      <Txt variant="mono" style={{ width: 44, textAlign: "right" }}>
        {line.amount}
      </Txt>
    </View>
  );
}

const styles = {
  track: {
    flex: 1,
    height: 6,
    borderRadius: 4,
    backgroundColor: palette.surface3,
    overflow: "hidden" as const,
  },
};
