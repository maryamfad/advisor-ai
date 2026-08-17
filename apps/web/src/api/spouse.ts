import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import type { components } from '@/api/schema'

export type Spouse = components['schemas']['SpouseRead']
export type SpouseCreatePayload = components['schemas']['SpouseCreate']
export type SpouseUpdatePayload = components['schemas']['SpouseUpdate']

/** Spouse is a singular, optional per-client resource -- GET 404s when
 * none exists yet, which we treat as `null` rather than an error. */
export function useSpouse(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'spouse'],
    queryFn: async (): Promise<Spouse | null> => {
      const { data, error, response } = await apiClient.GET('/clients/{client_id}/spouse', {
        params: { path: { client_id: clientId } },
      })
      if (response.status === 404) return null
      if (error !== undefined) throw new Error(response.statusText)
      return data ?? null
    },
  })
}

export function useCreateSpouse(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: SpouseCreatePayload) => {
      const { data, error, response } = await apiClient.POST('/clients/{client_id}/spouse', {
        params: { path: { client_id: clientId } },
        body: payload,
      })
      if (error !== undefined) throw new Error(response.statusText)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'spouse'] })
    },
  })
}

export function useUpdateSpouse(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: SpouseUpdatePayload) => {
      const { data, error, response } = await apiClient.PATCH('/clients/{client_id}/spouse', {
        params: { path: { client_id: clientId } },
        body: payload,
      })
      if (error !== undefined) throw new Error(response.statusText)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'spouse'] })
    },
  })
}

export function useDeleteSpouse(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { error, response } = await apiClient.DELETE('/clients/{client_id}/spouse', {
        params: { path: { client_id: clientId } },
      })
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'spouse'] })
    },
  })
}
