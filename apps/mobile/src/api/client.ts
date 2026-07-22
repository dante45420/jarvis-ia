/**
 * Cliente HTTP mínimo del backend. Invoca capacidades de módulos por su contrato
 * REST: POST /modules/{moduleId}/capabilities/{name}. Sin dependencias extra.
 */
import { apiBaseUrl } from "@/api/config";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function listModules(): Promise<unknown> {
  return request("GET", "/modules");
}

export async function invokeCapability(
  moduleId: string,
  capability: string,
  input: unknown,
): Promise<unknown> {
  const path = `/modules/${moduleId}/capabilities/${capability}`;
  return request("POST", path, input);
}

async function request(method: string, path: string, body?: unknown): Promise<unknown> {
  const response = await fetchOrThrow(method, path, body);
  if (!response.ok) {
    throw new ApiError(`Request a ${path} falló`, response.status);
  }
  return response.json();
}

async function fetchOrThrow(method: string, path: string, body?: unknown): Promise<Response> {
  try {
    return await fetch(`${apiBaseUrl}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Sin conexión con el backend", 0);
  }
}
