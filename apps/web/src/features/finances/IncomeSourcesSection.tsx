import * as React from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Trash2 } from 'lucide-react'
import { z } from 'zod'

import {
  useIncomeSources,
  useCreateIncomeSource,
  useDeleteIncomeSource,
  type IncomeSource,
} from '@/api/incomeSources'
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
import { formatCurrencyPrecise, formatEnumLabel } from '@/lib/format'

const OWNERS = ['client', 'spouse'] as const
const FREQUENCIES = ['weekly', 'biweekly', 'semi_monthly', 'monthly', 'annually'] as const

const schema = z.object({
  owner: z.enum(OWNERS),
  source: z.string().min(1, 'Required'),
  gross_amount: z.string().min(1, 'Required'),
  frequency: z.enum(FREQUENCIES),
  net_takehome: z.string().optional(),
  is_future: z.boolean(),
})

function IncomeSourceDialog({ clientId }: { clientId: number }) {
  const [open, setOpen] = React.useState(false)
  const createIncomeSource = useCreateIncomeSource(clientId)

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      owner: 'client',
      source: '',
      gross_amount: '',
      frequency: 'monthly',
      net_takehome: '',
      is_future: false,
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await createIncomeSource.mutateAsync({
      owner: values.owner,
      source: values.source,
      gross_amount: values.gross_amount,
      frequency: values.frequency,
      net_takehome: values.net_takehome || null,
      is_future: values.is_future,
    })
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">Add income</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add income source</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="source"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Source</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="owner"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Owner</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {OWNERS.map((owner) => (
                          <SelectItem key={owner} value={owner}>
                            {owner}
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
                name="gross_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Gross amount</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="frequency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Frequency</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {FREQUENCIES.map((frequency) => (
                          <SelectItem key={frequency} value={frequency}>
                            {formatEnumLabel(frequency)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="net_takehome"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Net take-home (optional)</FormLabel>
                  <FormControl>
                    <Input type="number" step="0.01" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {createIncomeSource.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {createIncomeSource.error instanceof ApiError
                    ? createIncomeSource.error.message
                    : 'Something went wrong.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={createIncomeSource.isPending}>
                {createIncomeSource.isPending ? 'Saving…' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export function IncomeSourcesSection({ clientId }: { clientId: number }) {
  const { data: incomeSources, isLoading } = useIncomeSources(clientId)
  const deleteIncomeSource = useDeleteIncomeSource(clientId)

  const columns: ColumnDef<IncomeSource>[] = [
    { accessorKey: 'source', header: 'Source' },
    {
      accessorKey: 'owner',
      header: 'Owner',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'gross_amount',
      header: 'Gross amount',
      cell: ({ getValue }) => formatCurrencyPrecise(getValue() as string),
    },
    {
      accessorKey: 'frequency',
      header: 'Frequency',
      cell: ({ getValue }) => formatEnumLabel(getValue() as string),
    },
    {
      accessorKey: 'is_future',
      header: 'Future',
      cell: ({ getValue }) => ((getValue() as boolean) ? 'Yes' : 'No'),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => deleteIncomeSource.mutate(row.original.id)}
        >
          <Trash2 className="size-4" />
        </Button>
      ),
    },
  ]

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Income sources</CardTitle>
        <IncomeSourceDialog clientId={clientId} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <DataTable
            columns={columns}
            data={incomeSources ?? []}
            emptyMessage="No income sources on file."
          />
        )}
      </CardContent>
    </Card>
  )
}
