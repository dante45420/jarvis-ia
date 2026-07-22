/** Registra el contexto (pestañas + ruta activa) del tab bar al enfocar una pantalla. */
import { useCallback } from "react";
import { useFocusEffect } from "expo-router";
import type { ModuleTab } from "@/modules/types";
import { useNavStore } from "@/state/navStore";

export function useScreenContext(contextId: string | null, tabs: ModuleTab[], route: string): void {
  const setContext = useNavStore((state) => state.setContext);
  useFocusEffect(
    useCallback(() => {
      setContext(contextId, tabs, route);
    }, [setContext, contextId, tabs, route]),
  );
}
