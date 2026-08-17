import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Advisor = components['schemas']['AdvisorRead']
type AdvisorCreatePayload = components['schemas']['AdvisorCreate']

export function useAdvisors() {
  return useQuery({
    queryKey: ['advisors'],
    queryFn: async () => unwrap(await apiClient.GET('/advisors')),
  })
}

export function useAdvisorById(advisorId: number | null) {
  return useQuery({
    queryKey: ['advisors', advisorId],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/advisors/{advisor_id}', {
          params: { path: { advisor_id: advisorId! } },
        })
      ),
    enabled: advisorId !== null,
  })
}

export function useCreateAdvisor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: AdvisorCreatePayload) =>
      unwrap(await apiClient.POST('/advisors', { body: payload })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['advisors'] })
    },
  })
}
