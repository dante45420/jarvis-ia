# Jarvis · App móvil

App nativa de Jarvis (Expo / React Native + TypeScript). Es un **caparazón que hospeda
módulos-plugin**: el hub central del tab bar es lo único fijo y lleva a la selección de
módulos y a lo transversal (costos, mensajes). Cada módulo aporta sus pestañas laterales.

Identidad visual: tipografía **Archivo + Figtree** (T4), paleta **Vocero nocturno** (P1).
Ver `docs/ARCHITECTURE.md` (sección "App mobile") y `docs/DECISIONS.md` (D-0010, D-0027).

## Cómo correrla

```bash
cd apps/mobile
npm install
npx expo start
```

Escanea el QR con la app **Expo Go** en tu iPhone, o presiona `i` para el simulador de iOS.

Si alguna versión de dependencia no calza con tu SDK de Expo:

```bash
npx expo install --fix
```

## Estructura

```
app/                      Rutas (expo-router, file-based)
  _layout.tsx             Caparazón: carga fuentes + tab bar persistente
  index.tsx               Redirige al hub
  hub.tsx                 Selección de módulos (+ atajos transversales)
  costos.tsx              Gasto agregado (transversal)
  mensajes.tsx            Bandeja de Jarvis (transversal)
  heraldo/                Pantallas del módulo Heraldo
    actividad.tsx  podcasts.tsx  noticias.tsx  config.tsx
src/
  theme/                  Paleta, tipografía, espaciado (un solo lugar)
  modules/                Contrato de módulo + registro + Heraldo
  state/                  Estado de navegación del tab bar (zustand)
  api/                    Cliente del backend (Heraldo en Render)
  components/             Kit de UI y el TabBar
```

## Agregar un módulo nuevo

1. Crea `src/modules/<id>/module.ts` con su `ModuleDef` (nombre, pestañas, home).
2. Súmalo a `src/modules/registry.ts`.
3. Crea sus pantallas en `app/<id>/`.

El hub y el tab bar lo toman de forma genérica; no hay que tocar el caparazón.

## Backend

Apunta por defecto al deploy de Render. Para cambiarlo, define `extra.apiBaseUrl`
en `app.json` o una variable de entorno de build.
