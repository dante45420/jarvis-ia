/**
 * Estado de navegación del caparazón. Guarda qué pestañas contextuales muestra
 * el tab bar y cuál ruta está activa. El hub central no vive acá: es fijo.
 */
import { create } from "zustand";
import type { ModuleTab } from "@/modules/types";

type NavState = {
  contextId: string | null;
  tabs: ModuleTab[];
  activeRoute: string;
  setContext: (contextId: string | null, tabs: ModuleTab[], activeRoute: string) => void;
};

export const useNavStore = create<NavState>()((set) => ({
  contextId: null,
  tabs: [],
  activeRoute: "",
  setContext: (contextId, tabs, activeRoute) => set({ contextId, tabs, activeRoute }),
}));
