import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import { useAccounts, useDeleteAccount, type Account } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import { formatCurrencyPrecise, formatEnumLabel } from '@/lib/format'
import { AccountDialog } from '@/features/finances/AccountDialog'
import { TransactionsSection } from '@/features/finances/TransactionsSection'

export function AccountsSection({ clientId }: { clientId: number }) {
  const { data: accounts, isLoading } = useAccounts(clientId)
  const deleteAccount = useDeleteAccount(clientId)
  const [selectedAccount, setSelectedAccount] = React.useState<Account | null>(null)

  const columns: ColumnDef<Account>[] = [
    { accessorKey: 'name', header: 'Name' },
    {
      accessorKey: 'account_type',
      header: 'Type',
      cell: ({ getValue }) => (getValue() as string).toUpperCase(),
    },
    {
      accessorKey: 'owner',
      header: 'Owner',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'institution',
      header: 'Institution',
      cell: ({ getValue }) => (getValue() as string | null) ?? '—',
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end gap-1">
          <AccountDialog
            clientId={clientId}
            account={row.original}
            trigger={
              <Button variant="ghost" size="sm" onClick={(e) => e.stopPropagation()}>
                Edit
              </Button>
            }
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation()
              deleteAccount.mutate(row.original.id)
            }}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      ),
    },
  ]

  if (selectedAccount) {
    return (
      <Card>
        <CardContent>
          <TransactionsSection
            clientId={clientId}
            account={selectedAccount}
            onBack={() => setSelectedAccount(null)}
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Accounts</CardTitle>
        <AccountDialog clientId={clientId} trigger={<Button size="sm">Add account</Button>} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={accounts ?? []}
            emptyMessage="No accounts yet."
            onRowClick={setSelectedAccount}
          />
        )}
      </CardContent>
    </Card>
  )
}
