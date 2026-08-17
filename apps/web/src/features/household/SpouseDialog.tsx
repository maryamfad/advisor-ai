import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { useCreateSpouse, useUpdateSpouse, type Spouse } from '@/api/spouse'
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
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  date_of_birth: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  employer: z.string().optional(),
  retirement_age: z.string().optional(),
  life_expectancy_age: z.string().optional(),
})

export function SpouseDialog({
  clientId,
  spouse,
  trigger,
}: {
  clientId: number
  spouse?: Spouse
  trigger: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const createSpouse = useCreateSpouse(clientId)
  const updateSpouse = useUpdateSpouse(clientId)
  const mutation = spouse ? updateSpouse : createSpouse

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      first_name: spouse?.first_name ?? '',
      last_name: spouse?.last_name ?? '',
      date_of_birth: spouse?.date_of_birth ?? '',
      email: spouse?.email ?? '',
      phone: spouse?.phone ?? '',
      employer: spouse?.employer ?? '',
      retirement_age: spouse?.retirement_age?.toString() ?? '',
      life_expectancy_age: spouse?.life_expectancy_age?.toString() ?? '',
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await mutation.mutateAsync({
      first_name: values.first_name,
      last_name: values.last_name,
      date_of_birth: values.date_of_birth || null,
      email: values.email || null,
      phone: values.phone || null,
      employer: values.employer || null,
      retirement_age: values.retirement_age ? Number(values.retirement_age) : null,
      life_expectancy_age: values.life_expectancy_age
        ? Number(values.life_expectancy_age)
        : null,
    })
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{spouse ? 'Edit spouse' : 'Add spouse'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>First name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
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
                name="employer"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Employer</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="retirement_age"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Retirement age</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="life_expectancy_age"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Life expectancy</FormLabel>
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
