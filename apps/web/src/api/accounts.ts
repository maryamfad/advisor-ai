import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Account = components['schemas']['AccountRead']
export type AccountCreatePayload = components['schemas']['AccountCreate']
export type AccountUpdatePayload = components['schemas']['AccountUpdate']

export function useAccounts(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'accounts'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/accounts', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateAccount(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: AccountCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/accounts', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'accounts'] })
    },
  })
}

export function useUpdateAccount(clientId: number, accountId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: AccountUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/accounts/{account_id}', {
          params: { path: { client_id: clientId, account_id: accountId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'accounts'] })
    },
  })
}

export function useDeleteAccount(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (accountId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/accounts/{account_id}',
        { params: { path: { client_id: clientId, account_id: accountId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'accounts'] })
    },
  })
}
