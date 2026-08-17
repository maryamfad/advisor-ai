import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type RiskQuestionnaire = components['schemas']['RiskQuestionnaireRead']
export type RiskQuestionnaireCreateResult =
  components['schemas']['RiskQuestionnaireCreateResult']
export type QuestionnaireCatalog = components['schemas']['QuestionnaireCatalog']
export type SubmitResultResponse = components['schemas']['SubmitResultResponse']

export function useRiskQuestionnaires(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'risk-questionnaire'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/risk-questionnaire', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateRiskQuestionnaire(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/risk-questionnaire', {
          params: { path: { client_id: clientId } },
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'risk-questionnaire'],
      })
    },
  })
}

export function useMarkRiskQuestionnaireSent(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (questionnaireId: number) =>
      unwrap(
        await apiClient.POST(
          '/clients/{client_id}/risk-questionnaire/{questionnaire_id}/mark-sent',
          { params: { path: { client_id: clientId, questionnaire_id: questionnaireId } } }
        )
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['clients', clientId, 'risk-questionnaire'],
      })
    },
  })
}

/** Public, unauthenticated -- used only by the client-facing questionnaire
 * page. A 410 means it was already completed. */
export function useQuestionnaireCatalog(token: string) {
  return useQuery({
    queryKey: ['risk-questionnaire', token],
    queryFn: async () => {
      const { data, error, response } = await apiClient.GET('/risk-questionnaire/{token}', {
        params: { path: { token } },
      })
      if (error !== undefined) {
        throw Object.assign(new Error(response.statusText), { status: response.status })
      }
      return data
    },
    retry: false,
  })
}

export function useSubmitQuestionnaire(token: string) {
  return useMutation({
    mutationFn: async (answers: Record<string, string>) =>
      unwrap(
        await apiClient.POST('/risk-questionnaire/{token}/submit', {
          params: { path: { token } },
          body: { answers },
        })
      ),
  })
}
