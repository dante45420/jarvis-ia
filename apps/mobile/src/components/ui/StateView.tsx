/** Envuelve contenido async: muestra spinner al cargar y error con reintento. */
import type { ReactNode } from "react";
import { Pressable, View } from "react-native";
import { palette, radius, spacing } from "@/theme";
import { Txt } from "@/components/ui/Txt";
import { LogoSpinner } from "@/components/ui/LogoSpinner";

type Props = {
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
  loadingLabel?: string;
  skeleton?: ReactNode;
  children: ReactNode;
};

export function StateView({ loading, error, onRetry, loadingLabel, skeleton, children }: Props) {
  if (loading) {
    if (skeleton) {
      return <>{skeleton}</>;
    }
    return (
      <View style={{ alignItems: "center", paddingVertical: spacing.xxl, gap: spacing.lg }}>
        <LogoSpinner size={52} />
        {loadingLabel ? (
          <Txt variant="small" dim>
            {loadingLabel}
          </Txt>
        ) : null}
      </View>
    );
  }
  if (error) {
    return (
      <View style={{ alignItems: "center", paddingVertical: spacing.xl, gap: spacing.md }}>
        <Txt variant="small" color={palette.coral} style={{ textAlign: "center" }}>
          {error}
        </Txt>
        {onRetry ? (
          <Pressable
            onPress={onRetry}
            style={{
              borderWidth: 1,
              borderColor: palette.line,
              borderRadius: radius.md,
              paddingHorizontal: spacing.lg,
              paddingVertical: spacing.sm,
            }}
          >
            <Txt variant="label">Reintentar</Txt>
          </Pressable>
        ) : null}
      </View>
    );
  }
  return <>{children}</>;
}
