import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Client = components['schemas']['ClientRead']
export type ClientCreatePayload = components['schemas']['ClientCreate']
export type ClientUpdatePayload = components['schemas']['ClientUpdate']

export function useClients() {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => unwrap(await apiClient.GET('/clients')),
  })
}

export function useClientById(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ClientCreatePayload) =>
      unwrap(await apiClient.POST('/clients', { body: payload })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useUpdateClient(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: ClientUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId] })
    },
  })
}

export function useDeleteClient() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (clientId: number) => {
      const { error, response } = await apiClient.DELETE('/clients/{client_id}', {
        params: { path: { client_id: clientId } },
      })
      if (error !== undefined) {
        throw new Error(response.statusText)
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}
