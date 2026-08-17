import type { Client } from '@/api/clients'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatDate, formatEnumLabel } from '@/lib/format'
import { ClientEditDialog } from '@/features/clients/ClientEditDialog'

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-medium">{value ?? '—'}</div>
    </div>
  )
}

export function OverviewTab({ client }: { client: Client }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Client details</CardTitle>
        <ClientEditDialog client={client} />
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Field label="Email" value={client.email} />
        <Field label="Phone" value={client.phone} />
        <Field label="Date of birth" value={formatDate(client.date_of_birth)} />
        <Field label="Marital status" value={formatEnumLabel(client.marital_status)} />
        <Field
          label="First-time home buyer"
          value={client.first_time_home_buyer ? 'Yes' : 'No'}
        />
        <Field label="Retirement age" value={client.retirement_age} />
        <Field label="Life expectancy" value={client.life_expectancy_age} />
        <Field
          label="Desired retirement income"
          value={
            client.desired_retirement_monthly_income
              ? `${formatCurrency(client.desired_retirement_monthly_income)}/mo`
              : null
          }
        />
        <Field label="Client since" value={formatDate(client.created_at)} />
      </CardContent>
    </Card>
  )
}
