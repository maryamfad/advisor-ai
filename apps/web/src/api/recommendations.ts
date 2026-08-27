import { useQuery } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type ClientRecommendation = components['schemas']['ClientRecommendation']

export function useClientRecommendations(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'recommendations'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/recommendations', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}
