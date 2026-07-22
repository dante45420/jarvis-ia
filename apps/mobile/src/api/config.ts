/** Configuración del backend. La URL viene de app config; cae al deploy de Render. */
import Constants from "expo-constants";

const FALLBACK_URL = "https://jarvis-backend-cs90.onrender.com";

// Orden: variable de build (EXPO_PUBLIC_API_URL, definida en eas.json) → extra de app.json → deploy.
export const apiBaseUrl: string =
  process.env.EXPO_PUBLIC_API_URL ??
  (Constants.expoConfig?.extra?.apiBaseUrl as string | undefined) ??
  FALLBACK_URL;

// Dueño de los temas. MVP mono-usuario; se reemplaza al sumar cuentas.
export const ownerId = "dante";
