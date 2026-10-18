import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import { useAdvisorDocuments, useDeleteDocument, type Document } from '@/api/documents'
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

export function DocumentsPage() {
  const { data: documents, isLoading } = useAdvisorDocuments()
  const firmWideDocuments = (documents ?? []).filter((d) => d.client_id === null)
  const deleteDocument = useDeleteDocument()

  const columns: ColumnDef<Document>[] = [
    { accessorKey: 'filename', header: 'File' },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ getValue }) => {
        // Every document on this page is firm-wide (no client), so
        // all of them are searchable by the AI assistant.
        const category = getValue() as string
        return <Badge variant="success">{formatEnumLabel(category)}</Badge>
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
                  onClick={() => deleteDocument.mutate({ documentId: row.original.id })}
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
        <div>
          <CardTitle>Documents</CardTitle>
          <p className="text-sm text-muted-foreground">
            Firm-wide and regulatory documents, not tied to a specific client.
          </p>
        </div>
        <DocumentUploadDialog trigger={<Button size="sm">Upload document</Button>} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={firmWideDocuments}
            emptyMessage="No firm-wide documents uploaded yet."
          />
        )}
      </CardContent>
    </Card>
  )
}
