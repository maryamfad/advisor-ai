import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Check, Copy } from 'lucide-react'

import {
  useRiskQuestionnaires,
  useCreateRiskQuestionnaire,
  useMarkRiskQuestionnaireSent,
  type RiskQuestionnaire,
} from '@/api/riskQuestionnaire'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { formatDateTime, formatEnumLabel } from '@/lib/format'

function linkFor(token: string) {
  return `${window.location.origin}/risk-questionnaire/${token}`
}

function CopyLinkButton({ token }: { token: string }) {
  const [copied, setCopied] = React.useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(linkFor(token))
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button variant="outline" size="sm" onClick={handleCopy}>
      {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
      {copied ? 'Copied' : 'Copy link'}
    </Button>
  )
}

export function RiskQuestionnaireTab({ clientId }: { clientId: number }) {
  const { data: questionnaires, isLoading } = useRiskQuestionnaires(clientId)
  const createQuestionnaire = useCreateRiskQuestionnaire(clientId)
  const markSent = useMarkRiskQuestionnaireSent(clientId)

  const columns: ColumnDef<RiskQuestionnaire>[] = [
    {
      accessorKey: 'created_at',
      header: 'Created',
      cell: ({ getValue }) => formatDateTime(getValue() as string),
    },
    {
      accessorKey: 'sent_at',
      header: 'Sent',
      cell: ({ getValue }) => {
        const value = getValue() as string | null
        return value ? formatDateTime(value) : <Badge variant="secondary">Not sent</Badge>
      },
    },
    {
      accessorKey: 'completed_at',
      header: 'Status',
      cell: ({ getValue }) => {
        const value = getValue() as string | null
        return value ? (
          <Badge variant="success">Completed {formatDateTime(value)}</Badge>
        ) : (
          <Badge variant="outline">Pending</Badge>
        )
      },
    },
    {
      accessorKey: 'score',
      header: 'Score',
      cell: ({ getValue }) => (getValue() as number | null) ?? '—',
    },
    {
      accessorKey: 'risk_tolerance',
      header: 'Risk tolerance',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string | null),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <CopyLinkButton token={row.original.token} />
          {!row.original.completed_at && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markSent.mutate(row.original.id)}
              disabled={markSent.isPending}
            >
              Mark sent
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Risk tolerance questionnaire</CardTitle>
        <Button size="sm" onClick={() => createQuestionnaire.mutate()} disabled={createQuestionnaire.isPending}>
          {createQuestionnaire.isPending ? 'Creating…' : 'New questionnaire'}
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {createQuestionnaire.isSuccess && (
          <Alert>
            <AlertTitle>Questionnaire created</AlertTitle>
            <AlertDescription className="flex w-full items-center justify-between gap-4">
              <span className="truncate font-mono text-xs">
                {linkFor(createQuestionnaire.data.token)}
              </span>
              <CopyLinkButton token={createQuestionnaire.data.token} />
            </AlertDescription>
          </Alert>
        )}
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={questionnaires ?? []}
            emptyMessage="No questionnaires sent yet."
          />
        )}
      </CardContent>
    </Card>
  )
}
