import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import {
  useCreateFinancialNeedsAnalysis,
  useUpdateFinancialNeedsAnalysis,
  type FinancialNeedsAnalysis,
} from '@/api/financialNeedsAnalyses'
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
import { Textarea } from '@/components/ui/textarea'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { formatEnumLabel } from '@/lib/format'

const INVESTOR_RATINGS = ['excellent', 'good', 'fair', 'poor'] as const
const RISK_TOLERANCES = ['low', 'low_medium', 'medium', 'medium_high', 'high'] as const

const schema = z.object({
  conducted_at: z.string().min(1, 'Required'),
  has_monthly_budget: z.boolean(),
  has_regular_savings_plan: z.boolean(),
  monthly_savings_capacity: z.string().optional(),
  biggest_financial_concern: z.string().optional(),
  notes: z.string().optional(),
  investment_knowledge: z.enum(INVESTOR_RATINGS).optional(),
  risk_tolerance: z.enum(RISK_TOLERANCES).optional(),
  investment_experience: z.enum(INVESTOR_RATINGS).optional(),
  wants_debt_payoff: z.boolean(),
  wants_income_replacement: z.boolean(),
  income_replacement_amount: z.string().optional(),
  income_replacement_years: z.string().optional(),
  wants_mortgage_payoff: z.boolean(),
  wants_education_funding: z.boolean(),
  education_funding_amount: z.string().optional(),
  wants_final_expenses: z.boolean(),
  final_expenses_amount: z.string().optional(),
  wants_emergency_fund: z.boolean(),
  emergency_fund_months: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

function defaultsFrom(fna?: FinancialNeedsAnalysis): FormValues {
  return {
    conducted_at: fna?.conducted_at ?? new Date().toISOString().slice(0, 10),
    has_monthly_budget: fna?.has_monthly_budget ?? false,
    has_regular_savings_plan: fna?.has_regular_savings_plan ?? false,
    monthly_savings_capacity: fna?.monthly_savings_capacity ?? '',
    biggest_financial_concern: fna?.biggest_financial_concern ?? '',
    notes: fna?.notes ?? '',
    investment_knowledge: fna?.investment_knowledge ?? undefined,
    risk_tolerance: fna?.risk_tolerance ?? undefined,
    investment_experience: fna?.investment_experience ?? undefined,
    wants_debt_payoff: fna?.wants_debt_payoff ?? false,
    wants_income_replacement: fna?.wants_income_replacement ?? false,
    income_replacement_amount: fna?.income_replacement_amount ?? '',
    income_replacement_years: fna?.income_replacement_years?.toString() ?? '',
    wants_mortgage_payoff: fna?.wants_mortgage_payoff ?? false,
    wants_education_funding: fna?.wants_education_funding ?? false,
    education_funding_amount: fna?.education_funding_amount ?? '',
    wants_final_expenses: fna?.wants_final_expenses ?? false,
    final_expenses_amount: fna?.final_expenses_amount ?? '',
    wants_emergency_fund: fna?.wants_emergency_fund ?? false,
    emergency_fund_months: fna?.emergency_fund_months?.toString() ?? '',
  }
}

export function FnaDialog({
  clientId,
  fna,
  trigger,
}: {
  clientId: number
  fna?: FinancialNeedsAnalysis
  trigger: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const createFna = useCreateFinancialNeedsAnalysis(clientId)
  const updateFna = useUpdateFinancialNeedsAnalysis(clientId, fna?.id ?? -1)
  const mutation = fna ? updateFna : createFna

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultsFrom(fna),
  })

  async function onSubmit(values: FormValues) {
    await mutation.mutateAsync({
      conducted_at: values.conducted_at,
      has_monthly_budget: values.has_monthly_budget,
      has_regular_savings_plan: values.has_regular_savings_plan,
      monthly_savings_capacity: values.monthly_savings_capacity || null,
      biggest_financial_concern: values.biggest_financial_concern || null,
      notes: values.notes || null,
      investment_knowledge: values.investment_knowledge ?? null,
      risk_tolerance: values.risk_tolerance ?? null,
      investment_experience: values.investment_experience ?? null,
      wants_debt_payoff: values.wants_debt_payoff,
      wants_income_replacement: values.wants_income_replacement,
      income_replacement_amount: values.income_replacement_amount || null,
      income_replacement_years: values.income_replacement_years
        ? Number(values.income_replacement_years)
        : null,
      wants_mortgage_payoff: values.wants_mortgage_payoff,
      wants_education_funding: values.wants_education_funding,
      education_funding_amount: values.education_funding_amount || null,
      wants_final_expenses: values.wants_final_expenses,
      final_expenses_amount: values.final_expenses_amount || null,
      wants_emergency_fund: values.wants_emergency_fund,
      emergency_fund_months: values.emergency_fund_months
        ? Number(values.emergency_fund_months)
        : null,
    })
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{fna ? 'Edit assessment' : 'New financial needs assessment'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4">
            <FormField
              control={form.control}
              name="conducted_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Conducted on</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Separator />
            <p className="text-sm font-medium">Cash flow habits</p>
            <div className="flex gap-6">
              <FormField
                control={form.control}
                name="has_monthly_budget"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center gap-2">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel className="font-normal">Has a monthly budget</FormLabel>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="has_regular_savings_plan"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center gap-2">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel className="font-normal">Regular savings plan</FormLabel>
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="monthly_savings_capacity"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Monthly savings capacity</FormLabel>
                    <FormControl>
                      <Input type="number" step="0.01" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="biggest_financial_concern"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Biggest financial concern</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />
            <p className="text-sm font-medium">Investor profile</p>
            <div className="grid grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="investment_knowledge"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Knowledge</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="—" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {INVESTOR_RATINGS.map((rating) => (
                          <SelectItem key={rating} value={rating}>
                            {formatEnumLabel(rating)}
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
                name="investment_experience"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Experience</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="—" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {INVESTOR_RATINGS.map((rating) => (
                          <SelectItem key={rating} value={rating}>
                            {formatEnumLabel(rating)}
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
                name="risk_tolerance"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Risk tolerance</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="—" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {RISK_TOLERANCES.map((tolerance) => (
                          <SelectItem key={tolerance} value={tolerance}>
                            {formatEnumLabel(tolerance)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />
            <p className="text-sm font-medium">Needs checklist (DIME)</p>
            <div className="grid gap-3">
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_debt_payoff"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Debt payoff</FormLabel>
                    </FormItem>
                  )}
                />
              </div>
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_income_replacement"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Income replacement</FormLabel>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="income_replacement_amount"
                  render={({ field }) => (
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="Amount" {...field} />
                    </FormControl>
                  )}
                />
                <FormField
                  control={form.control}
                  name="income_replacement_years"
                  render={({ field }) => (
                    <FormControl>
                      <Input type="number" placeholder="Years" {...field} />
                    </FormControl>
                  )}
                />
              </div>
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_mortgage_payoff"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Mortgage payoff</FormLabel>
                    </FormItem>
                  )}
                />
              </div>
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_education_funding"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Education funding</FormLabel>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="education_funding_amount"
                  render={({ field }) => (
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="Amount" {...field} />
                    </FormControl>
                  )}
                />
              </div>
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_final_expenses"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Final expenses</FormLabel>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="final_expenses_amount"
                  render={({ field }) => (
                    <FormControl>
                      <Input type="number" step="0.01" placeholder="Amount" {...field} />
                    </FormControl>
                  )}
                />
              </div>
              <div className="flex items-center gap-3">
                <FormField
                  control={form.control}
                  name="wants_emergency_fund"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-2">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <FormLabel className="w-40 font-normal">Emergency fund</FormLabel>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="emergency_fund_months"
                  render={({ field }) => (
                    <FormControl>
                      <Input type="number" placeholder="Months" {...field} />
                    </FormControl>
                  )}
                />
              </div>
            </div>

            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Notes</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
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
