import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type InsurancePolicy = components['schemas']['InsurancePolicyRead']
export type InsurancePolicyCreatePayload = components['schemas']['InsurancePolicyCreate']
export type InsurancePolicyUpdatePayload = components['schemas']['InsurancePolicyUpdate']

export function useInsurancePolicies(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'insurance-policies'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/insurance-policies', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateInsurancePolicy(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: InsurancePolicyCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/insurance-policies', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'insurance-policies'] })
    },
  })
}

export function useUpdateInsurancePolicy(clientId: number, policyId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: InsurancePolicyUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/insurance-policies/{insurance_policy_id}', {
          params: { path: { client_id: clientId, insurance_policy_id: policyId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'insurance-policies'] })
    },
  })
}

export function useDeleteInsurancePolicy(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (policyId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/insurance-policies/{insurance_policy_id}',
        { params: { path: { client_id: clientId, insurance_policy_id: policyId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'insurance-policies'] })
    },
  })
}
