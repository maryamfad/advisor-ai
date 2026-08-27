import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Transaction = components['schemas']['TransactionRead']
export type TransactionCreatePayload = components['schemas']['TransactionCreate']
export type TransactionUpdatePayload = components['schemas']['TransactionUpdate']

export function useTransactions(clientId: number, accountId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'accounts', accountId, 'transactions'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/accounts/{account_id}/transactions', {
          params: { path: { client_id: clientId, account_id: accountId } },
        })
      ),
  })
}

export function useCreateTransaction(clientId: number, accountId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: TransactionCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/accounts/{account_id}/transactions', {
          params: { path: { client_id: clientId, account_id: accountId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'accounts', accountId, 'transactions'],
      })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useDeleteTransaction(clientId: number, accountId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transactionId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/accounts/{account_id}/transactions/{transaction_id}',
        {
          params: {
            path: { client_id: clientId, account_id: accountId, transaction_id: transactionId },
          },
        }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'accounts', accountId, 'transactions'],
      })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}
