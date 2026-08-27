import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Debt = components['schemas']['DebtRead']
export type DebtCreatePayload = components['schemas']['DebtCreate']
export type DebtUpdatePayload = components['schemas']['DebtUpdate']

export function useDebts(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'debts'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/debts', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateDebt(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: DebtCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/debts', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'debts'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useUpdateDebt(clientId: number, debtId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: DebtUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/debts/{debt_id}', {
          params: { path: { client_id: clientId, debt_id: debtId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'debts'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useDeleteDebt(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (debtId: number) => {
      const { error, response } = await apiClient.DELETE('/clients/{client_id}/debts/{debt_id}', {
        params: { path: { client_id: clientId, debt_id: debtId } },
      })
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'debts'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}
