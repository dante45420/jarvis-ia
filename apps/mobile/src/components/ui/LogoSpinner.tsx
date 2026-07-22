/** El logo de Jarvis girando: loader para esperas indeterminadas o el arranque. */
import { useEffect, useRef } from "react";
import { Animated, Easing } from "react-native";

const LOGO = require("../../../assets/logo.png");

export function LogoSpinner({ size = 56 }: { size?: number }) {
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(spin, {
        toValue: 1,
        duration: 2600,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );
    loop.start();
    return () => loop.stop();
  }, [spin]);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ["0deg", "360deg"] });

  return (
    <Animated.Image
      source={LOGO}
      resizeMode="contain"
      style={{ width: size, height: size, transform: [{ rotate }] }}
    />
  );
}
