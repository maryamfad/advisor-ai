import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import { useClientDocuments, useDeleteDocument, type Document } from '@/api/documents'
import { Button, buttonVariants } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { formatDateTime, formatEnumLabel } from '@/lib/format'
import { DocumentUploadDialog } from '@/features/documents/DocumentUploadDialog'

export function DocumentsTab({ clientId }: { clientId: number }) {
  const { data: documents, isLoading } = useClientDocuments(clientId)
  const deleteDocument = useDeleteDocument()

  const columns: ColumnDef<Document>[] = [
    { accessorKey: 'filename', header: 'File' },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ getValue }) => {
        // Every document on this tab belongs to this client, so none
        // of them are ever searchable by the AI assistant -- see
        // DocumentsPage for firm-wide, searchable documents.
        const category = getValue() as string
        return <Badge variant="outline">{formatEnumLabel(category)}</Badge>
      },
    },
    {
      accessorKey: 'uploaded_at',
      header: 'Uploaded',
      cell: ({ getValue }) => formatDateTime(getValue() as string),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon">
                <Trash2 className="size-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete this document?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete &ldquo;{row.original.filename}&rdquo;. This
                  can&apos;t be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className={buttonVariants({ variant: 'destructive' })}
                  onClick={() =>
                    deleteDocument.mutate({ documentId: row.original.id, clientId })
                  }
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Documents</CardTitle>
        <DocumentUploadDialog
          clientId={clientId}
          trigger={<Button size="sm">Upload document</Button>}
        />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={documents ?? []}
            emptyMessage="No documents uploaded yet."
          />
        )}
      </CardContent>
    </Card>
  )
}
