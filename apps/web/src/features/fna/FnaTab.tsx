import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import {
  useFinancialNeedsAnalyses,
  useDeleteFinancialNeedsAnalysis,
  type FinancialNeedsAnalysis,
} from '@/api/financialNeedsAnalyses'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import { formatDate, formatEnumLabel } from '@/lib/format'
import { FnaDialog } from '@/features/fna/FnaDialog'
import { RecommendationSection } from '@/features/recommendations/RecommendationSection'

export function FnaTab({ clientId }: { clientId: number }) {
  const { data: analyses, isLoading } = useFinancialNeedsAnalyses(clientId)
  const deleteFna = useDeleteFinancialNeedsAnalysis(clientId)

  const sorted = [...(analyses ?? [])].sort((a, b) =>
    b.conducted_at.localeCompare(a.conducted_at)
  )

  const columns: ColumnDef<FinancialNeedsAnalysis>[] = [
    {
      accessorKey: 'conducted_at',
      header: 'Conducted on',
      cell: ({ getValue }) => formatDate(getValue() as string),
    },
    {
      accessorKey: 'risk_tolerance',
      header: 'Risk tolerance',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string | null),
    },
    {
      accessorKey: 'investment_knowledge',
      header: 'Investment knowledge',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string | null),
    },
    {
      accessorKey: 'biggest_financial_concern',
      header: 'Biggest concern',
      cell: ({ getValue }) => (getValue() as string | null) ?? '—',
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end gap-1">
          <FnaDialog
            clientId={clientId}
            fna={row.original}
            trigger={
              <Button variant="ghost" size="sm">
                Edit
              </Button>
            }
          />
          <Button variant="ghost" size="icon" onClick={() => deleteFna.mutate(row.original.id)}>
            <Trash2 className="size-4" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Financial Needs Analysis</CardTitle>
          <FnaDialog clientId={clientId} trigger={<Button size="sm">New assessment</Button>} />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <DataTable
              columns={columns}
              data={sorted}
              emptyMessage="No assessments on file yet."
            />
          )}
        </CardContent>
      </Card>

      <RecommendationSection clientId={clientId} />
    </div>
  )
}
