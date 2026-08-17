import { useNavigate } from 'react-router-dom'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { useAdvisor as useAdvisorContext } from '@/context/AdvisorContext'
import { useAdvisors, useCreateAdvisor } from '@/api/advisors'
import { ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'

const createAdvisorSchema = z.object({
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  email: z.string().email('Enter a valid email'),
})

export function AdvisorSetupPage() {
  const navigate = useNavigate()
  const { setAdvisorId } = useAdvisorContext()
  const { data: advisors, isLoading } = useAdvisors()
  const createAdvisor = useCreateAdvisor()

  const form = useForm<z.infer<typeof createAdvisorSchema>>({
    resolver: zodResolver(createAdvisorSchema),
    defaultValues: { first_name: '', last_name: '', email: '' },
  })

  function selectAdvisor(id: string) {
    setAdvisorId(Number(id))
    navigate('/clients')
  }

  async function onSubmit(values: z.infer<typeof createAdvisorSchema>) {
    const advisor = await createAdvisor.mutateAsync(values)
    setAdvisorId(advisor.id)
    navigate('/clients')
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-6 px-4 py-10">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">AdvisorAI</h1>
        <p className="text-sm text-muted-foreground">
          Choose an advisor profile to continue, or create a new one.
        </p>
      </div>

      {advisors && advisors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Existing advisors</CardTitle>
            <CardDescription>Pick a profile you've used before.</CardDescription>
          </CardHeader>
          <CardContent>
            <Select onValueChange={selectAdvisor} disabled={isLoading}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select an advisor" />
              </SelectTrigger>
              <SelectContent>
                {advisors.map((advisor) => (
                  <SelectItem key={advisor.id} value={String(advisor.id)}>
                    {advisor.first_name} {advisor.last_name} ({advisor.email})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>New advisor</CardTitle>
          <CardDescription>
            No real authentication yet -- this stands in for it during development.
          </CardDescription>
        </CardHeader>
        <CardContent>
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
              {createAdvisor.isError && (
                <Alert variant="destructive">
                  <AlertDescription>
                    {createAdvisor.error instanceof ApiError
                      ? createAdvisor.error.message
                      : 'Something went wrong.'}
                  </AlertDescription>
                </Alert>
              )}
              <Button type="submit" disabled={createAdvisor.isPending}>
                {createAdvisor.isPending ? 'Creating…' : 'Create advisor'}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
