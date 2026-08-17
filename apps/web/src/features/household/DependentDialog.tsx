import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import {
  useCreateDependent,
  useUpdateDependent,
  type Dependent,
} from '@/api/dependents'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
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
import { Alert, AlertDescription } from '@/components/ui/alert'

const schema = z.object({
  name: z.string().min(1, 'Required'),
  date_of_birth: z.string().optional(),
  years_of_education_remaining: z.string().optional(),
})

export function DependentDialog({
  clientId,
  dependent,
  trigger,
}: {
  clientId: number
  dependent?: Dependent
  trigger: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const createDependent = useCreateDependent(clientId)
  const updateDependent = useUpdateDependent(clientId, dependent?.id ?? -1)
  const mutation = dependent ? updateDependent : createDependent

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: dependent?.name ?? '',
      date_of_birth: dependent?.date_of_birth ?? '',
      years_of_education_remaining:
        dependent?.years_of_education_remaining?.toString() ?? '',
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await mutation.mutateAsync({
      name: values.name,
      date_of_birth: values.date_of_birth || null,
      years_of_education_remaining: values.years_of_education_remaining
        ? Number(values.years_of_education_remaining)
        : null,
    })
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{dependent ? 'Edit dependent' : 'Add dependent'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
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
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="date_of_birth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date of birth</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="years_of_education_remaining"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Years of education left</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            {mutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {mutation.error instanceof ApiError
                    ? mutation.error.message
                    : 'Something went wrong.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Saving…' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
