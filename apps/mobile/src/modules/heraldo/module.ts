/** Definición del módulo Heraldo: podcasts, noticiero y buscador. */
import type { ModuleDef } from "@/modules/types";

export const heraldoModule: ModuleDef = {
  id: "heraldo",
  name: "Heraldo",
  glyph: "H",
  tagline: "Podcasts · Noticiero · Buscador",
  home: "/heraldo/actividad",
  tabs: [
    { key: "actividad", title: "Actividad", icon: "pulse", route: "/heraldo/actividad" },
    { key: "podcasts", title: "Podcasts", icon: "headset", route: "/heraldo/podcasts" },
    { key: "noticias", title: "Noticias", icon: "newspaper", route: "/heraldo/noticias" },
    { key: "buscar", title: "Buscar", icon: "search", route: "/heraldo/buscar" },
  ],
};
