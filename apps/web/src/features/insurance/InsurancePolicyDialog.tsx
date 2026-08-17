import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import {
  useCreateInsurancePolicy,
  useUpdateInsurancePolicy,
  type InsurancePolicy,
} from '@/api/insurancePolicies'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatEnumLabel } from '@/lib/format'

const POLICY_TYPES = [
  'term_life',
  'whole_life',
  'disability',
  'critical_illness',
  'health',
  'auto',
  'home',
  'other',
] as const
const OWNERS = ['client', 'spouse'] as const
const PREMIUM_FREQUENCIES = ['monthly', 'quarterly', 'annually'] as const
const POLICY_STATUSES = ['active', 'lapsed', 'cancelled'] as const

const schema = z.object({
  policy_type: z.enum(POLICY_TYPES),
  insured_owner: z.enum(OWNERS),
  provider: z.string().min(1, 'Required'),
  policy_number: z.string().optional(),
  beneficiary: z.string().optional(),
  coverage_amount: z.string().optional(),
  premium: z.string().optional(),
  premium_frequency: z.enum(PREMIUM_FREQUENCIES).optional(),
  status: z.enum(POLICY_STATUSES),
})

export function InsurancePolicyDialog({
  clientId,
  policy,
  trigger,
}: {
  clientId: number
  policy?: InsurancePolicy
  trigger: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const createPolicy = useCreateInsurancePolicy(clientId)
  const updatePolicy = useUpdateInsurancePolicy(clientId, policy?.id ?? -1)
  const mutation = policy ? updatePolicy : createPolicy

  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: {
      policy_type: policy?.policy_type ?? 'term_life',
      insured_owner: policy?.insured_owner ?? 'client',
      provider: policy?.provider ?? '',
      policy_number: policy?.policy_number ?? '',
      beneficiary: policy?.beneficiary ?? '',
      coverage_amount: policy?.coverage_amount ?? '',
      premium: policy?.premium ?? '',
      premium_frequency: policy?.premium_frequency ?? undefined,
      status: policy?.status ?? 'active',
    },
  })

  async function onSubmit(values: z.infer<typeof schema>) {
    await mutation.mutateAsync({
      policy_type: values.policy_type,
      insured_owner: values.insured_owner,
      provider: values.provider,
      policy_number: values.policy_number || null,
      beneficiary: values.beneficiary || null,
      coverage_amount: values.coverage_amount || null,
      premium: values.premium || null,
      premium_frequency: values.premium_frequency ?? null,
      status: values.status,
    })
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{policy ? 'Edit policy' : 'Add policy'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="policy_type"
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
                        {POLICY_TYPES.map((type) => (
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
                name="insured_owner"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Insured</FormLabel>
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
                name="provider"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Provider</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="policy_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Policy number</FormLabel>
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
              name="beneficiary"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Beneficiary</FormLabel>
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
                name="coverage_amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Coverage</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="premium"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Premium</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="premium_frequency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Frequency</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="—" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {PREMIUM_FREQUENCIES.map((frequency) => (
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
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Status</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {POLICY_STATUSES.map((status) => (
                        <SelectItem key={status} value={status}>
                          {formatEnumLabel(status)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
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
