import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Dependent = components['schemas']['DependentRead']
export type DependentCreatePayload = components['schemas']['DependentCreate']
export type DependentUpdatePayload = components['schemas']['DependentUpdate']

export function useDependents(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'dependents'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/dependents', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateDependent(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: DependentCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/dependents', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'dependents'] })
    },
  })
}

export function useUpdateDependent(clientId: number, dependentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: DependentUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/dependents/{dependent_id}', {
          params: { path: { client_id: clientId, dependent_id: dependentId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'dependents'] })
    },
  })
}

export function useDeleteDependent(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (dependentId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/dependents/{dependent_id}',
        { params: { path: { client_id: clientId, dependent_id: dependentId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'dependents'] })
    },
  })
}
