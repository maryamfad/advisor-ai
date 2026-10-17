import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Document = components['schemas']['DocumentRead']
export type DocumentCategory = components['schemas']['DocumentCategory']

type UploadDocumentBody =
  components['schemas']['Body_upload_document_clients__client_id__documents_post']

export function useDocuments(clientId: number) {
  return useQuery({
    queryKey: ['clients', clientId, 'documents'],
    queryFn: async () =>
      unwrap(
        await apiClient.GET('/clients/{client_id}/documents', {
          params: { path: { client_id: clientId } },
        })
      ),
  })
}

/** Thrown when the backend returns 503 -- no openai_api_key configured,
 * so an insurance_policy upload couldn't be made searchable. The file
 * itself is still saved and the row still created either way. */
export class DocumentIngestionUnavailableError extends Error {}

export function useUploadDocument(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ file, category }: { file: File; category: DocumentCategory }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', category)

      const { data, error, response } = await apiClient.POST('/clients/{client_id}/documents', {
        params: { path: { client_id: clientId } },
        // openapi-fetch requires a real FormData instance for a
        // multipart/form-data body -- the generated type reflects the
        // JSON Schema shape (file: string), not the runtime value.
        body: formData as unknown as UploadDocumentBody,
      })

      if (response.status === 503) {
        void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
        throw new DocumentIngestionUnavailableError(
          'Saved, but not searchable by the AI assistant -- policy-document search is not configured for this environment.'
        )
      }
      if (error !== undefined) throw new Error(response.statusText)
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
    },
  })
}

export function useDeleteDocument(clientId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (documentId: number) => {
      const { error, response } = await apiClient.DELETE(
        '/clients/{client_id}/documents/{document_id}',
        { params: { path: { client_id: clientId, document_id: documentId } } }
      )
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
    },
  })
}
