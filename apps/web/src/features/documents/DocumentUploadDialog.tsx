import * as React from 'react'

import {
  useUploadDocument,
  DocumentIngestionUnavailableError,
  type DocumentCategory,
} from '@/api/documents'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatEnumLabel } from '@/lib/format'

const CATEGORIES: DocumentCategory[] = [
  'statement',
  'tax_document',
  'insurance_policy',
  'identification',
  'regulatory',
  'investment',
  'other',
]

export function DocumentUploadDialog({
  clientId,
  trigger,
}: {
  clientId?: number
  trigger: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const [file, setFile] = React.useState<File | null>(null)
  const [category, setCategory] = React.useState<DocumentCategory>('other')
  const upload = useUploadDocument()

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!file) return

    try {
      await upload.mutateAsync({ file, category, clientId })
      setOpen(false)
      setFile(null)
      setCategory('other')
    } catch {
      // Surfaced below via upload.isError/upload.error -- dialog stays
      // open so the advisor sees why.
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload document</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="document-file">File</Label>
            <Input
              id="document-file"
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="document-category">Category</Label>
            <Select
              value={category}
              onValueChange={(value) => setCategory(value as DocumentCategory)}
            >
              <SelectTrigger id="document-category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((value) => (
                  <SelectItem key={value} value={value}>
                    {formatEnumLabel(value)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {category === 'insurance_policy' && clientId !== undefined && (
            <p className="text-sm text-muted-foreground">
              Insurance policy documents are searchable by the AI assistant once uploaded.
            </p>
          )}
          {upload.isError && (
            <Alert
              variant={
                upload.error instanceof DocumentIngestionUnavailableError
                  ? 'warning'
                  : 'destructive'
              }
            >
              <AlertDescription>
                {upload.error instanceof DocumentIngestionUnavailableError
                  ? upload.error.message
                  : upload.error instanceof ApiError
                    ? upload.error.message
                    : 'Something went wrong.'}
              </AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            <Button type="submit" disabled={!file || upload.isPending}>
              {upload.isPending ? 'Uploading…' : 'Upload'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
