import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Goal = components['schemas']['GoalRead']
export type GoalCreatePayload = components['schemas']['GoalCreate']
export type GoalUpdatePayload = components['schemas']['GoalUpdate']

export function useGoals(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'goals'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/goals', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

export function useCreateGoal(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: GoalCreatePayload) =>
      unwrap(
        await apiClient.POST('/clients/{client_id}/goals', {
          params: { path: { client_id: clientId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'goals'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useUpdateGoal(clientId: number, goalId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: GoalUpdatePayload) =>
      unwrap(
        await apiClient.PATCH('/clients/{client_id}/goals/{goal_id}', {
          params: { path: { client_id: clientId, goal_id: goalId } },
          body: payload,
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'goals'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}

export function useDeleteGoal(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (goalId: number) => {
      const { error, response } = await apiClient.DELETE('/clients/{client_id}/goals/{goal_id}', {
        params: { path: { client_id: clientId, goal_id: goalId } },
      })
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'goals'] })
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'recommendations'] })
    },
  })
}
