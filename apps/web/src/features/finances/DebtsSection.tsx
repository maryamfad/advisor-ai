import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Trash2 } from 'lucide-react'
import { z } from 'zod'

import { useDebts, useCreateDebt, useDeleteDebt, type Debt } from '@/api/debts'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/data-table/DataTable'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatCurrencyPrecise, formatEnumLabel, formatPercent } from '@/lib/format'

const DEBT_TYPES = [
  'mortgage_primary',
  'mortgage_secondary_heloc',
  'auto_loan',
  'student_loan',
  'credit_card',
  'personal_loan',
  'other',
] as const

const schema = z.object({
  debt_type: z.enum(DEBT_TYPES),
  description: z.string().optional(),
  lender: z.string().optional(),
  balance: z.string().min(1, 'Required'),
  interest_rate: z.string().optional(),
  minimum_payment: z.string().optional(),
})

function DebtDialog({ clientId }: { clientId: number }) {
  const [open, setOpen] = React.useState(false)
  const createDebt = useCreateDebt(clientId)

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      debt_type: 'other',
      description: '',
      lender: '',
      balance: '',
      interest_rate: '',
      minimum_payment: '',
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await createDebt.mutateAsync({
      debt_type: values.debt_type,
      description: values.description || null,
      lender: values.lender || null,
      balance: values.balance,
      interest_rate: values.interest_rate || null,
      minimum_payment: values.minimum_payment || null,
    })
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Add debt</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add debt</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="debt_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {DEBT_TYPES.map((type) => (
                          <SelectItem key={type} value={type}>
                            {formatEnumLabel(type)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="lender"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Lender</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="balance"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Balance</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="interest_rate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Interest rate (%)</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="minimum_payment"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Min. payment</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            {createDebt.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {createDebt.error instanceof ApiError
                    ? createDebt.error.message
                    : 'Something went wrong.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={createDebt.isPending}>
                {createDebt.isPending ? 'Saving…' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export function DebtsSection({ clientId }: { clientId: number }) {
  const { data: debts, isLoading } = useDebts(clientId)
  const deleteDebt = useDeleteDebt(clientId)

  const columns: ColumnDef<Debt>[] = [
    {
      accessorKey: 'debt_type',
      header: 'Type',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'lender',
      header: 'Lender',
      cell: ({ getValue }) => (getValue() as string | null) ?? '—',
    },
    {
      accessorKey: 'balance',
      header: 'Balance',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      accessorKey: 'interest_rate',
      header: 'Interest rate',
      cell: ({ getValue }) => {
        const value = getValue() as string | null
        return value ? formatPercent(Number(value) / 100) : '—'
      },
    },
    {
      accessorKey: 'minimum_payment',
      header: 'Min. payment',
      cell: ({ getValue }) => {
        const value = getValue() as string | null
        return value ? formatCurrencyPrecise(value) : '—'
      },
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button variant="ghost" size="icon" onClick={() => deleteDebt.mutate(row.original.id)}>
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Debts</CardTitle>
        <DebtDialog clientId={clientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable columns={columns} data={debts ?? []} emptyMessage="No debts on file." />
        )}
      </CardContent>
    </Card>
  )
}
