import type { components } from "./api-types";

export type Health = components["schemas"]["Health"];

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) throw new ApiError(resp.status, `${resp.status} ${resp.statusText}`);
  return (await resp.json()) as T;
}

export const api = {
  health: () => request<Health>("/health"),
};
