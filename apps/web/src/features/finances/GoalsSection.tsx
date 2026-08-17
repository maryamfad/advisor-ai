import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Trash2 } from 'lucide-react'
import { z } from 'zod'

import { useGoals, useCreateGoal, useDeleteGoal, type Goal } from '@/api/goals'
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
import { formatCurrencyPrecise, formatDate, formatEnumLabel } from '@/lib/format'

const GOAL_TYPES = [
  'emergency_fund',
  'retirement',
  'home_purchase',
  'education',
  'debt_payoff',
  'other',
] as const

const schema = z.object({
  name: z.string().min(1, 'Required'),
  goal_type: z.enum(GOAL_TYPES),
  target_amount: z.string().min(1, 'Required'),
  current_amount: z.string().optional(),
  monthly_contribution: z.string().optional(),
  target_date: z.string().optional(),
})

function GoalDialog({ clientId }: { clientId: number }) {
  const [open, setOpen] = React.useState(false)
  const createGoal = useCreateGoal(clientId)

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      goal_type: 'other',
      target_amount: '',
      current_amount: '0',
      monthly_contribution: '',
      target_date: '',
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await createGoal.mutateAsync({
      name: values.name,
      goal_type: values.goal_type,
      target_amount: values.target_amount,
      current_amount: values.current_amount || '0',
      monthly_contribution: values.monthly_contribution || null,
      target_date: values.target_date || null,
      status: 'active',
    })
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Add goal</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add goal</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="goal_type"
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
                        {GOAL_TYPES.map((type) => (
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
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="target_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Target amount</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="current_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current amount</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="monthly_contribution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monthly contribution</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="target_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Target date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            {createGoal.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {createGoal.error instanceof ApiError
                    ? createGoal.error.message
                    : 'Something went wrong.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={createGoal.isPending}>
                {createGoal.isPending ? 'Saving…' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export function GoalsSection({ clientId }: { clientId: number }) {
  const { data: goals, isLoading } = useGoals(clientId)
  const deleteGoal = useDeleteGoal(clientId)

  const columns: ColumnDef<Goal>[] = [
    { accessorKey: 'name', header: 'Name' },
    {
      accessorKey: 'goal_type',
      header: 'Type',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'current_amount',
      header: 'Current',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      accessorKey: 'target_amount',
      header: 'Target',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      accessorKey: 'target_date',
      header: 'Target date',
      cell: ({ getValue }) => formatDate(getValue() as string | null),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button variant="ghost" size="icon" onClick={() => deleteGoal.mutate(row.original.id)}>
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Goals</CardTitle>
        <GoalDialog clientId={clientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable columns={columns} data={goals ?? []} emptyMessage="No goals yet." />
        )}
      </CardContent>
    </Card>
  )
}
