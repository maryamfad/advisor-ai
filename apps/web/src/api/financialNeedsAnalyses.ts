import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type FinancialNeedsAnalysis = components['schemas']['FinancialNeedsAnalysisRead']
export type FinancialNeedsAnalysisCreatePayload =
  components['schemas']['FinancialNeedsAnalysisCreate']
export type FinancialNeedsAnalysisUpdatePayload =
  components['schemas']['FinancialNeedsAnalysisUpdate']

export function useFinancialNeedsAnalyses(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'financial-needs-analyses'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/financial-needs-analyses', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateFinancialNeedsAnalysis(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: FinancialNeedsAnalysisCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/financial-needs-analyses', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'financial-needs-analyses'],
      })
    },
  })
}

export function useUpdateFinancialNeedsAnalysis(clientId: number, fnaId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: FinancialNeedsAnalysisUpdatePayload) =>
      unwrap(
        await apiClient.PATCH(
          '/clients/{client_id}/financial-needs-analyses/{financial_needs_analysis_id}',
          {
            params: { path: { client_id: clientId, financial_needs_analysis_id: fnaId } },
            body: payload,
          }
        )
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'financial-needs-analyses'],
      })
    },
  })
}

export function useDeleteFinancialNeedsAnalysis(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (fnaId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/financial-needs-analyses/{financial_needs_analysis_id}',
        { params: { path: { client_id: clientId, financial_needs_analysis_id: fnaId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'financial-needs-analyses'],
      })
    },
  })
}
