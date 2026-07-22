/** Placeholder con pulso suave: para listas mientras cargan (muestra la estructura). */
import { useEffect, useRef } from "react";
import { Animated, View } from "react-native";
import { palette, radius, spacing } from "@/theme";

function Bar({ width, height }: { width: number | `${number}%`; height: number }) {
  const pulse = useRef(new Animated.Value(0.4)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 0.9, duration: 800, useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0.4, duration: 800, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  return <Animated.View style={{ width, height, borderRadius: 6, backgroundColor: palette.surface2, opacity: pulse }} />;
}

function SkeletonCard() {
  return (
    <View style={styles.card}>
      <Bar width="70%" height={14} />
      <View style={{ height: spacing.sm }} />
      <Bar width="100%" height={10} />
      <View style={{ height: spacing.xs }} />
      <Bar width="45%" height={10} />
    </View>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <View style={{ gap: spacing.md }}>
      {Array.from({ length: count }).map((_, index) => (
        <SkeletonCard key={index} />
      ))}
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
};
