import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Trash2 } from 'lucide-react'
import { z } from 'zod'

import { useBudgets, useCreateBudget, useDeleteBudget, type Budget } from '@/api/budgets'
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
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatCurrencyPrecise, formatEnumLabel } from '@/lib/format'
import { TRANSACTION_CATEGORIES } from '@/lib/enums'

const schema = z.object({
  category: z.enum(TRANSACTION_CATEGORIES),
  monthly_limit: z.string().min(1, 'Required'),
  is_discretionary: z.boolean(),
})

function BudgetDialog({ clientId }: { clientId: number }) {
  const [open, setOpen] = React.useState(false)
  const createBudget = useCreateBudget(clientId)

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { category: 'other', monthly_limit: '', is_discretionary: true },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await createBudget.mutateAsync(values)
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Add budget</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add budget</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {TRANSACTION_CATEGORIES.map((category) => (
                        <SelectItem key={category} value={category}>
                          {category.replace(/_/g, ' ')}
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
              name="monthly_limit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Monthly limit</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="is_discretionary"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center gap-2">
                  <FormControl>
                    <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                  <FormLabel className="font-normal">Discretionary spending</FormLabel>
                </FormItem>
              )}
            />
            {createBudget.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {createBudget.error instanceof ApiError
                    ? createBudget.error.message
                    : 'Something went wrong.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={createBudget.isPending}>
                {createBudget.isPending ? 'Saving…' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export function BudgetsSection({ clientId }: { clientId: number }) {
  const { data: budgets, isLoading } = useBudgets(clientId)
  const deleteBudget = useDeleteBudget(clientId)

  const columns: ColumnDef<Budget>[] = [
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'monthly_limit',
      header: 'Monthly limit',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      accessorKey: 'is_discretionary',
      header: 'Discretionary',
      cell: ({ getValue }) => ((getValue() as boolean) ? 'Yes' : 'No'),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button variant="ghost" size="icon" onClick={() => deleteBudget.mutate(row.original.id)}>
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Budgets</CardTitle>
        <BudgetDialog clientId={clientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable columns={columns} data={budgets ?? []} emptyMessage="No budgets set." />
        )}
      </CardContent>
    </Card>
  )
}
