/** Interruptor estilo iOS con desplazamiento animado. */
import { useEffect, useRef } from "react";
import { Animated, Pressable } from "react-native";
import { palette } from "@/theme";

type Props = {
  value: boolean;
  onChange: (next: boolean) => void;
};

export function Toggle({ value, onChange }: Props) {
  const anim = useRef(new Animated.Value(value ? 1 : 0)).current;

  useEffect(() => {
    Animated.timing(anim, {
      toValue: value ? 1 : 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  }, [value, anim]);

  const translateX = anim.interpolate({ inputRange: [0, 1], outputRange: [3, 21] });
  const backgroundColor = anim.interpolate({
    inputRange: [0, 1],
    outputRange: [palette.surface3, palette.teal],
  });

  return (
    <Pressable onPress={() => onChange(!value)} hitSlop={8}>
      <Animated.View
        style={{ width: 46, height: 28, borderRadius: 999, backgroundColor, justifyContent: "center" }}
      >
        <Animated.View
          style={{
            width: 22,
            height: 22,
            borderRadius: 11,
            backgroundColor: "#fff",
            transform: [{ translateX }],
          }}
        />
      </Animated.View>
    </Pressable>
  );
}
