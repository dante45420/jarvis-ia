/**
 * Contrato de módulo en el frontend. Espeja la idea del backend: la app es un
 * caparazón que hospeda módulos-plugin. Cada módulo aporta sus pestañas
 * contextuales; el hub central es lo único fijo del tab bar.
 */
import type { ComponentProps } from "react";
import type { Ionicons } from "@expo/vector-icons";

export type IoniconName = ComponentProps<typeof Ionicons>["name"];

export type ModuleTab = {
  key: string;
  title: string;
  icon: IoniconName;
  route: string;
};

export type ModuleDef = {
  id: string;
  name: string;
  glyph: string;
  tagline: string;
  tabs: ModuleTab[];
  home: string;
};
