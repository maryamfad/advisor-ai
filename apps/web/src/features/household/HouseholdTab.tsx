import type { ColumnDef } from '@tanstack/react-table'
import { Trash2 } from 'lucide-react'

import { useSpouse, useDeleteSpouse } from '@/api/spouse'
import { useDependents, useDeleteDependent, type Dependent } from '@/api/dependents'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import { formatDate } from '@/lib/format'
import { SpouseDialog } from '@/features/household/SpouseDialog'
import { DependentDialog } from '@/features/household/DependentDialog'

function SpouseSection({ clientId }: { clientId: number }) {
  const { data: spouse, isLoading } = useSpouse(clientId)
  const deleteSpouse = useDeleteSpouse(clientId)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Spouse</CardTitle>
        {!isLoading && !spouse && (
          <SpouseDialog clientId={clientId} trigger={<Button size="sm">Add spouse</Button>} />
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : !spouse ? (
          <p className="text-sm text-muted-foreground">No spouse on file.</p>
        ) : (
          <div className="flex items-center justify-between">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <div className="text-xs text-muted-foreground">Name</div>
                <div className="text-sm font-medium">
                  {spouse.first_name} {spouse.last_name}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Date of birth</div>
                <div className="text-sm font-medium">{formatDate(spouse.date_of_birth)}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Employer</div>
                <div className="text-sm font-medium">{spouse.employer ?? '—'}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Contact</div>
                <div className="text-sm font-medium">{spouse.email ?? spouse.phone ?? '—'}</div>
              </div>
            </div>
            <div className="flex gap-2">
              <SpouseDialog
                clientId={clientId}
                spouse={spouse}
                trigger={
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                }
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => deleteSpouse.mutate()}
                disabled={deleteSpouse.isPending}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DependentsSection({ clientId }: { clientId: number }) {
  const { data: dependents, isLoading } = useDependents(clientId)
  const deleteDependent = useDeleteDependent(clientId)

  const columns: ColumnDef<Dependent>[] = [
    { accessorKey: 'name', header: 'Name' },
    {
      accessorKey: 'date_of_birth',
      header: 'Date of birth',
      cell: ({ getValue }) => formatDate(getValue() as string | null),
    },
    {
      accessorKey: 'years_of_education_remaining',
      header: 'Years of education left',
      cell: ({ getValue }) => (getValue() as number | null) ?? '—',
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex justify-end gap-1">
          <DependentDialog
            clientId={clientId}
            dependent={row.original}
            trigger={
              <Button variant="ghost" size="sm">
                Edit
              </Button>
            }
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => deleteDependent.mutate(row.original.id)}
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
        <CardTitle>Dependents</CardTitle>
        <DependentDialog
          clientId={clientId}
          trigger={<Button size="sm">Add dependent</Button>}
        />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={dependents ?? []}
            emptyMessage="No dependents on file."
          />
        )}
      </CardContent>
    </Card>
  )
}

export function HouseholdTab({ clientId }: { clientId: number }) {
  return (
    <div className="flex flex-col gap-4">
      <SpouseSection clientId={clientId} />
      <DependentsSection clientId={clientId} />
    </div>
  )
}
