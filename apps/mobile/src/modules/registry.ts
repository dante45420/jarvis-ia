/**
 * Registro de módulos disponibles en la app. Agregar un módulo nuevo es sumar
 * su definición acá; el hub y el tab bar lo toman de forma genérica.
 */
import type { ModuleDef, ModuleTab } from "@/modules/types";
import { heraldoModule } from "@/modules/heraldo/module";

export const modules: ModuleDef[] = [heraldoModule];

export function findModule(id: string): ModuleDef | undefined {
  return modules.find((module) => module.id === id);
}

/** Pestañas transversales del hub: lo que no pertenece a un módulo puntual. */
export const hubTabs: ModuleTab[] = [
  { key: "costos", title: "Costos", icon: "stats-chart", route: "/costos" },
  { key: "mensajes", title: "Mensajes", icon: "chatbubbles", route: "/mensajes" },
];
