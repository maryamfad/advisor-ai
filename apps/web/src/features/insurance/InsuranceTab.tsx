import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import {
  useInsurancePolicies,
  useDeleteInsurancePolicy,
  type InsurancePolicy,
} from '@/api/insurancePolicies'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import { formatCurrencyPrecise, formatEnumLabel } from '@/lib/format'
import { InsurancePolicyDialog } from '@/features/insurance/InsurancePolicyDialog'

const STATUS_VARIANT: Record<string, 'success' | 'secondary' | 'destructive'> = {
  active: 'success',
  lapsed: 'secondary',
  cancelled: 'destructive',
}

export function InsuranceTab({ clientId }: { clientId: number }) {
  const { data: policies, isLoading } = useInsurancePolicies(clientId)
  const deletePolicy = useDeleteInsurancePolicy(clientId)

  const columns: ColumnDef<InsurancePolicy>[] = [
    {
      accessorKey: 'policy_type',
      header: 'Type',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'insured_owner',
      header: 'Insured',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    { accessorKey: 'provider', header: 'Provider' },
    {
      accessorKey: 'coverage_amount',
      header: 'Coverage',
      cell: ({ getValue }) => {
        const value = getValue() as string | null
        return value ? formatCurrencyPrecise(value) : '—'
      },
    },
    {
      accessorKey: 'premium',
      header: 'Premium',
      cell: ({ row }) => {
        const { premium, premium_frequency } = row.original
        if (!premium) return '—'
        return `${formatCurrencyPrecise(premium)}${
          premium_frequency ? ` / ${formatEnumLabel(premium_frequency)}` : ''
        }`
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => {
        const status = getValue() as string
        return <Badge variant={STATUS_VARIANT[status] ?? 'outline'}>{formatEnumLabel(status)}</Badge>
      },
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end gap-1">
          <InsurancePolicyDialog
            clientId={clientId}
            policy={row.original}
            trigger={
              <Button variant="ghost" size="sm">
                Edit
              </Button>
            }
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => deletePolicy.mutate(row.original.id)}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Insurance policies</CardTitle>
        <InsurancePolicyDialog
          clientId={clientId}
          trigger={<Button size="sm">Add policy</Button>}
        />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={policies ?? []}
            emptyMessage="No insurance policies on file."
          />
        )}
      </CardContent>
    </Card>
  )
}
