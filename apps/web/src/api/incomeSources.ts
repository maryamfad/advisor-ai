import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type IncomeSource = components['schemas']['IncomeSourceRead']
export type IncomeSourceCreatePayload = components['schemas']['IncomeSourceCreate']
export type IncomeSourceUpdatePayload = components['schemas']['IncomeSourceUpdate']

export function useIncomeSources(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'income-sources'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/income-sources', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateIncomeSource(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: IncomeSourceCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/income-sources', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'income-sources'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useUpdateIncomeSource(clientId: number, incomeSourceId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: IncomeSourceUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/income-sources/{income_source_id}', {
          params: { path: { client_id: clientId, income_source_id: incomeSourceId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'income-sources'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useDeleteIncomeSource(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (incomeSourceId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/income-sources/{income_source_id}',
        { params: { path: { client_id: clientId, income_source_id: incomeSourceId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'income-sources'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}
