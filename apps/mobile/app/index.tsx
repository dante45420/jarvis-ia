import { Redirect } from "expo-router";

/** La entrada de la app es el hub: la selección de módulos. */
export default function Index() {
  return <Redirect href="/hub" />;
}
