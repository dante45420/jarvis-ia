import { useEffect, useRef } from "react";
import { Animated, Pressable, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { palette, radius, spacing } from "@/theme";
import { Screen } from "@/components/ui/Screen";
import { Card } from "@/components/ui/Card";
import { Txt } from "@/components/ui/Txt";
import { LivePill } from "@/components/ui/LivePill";
import { heraldoModule } from "@/modules/heraldo/module";
import { useScreenContext } from "@/state/useScreenContext";

export default function Actividad() {
  useScreenContext(heraldoModule.id, heraldoModule.tabs, "/heraldo/actividad");
  return (
    <Screen kicker="Heraldo · hoy" title="Actividad">
      <Card accent={palette.teal}>
        <View style={styles.rowTop}>
          <IconBox icon="headset" tint={palette.teal} />
          <View style={{ flex: 1 }}>
            <Txt variant="label">Preparando tu podcast</Txt>
            <Txt variant="mono" dim style={{ marginTop: 2 }}>
              IA INDUSTRIAL · ECONÓMICO
            </Txt>
          </View>
          <LivePill />
        </View>
        <Txt variant="small" dim style={{ marginTop: spacing.md }}>
          Reuniendo 6 fuentes reales y armando el guion. Te aviso cuando esté.
        </Txt>
        <Progress />
      </Card>

      <FeedCard
        icon="newspaper"
        tint={palette.gold}
        title="Noticiero de la mañana"
        meta="HACE 5 MIN · 3 TITULARES"
        body="Elige cuáles profundizar. Solo esas gastan IA."
        cta="Leer"
      />
      <FeedCard
        icon="sparkles"
        tint={palette.gold}
        title="Hallazgo en tu tema"
        meta="EMPRENDER CON IA · HACE 1 H"
        body="Apareció algo relevante que no habías visto."
      />
      <FeedCard
        icon="pause"
        tint={palette.coral}
        title="Pausé 'Criptomonedas'"
        meta="3 DÍAS SIN ABRIR"
        body="Lo retomo apenas lo abras. Cero gasto mientras tanto."
      />
    </Screen>
  );
}

function FeedCard({
  icon,
  tint,
  title,
  meta,
  body,
  cta,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  tint: string;
  title: string;
  meta: string;
  body: string;
  cta?: string;
}) {
  return (
    <Card>
      <View style={styles.rowTop}>
        <IconBox icon={icon} tint={tint} />
        <View style={{ flex: 1 }}>
          <Txt variant="label">{title}</Txt>
          <Txt variant="mono" dim style={{ marginTop: 2 }}>
            {meta}
          </Txt>
        </View>
      </View>
      <Txt variant="small" dim style={{ marginTop: spacing.md }}>
        {body}
      </Txt>
      {cta ? (
        <Pressable style={({ pressed }) => [styles.cta, pressed && { opacity: 0.85 }]}>
          <Txt variant="label" color={palette.onGold}>
            {cta}
          </Txt>
        </Pressable>
      ) : null}
    </Card>
  );
}

function IconBox({ icon, tint }: { icon: keyof typeof Ionicons.glyphMap; tint: string }) {
  return (
    <View style={[styles.iconBox, { backgroundColor: tintBg(tint) }]}>
      <Ionicons name={icon} size={18} color={tint} />
    </View>
  );
}

function Progress() {
  const anim = useRef(new Animated.Value(0.4)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 0.8, duration: 1600, useNativeDriver: false }),
        Animated.timing(anim, { toValue: 0.45, duration: 1600, useNativeDriver: false }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [anim]);
  const width = anim.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] });
  return (
    <View style={styles.progressTrack}>
      <Animated.View style={{ height: 3, borderRadius: 3, backgroundColor: palette.teal, width }} />
    </View>
  );
}

function tintBg(tint: string): string {
  return tint === palette.coral ? "rgba(240,112,94,0.16)" : tint === palette.gold ? "rgba(245,184,65,0.16)" : "rgba(70,211,196,0.16)";
}

const styles = {
  rowTop: { flexDirection: "row" as const, alignItems: "center" as const, gap: spacing.md },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: radius.sm,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
  cta: {
    marginTop: spacing.md,
    backgroundColor: palette.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: "center" as const,
  },
  progressTrack: {
    height: 3,
    borderRadius: 3,
    backgroundColor: palette.surface3,
    overflow: "hidden" as const,
    marginTop: spacing.md,
  },
};
