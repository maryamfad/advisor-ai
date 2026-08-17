import * as React from 'react'
import { useNavigate } from 'react-router-dom'
import type { ColumnDef } from '@tanstack/react-table'

import { useClients, type Client } from '@/api/clients'
import { DataTable } from '@/components/data-table/DataTable'
import { Input } from '@/components/ui/input'
import { formatDate, formatEnumLabel } from '@/lib/format'
import { ClientCreateDialog } from '@/features/clients/ClientCreateDialog'

const columns: ColumnDef<Client>[] = [
  {
    id: 'name',
    header: 'Name',
    accessorFn: (client) => `${client.first_name} ${client.last_name}`,
  },
  {
    accessorKey: 'email',
    header: 'Email',
  },
  {
    accessorKey: 'phone',
    header: 'Phone',
    cell: ({ getValue }) => (getValue() as string | null) ?? '—',
  },
  {
    accessorKey: 'marital_status',
    header: 'Marital status',
    cell: ({ getValue }) => formatEnumLabel(getValue() as string | null),
  },
  {
    accessorKey: 'created_at',
    header: 'Client since',
    cell: ({ getValue }) => formatDate(getValue() as string),
  },
]

export function ClientsListPage() {
  const { data: clients, isLoading, isError } = useClients()
  const navigate = useNavigate()
  const [search, setSearch] = React.useState('')

  const filtered = React.useMemo(() => {
    if (!clients) return []
    const term = search.trim().toLowerCase()
    if (!term) return clients
    return clients.filter((client) =>
      `${client.first_name} ${client.last_name} ${client.email}`
        .toLowerCase()
        .includes(term)
    )
  }, [clients, search])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Clients</h1>
        <ClientCreateDialog />
      </div>

      <Input
        placeholder="Search clients…"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        className="max-w-sm"
      />

      {isError ? (
        <p className="text-sm text-destructive">Couldn't load clients.</p>
      ) : isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <DataTable
          columns={columns}
          data={filtered}
          emptyMessage="No clients yet. Create your first one to get started."
          onRowClick={(client) => navigate(`/clients/${client.id}`)}
        />
      )}
    </div>
  )
}
