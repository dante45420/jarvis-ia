/**
 * Progreso narrado para esperas largas (generar podcast, ~2-3 min). En vez de un
 * spinner mudo, cuenta por etapas lo que Jarvis está haciendo: baja la ansiedad de
 * la espera. El logo gira al centro y la etapa avanza en el tiempo.
 */
import { useEffect, useState } from "react";
import { View } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";
import { LogoSpinner } from "@/components/ui/LogoSpinner";

type Props = {
  stages: string[];
  stageSeconds?: number;
};

export function StagedProgress({ stages, stageSeconds = 18 }: Props) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => Math.min(prev + 1, stages.length - 1));
    }, stageSeconds * 1000);
    return () => clearInterval(timer);
  }, [stages.length, stageSeconds]);

  return (
    <View style={styles.wrap}>
      <LogoSpinner size={64} />
      <Txt variant="heading" style={{ marginTop: spacing.lg, textAlign: "center" }}>
        {stages[index]}
      </Txt>
      <View style={styles.dots}>
        {stages.map((_, dot) => (
          <View key={dot} style={[styles.dot, dot <= index && { backgroundColor: palette.teal }]} />
        ))}
      </View>
      <Txt variant="small" dim style={{ marginTop: spacing.md, textAlign: "center" }}>
        Esto toma un par de minutos. Puedes dejar la app y te aviso cuando esté.
      </Txt>
    </View>
  );
}

const styles = {
  wrap: { alignItems: "center" as const, paddingVertical: spacing.xxl },
  dots: { flexDirection: "row" as const, gap: spacing.sm, marginTop: spacing.lg },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: palette.surface3 },
};
