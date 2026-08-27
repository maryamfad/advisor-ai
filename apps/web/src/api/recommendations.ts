import { useQuery } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type ClientAdvice = components['schemas']['ClientAdvice']

export function useClientAdvice(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'advice'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/advice', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}
