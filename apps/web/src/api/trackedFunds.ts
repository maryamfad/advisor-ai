import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type TrackedFund = components['schemas']['TrackedFundRead']
export type TrackedFundCreatePayload = components['schemas']['TrackedFundCreate']
export type ClientTrackedFund = components['schemas']['ClientTrackedFundRead']
export type FundPerformanceResponse = components['schemas']['FundPerformanceResponse']

// -- Advisor's shared catalog -------------------------------------------

export function useTrackedFunds() {
  return useQuery({
    queryKey: ['tracked-funds'],
    queryFn: async () => unwrap(await apiClient.GET('/tracked-funds')),
  })
}

export function useCreateTrackedFund() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: TrackedFundCreatePayload) =>
      unwrap(await apiClient.POST('/tracked-funds', { body: payload })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['tracked-funds'] })
    },
  })
}

export function useDeleteTrackedFund() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (trackedFundId: number) => {
      const { error, response } = await apiClient.DELETE('/tracked-funds/{tracked_fund_id}', {
        params: { path: { tracked_fund_id: trackedFundId } },
      })
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['tracked-funds'] })
    },
  })
}

// -- Per-client selection -------------------------------------------------

export function useClientTrackedFunds(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'tracked-funds'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/tracked-funds', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useSelectTrackedFundForClient(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (trackedFundId: number) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/tracked-funds', {
          params: { path: { client_id: clientId } },
          body: { tracked_fund_id: trackedFundId },
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'tracked-funds'] })
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'tracked-funds', 'performance'],
      })
    },
  })
}

export function useUnselectTrackedFundForClient(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (trackedFundId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/tracked-funds/{tracked_fund_id}',
        { params: { path: { client_id: clientId, tracked_fund_id: trackedFundId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'tracked-funds'] })
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'tracked-funds', 'performance'],
      })
    },
  })
}

export function useFundPerformance(
  clientId: number,
  range: { start_date?: string; end_date?: string } = {}
) {
  return useQuery({
    queryKey: ['clients', clientId, 'tracked-funds', 'performance', range],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/tracked-funds/performance', {
          params: { path: { client_id: clientId }, query: range },
        })
      ),
  })
}
