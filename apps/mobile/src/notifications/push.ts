/** Notificaciones push: registra el token del dispositivo y rutea al tocar el aviso. */
import { useEffect } from "react";
import { Platform } from "react-native";
import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { useRouter, type Router } from "expo-router";
import { invokeCapability } from "@/api/client";
import { ownerId } from "@/api/config";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/** Pide permiso, obtiene el token de Expo y lo registra en el backend. Silencioso si falla. */
export async function registerPushToken(): Promise<void> {
  if (!(await ensurePermission())) {
    return;
  }
  const token = await fetchExpoToken();
  if (!token) {
    return;
  }
  await invokeCapability("herald", "register_push_token", {
    owner_id: ownerId,
    token,
    platform: Platform.OS === "android" ? "android" : "ios",
  }).catch(() => undefined);
}

async function ensurePermission(): Promise<boolean> {
  const current = await Notifications.getPermissionsAsync();
  if (current.granted) {
    return true;
  }
  const asked = await Notifications.requestPermissionsAsync();
  return asked.granted;
}

async function fetchExpoToken(): Promise<string | null> {
  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) {
    return null;
  }
  try {
    return (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  } catch {
    return null;
  }
}

/** Registra el token al abrir y navega al tema cuando tocas una notificación. */
export function usePushSetup(): void {
  const router = useRouter();
  useEffect(() => {
    void registerPushToken();
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      routeFromData(response.notification.request.content.data, router);
    });
    return () => sub.remove();
  }, [router]);
}

function routeFromData(data: Record<string, unknown>, router: Router): void {
  const topicId = typeof data.topic_id === "string" ? data.topic_id : null;
  if (!topicId) {
    return;
  }
  const name = typeof data.name === "string" ? data.name : "";
  router.push(`/heraldo/podcasts?topicId=${topicId}&topic=${encodeURIComponent(name)}`);
}
