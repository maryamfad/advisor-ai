import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type AiConversation = components['schemas']['AiConversationRead']
export type AiMessage = components['schemas']['AiMessageRead']
export type SendMessageResponse = components['schemas']['SendMessageResponse']

export function useConversations(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'assistant', 'conversations'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/assistant/conversations', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useConversation(clientId: number, conversationId: number | null) {
  return useQuery({
    queryKey: ['clients', clientId, 'assistant', 'conversations', conversationId],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/assistant/conversations/{conversation_id}', {
          params: { path: { client_id: clientId, conversation_id: conversationId! } },
        })
      ),
    enabled: conversationId !== null,
  })
}

export function useCreateConversation(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/assistant/conversations', {
          params: { path: { client_id: clientId } },
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'assistant', 'conversations'],
      })
    },
  })
}

/** Thrown when the backend returns 503 -- no anthropic_api_key configured. */
export class AssistantUnavailableError extends Error {}

export function useSendMessage(clientId: number, conversationId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (message: string) => {
      const { data, error, response } = await apiClient.POST(
        '/clients/{client_id}/assistant/conversations/{conversation_id}/messages',
        {
          params: { path: { client_id: clientId, conversation_id: conversationId } },
          body: { message },
        }
      )
      if (response.status === 503) {
        throw new AssistantUnavailableError(
          'The AI assistant is not configured for this environment.'
        )
      }
      if (error !== undefined) throw new Error(response.statusText)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'assistant', 'conversations', conversationId],
      })
    },
  })
}
