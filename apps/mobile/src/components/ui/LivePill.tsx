/** Píldora "en vivo": un punto teal que late para señalar actividad en curso. */
import { useEffect, useRef } from "react";
import { Animated, Easing, View } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";

type Props = { label?: string };

export function LivePill({ label = "en vivo" }: Props) {
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(pulse, {
        toValue: 1,
        duration: 1800,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 2.6] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0] });

  return (
    <View style={styles.wrap}>
      <View style={styles.dotWrap}>
        <Animated.View style={[styles.halo, { transform: [{ scale }], opacity }]} />
        <View style={styles.dot} />
      </View>
      <Txt variant="mono" color={palette.teal}>
        {label.toUpperCase()}
      </Txt>
    </View>
  );
}

const styles = {
  wrap: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    alignSelf: "flex-start" as const,
    gap: spacing.sm,
    backgroundColor: "rgba(70,211,196,0.14)",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 1,
    borderRadius: radius.pill,
  },
  dotWrap: { width: 8, height: 8, alignItems: "center" as const, justifyContent: "center" as const },
  halo: { position: "absolute" as const, width: 8, height: 8, borderRadius: 4, backgroundColor: palette.teal },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: palette.teal },
};
