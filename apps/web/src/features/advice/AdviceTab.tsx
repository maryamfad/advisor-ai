import { useClientAdvice } from '@/api/advice'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatEnumLabel, formatPercent } from '@/lib/format'

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-2xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  )
}

export function AdviceTab({ clientId }: { clientId: number }) {
  const { data: advice, isLoading, isError } = useClientAdvice(clientId)

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  if (isError || !advice) {
    return <p className="text-sm text-destructive">Couldn't load advice for this client.</p>
  }

  const { financial_summary, insurance, registered_accounts } = advice

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <StatTile label="Monthly income" value={formatCurrency(financial_summary.monthly_income)} />
        <StatTile
          label="Monthly expenses"
          value={formatCurrency(financial_summary.monthly_expenses)}
        />
        <StatTile
          label="Monthly cash flow"
          value={formatCurrency(financial_summary.monthly_cash_flow)}
        />
        <StatTile
          label="Savings rate"
          value={formatPercent(Number(financial_summary.savings_rate))}
        />
        <StatTile label="Net worth" value={formatCurrency(financial_summary.net_worth)} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Life insurance recommendation</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-muted-foreground">Recommended type</div>
              <div className="text-lg font-semibold">
                {formatEnumLabel(insurance.recommended_type)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Estimated need</div>
              <div className="text-lg font-semibold">
                {formatCurrency(insurance.estimated_coverage_need)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Coverage gap</div>
              <div className="text-lg font-semibold">
                {formatCurrency(insurance.coverage_gap)}
              </div>
            </div>
          </div>
          <div>
            <div className="mb-1 text-xs text-muted-foreground">Existing coverage</div>
            <div className="text-sm">{formatCurrency(insurance.existing_coverage)}</div>
          </div>
          {insurance.reasons.length > 0 && (
            <div>
              <div className="mb-1 text-xs text-muted-foreground">Reasons</div>
              <ul className="list-inside list-disc space-y-1 text-sm">
                {insurance.reasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Registered account priorities</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 sm:grid-cols-2">
          {registered_accounts.map((group) => (
            <div key={group.owner}>
              <h4 className="mb-2 text-sm font-medium">{formatEnumLabel(group.owner)}</h4>
              {group.recommendations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No recommendations.</p>
              ) : (
                <ol className="flex flex-col gap-3">
                  {[...group.recommendations]
                    .sort((a, b) => a.priority - b.priority)
                    .map((rec) => (
                      <li key={rec.account_type} className="flex gap-3">
                        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                          {rec.priority}
                        </span>
                        <div>
                          <div className="text-sm font-medium">
                            {rec.account_type.toUpperCase()}
                          </div>
                          <div className="text-sm text-muted-foreground">{rec.reason}</div>
                        </div>
                      </li>
                    ))}
                </ol>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
