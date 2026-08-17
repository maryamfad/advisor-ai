import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import { useTrackedFunds, useDeleteTrackedFund, type TrackedFund } from '@/api/trackedFunds'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/data-table/DataTable'
import { formatEnumLabel } from '@/lib/format'
import { TrackedFundDialog } from '@/features/trackedFunds/TrackedFundDialog'

export function TrackedFundsPage() {
  const { data: funds, isLoading } = useTrackedFunds()
  const deleteFund = useDeleteTrackedFund()

  const columns: ColumnDef<TrackedFund>[] = [
    { accessorKey: 'symbol', header: 'Symbol' },
    { accessorKey: 'display_name', header: 'Name' },
    {
      accessorKey: 'fund_type',
      header: 'Type',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button variant="ghost" size="icon" onClick={() => deleteFund.mutate(row.original.id)}>
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Tracked funds</h1>
          <p className="text-sm text-muted-foreground">
            Your shared fund catalog -- select from these on any client's Funds tab.
          </p>
        </div>
        <TrackedFundDialog />
      </div>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <DataTable
          columns={columns}
          data={funds ?? []}
          emptyMessage="No funds in your catalog yet."
        />
      )}
    </div>
  )
}
