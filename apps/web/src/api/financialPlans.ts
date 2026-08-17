import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type FinancialPlan = components['schemas']['FinancialPlanRead']
export type FinancialPlanActionItem = components['schemas']['FinancialPlanActionItemRead']
export type ActionItemStatus = components['schemas']['ActionItemStatus']

export function useFinancialPlans(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'financial-plans'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/financial-plans', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useGenerateFinancialPlan(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/financial-plans', {
          params: { path: { client_id: clientId } },
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'financial-plans'],
      })
    },
  })
}

export function useUpdateActionItemStatus(clientId: number, planId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ itemId, status }: { itemId: number; status: ActionItemStatus }) =>
      unwrap(
        await apiClient.PATCH(
          '/clients/{client_id}/financial-plans/{plan_id}/action-items/{item_id}',
          {
            params: { path: { client_id: clientId, plan_id: planId, item_id: itemId } },
            body: { status },
          }
        )
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'financial-plans'],
      })
    },
  })
}
