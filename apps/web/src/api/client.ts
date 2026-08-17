import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from '@/api/schema'

const ADVISOR_ID_STORAGE_KEY = 'advisor-ai.advisor-id'

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

const advisorHeaderMiddleware: Middleware = {
  onRequest({ request }) {
    const advisorId = window.localStorage.getItem(ADVISOR_ID_STORAGE_KEY)
    if (advisorId) {
      request.headers.set('X-Advisor-Id', advisorId)
    }
    return request
  },
}

export const apiClient = createClient<paths>({ baseUrl: API_BASE_URL })
apiClient.use(advisorHeaderMiddleware)

/** Thrown by unwrap() when a typed API call returns an error response. */
export class ApiError extends Error {
  status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Unwraps an openapi-fetch response, throwing ApiError on failure. Every
 * hook's queryFn/mutationFn should route through this so React Query sees
 * a rejected promise (and its error state) instead of a `{ data, error }`
 * pair it doesn't know how to interpret. */
export function unwrap<T>({
  data,
  error,
  response,
}: {
  data?: T
  error?: unknown
  response: Response
}): T {
  if (error !== undefined) {
    const detail =
      typeof error === 'object' && error !== null && 'detail' in error
        ? String((error as { detail: unknown }).detail)
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  if (data === undefined) {
    throw new ApiError(response.status, 'Empty response body')
  }
  return data
}
