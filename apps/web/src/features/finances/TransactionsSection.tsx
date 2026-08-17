import type { ColumnDef } from '@tanstack/react-table'
import { ChevronLeft, Trash2 } from 'lucide-react'

import { useTransactions, useDeleteTransaction, type Transaction } from '@/api/transactions'
import type { Account } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/data-table/DataTable'
import { formatCurrencyPrecise, formatDate, formatEnumLabel } from '@/lib/format'
import { TransactionDialog } from '@/features/finances/TransactionDialog'

export function TransactionsSection({
  clientId,
  account,
  onBack,
}: {
  clientId: number
  account: Account
  onBack: () => void
}) {
  const { data: transactions, isLoading } = useTransactions(clientId, account.id)
  const deleteTransaction = useDeleteTransaction(clientId, account.id)

  const columns: ColumnDef<Transaction>[] = [
    {
      accessorKey: 'transaction_date',
      header: 'Date',
      cell: ({ getValue }) => formatDate(getValue() as string),
    },
    { accessorKey: 'description', header: 'Description' },
    {
      accessorKey: 'merchant',
      header: 'Merchant',
      cell: ({ getValue }) => (getValue() as string | null) ?? '—',
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'amount',
      header: 'Amount',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => deleteTransaction.mutate(row.original.id)}
        >
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-4" />
          Back to accounts
        </button>
        <TransactionDialog
          clientId={clientId}
          accountId={account.id}
          trigger={<Button size="sm">Add transaction</Button>}
        />
      </div>
      <h3 className="text-sm font-medium text-muted-foreground">
        Transactions for {account.name}
      </h3>
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <DataTable
          columns={columns}
          data={transactions ?? []}
          emptyMessage="No transactions yet."
        />
      )}
    </div>
  )
}
