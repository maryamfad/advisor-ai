import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Budget = components['schemas']['BudgetRead']
export type BudgetCreatePayload = components['schemas']['BudgetCreate']
export type BudgetUpdatePayload = components['schemas']['BudgetUpdate']

export function useBudgets(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'budgets'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/budgets', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateBudget(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: BudgetCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/budgets', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'budgets'] })
    },
  })
}

export function useUpdateBudget(clientId: number, budgetId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: BudgetUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/budgets/{budget_id}', {
          params: { path: { client_id: clientId, budget_id: budgetId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'budgets'] })
    },
  })
}

export function useDeleteBudget(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (budgetId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/budgets/{budget_id}',
        { params: { path: { client_id: clientId, budget_id: budgetId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'budgets'] })
    },
  })
}
