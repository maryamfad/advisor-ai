import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

export type Document = components['schemas']['DocumentRead']
export type DocumentCategory = components['schemas']['DocumentCategory']

type UploadDocumentBody = components['schemas']['Body_upload_document_documents_post']

/** Thrown when the backend returns 503 -- no openai_api_key configured,
 * so an insurance_policy upload couldn't be made searchable. The file
 * itself is still saved and the row still created either way. */
export class DocumentIngestionUnavailableError extends Error {}

// -- Per-client listing (read-only; upload/delete live on the
// advisor-scoped routes below -- same split as tracked funds'
// catalog vs. selection) -------------------------------------------

export function useClientDocuments(clientId: number) {
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

// -- Advisor-scoped (firm-wide, or per-client via clientId) ----------

export function useAdvisorDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: async () => unwrap(await apiClient.GET('/documents')),
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      file,
      category,
      clientId,
    }: {
      file: File
      category: DocumentCategory
      clientId?: number
    }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', category)
      if (clientId !== undefined) formData.append('client_id', String(clientId))

      const { data, error, response } = await apiClient.POST('/documents', {
        // openapi-fetch requires a real FormData instance for a
        // multipart/form-data body -- the generated type reflects the
        // JSON Schema shape (file: string), not the runtime value.
        body: formData as unknown as UploadDocumentBody,
      })

      if (response.status === 503) {
        void queryClient.invalidateQueries({ queryKey: ['documents'] })
        if (clientId !== undefined) {
          void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
        }
        throw new DocumentIngestionUnavailableError(
          'Saved, but not searchable by the AI assistant -- policy-document search is not configured for this environment.'
        )
      }
      if (error !== undefined) throw new Error(response.statusText)
      return data
    },
    onSuccess: (_data, { clientId }) => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
      if (clientId !== undefined) {
        void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
      }
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      documentId,
    }: {
      documentId: number
      clientId?: number
    }) => {
      const { error, response } = await apiClient.DELETE('/documents/{document_id}', {
        params: { path: { document_id: documentId } },
      })
      if (error !== undefined) throw new Error(response.statusText)
    },
    onSuccess: (_data, { clientId }) => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
      if (clientId !== undefined) {
        void queryClient.invalidateQueries({ queryKey: ['clients', clientId, 'documents'] })
      }
    },
  })
}
