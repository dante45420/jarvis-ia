/** Hooks mínimos de estado async: uno auto-carga al montar, otro dispara acciones a pedido. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/api/client";

export type AsyncState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

function messageFrom(error: unknown): string {
  if (error instanceof ApiError && error.status === 0) {
    return "Sin conexión con Jarvis. Revisa tu internet.";
  }
  return "Algo falló al hablar con Jarvis. Reintenta.";
}

/** Ejecuta `fn` al montar (y cuando cambie `deps`), exponiendo carga/error/datos. */
export function useAsync<T>(fn: () => Promise<T>, deps: readonly unknown[]): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null });
  const mounted = useRef(true);

  const run = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    fn()
      .then((data) => mounted.current && setState({ data, loading: false, error: null }))
      .catch((error) => mounted.current && setState({ data: null, loading: false, error: messageFrom(error) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mounted.current = true;
    run();
    return () => {
      mounted.current = false;
    };
  }, [run]);

  return { ...state, reload: run };
}

/** Acción disparada a mano (submit): expone `run`, estado de carga y error. */
export function useAction<A extends unknown[], T>(
  fn: (...args: A) => Promise<T>,
): { run: (...args: A) => Promise<T | null>; loading: boolean; error: string | null } {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (...args: A): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        return await fn(...args);
      } catch (caught) {
        setError(messageFrom(caught));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fn],
  );

  return { run, loading, error };
}
