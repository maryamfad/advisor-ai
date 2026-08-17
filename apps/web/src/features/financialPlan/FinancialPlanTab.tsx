import * as React from 'react'
import { CheckCircle2, Circle, CircleDashed } from 'lucide-react'

import {
  useFinancialPlans,
  useGenerateFinancialPlan,
  useUpdateActionItemStatus,
  type ActionItemStatus,
  type FinancialPlanActionItem,
} from '@/api/financialPlans'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { formatCurrency, formatDateTime, formatEnumLabel } from '@/lib/format'

const STATUS_OPTIONS: ActionItemStatus[] = ['not_started', 'in_progress', 'done']

const STATUS_ICON: Record<ActionItemStatus, React.ReactNode> = {
  not_started: <Circle className="size-4 text-muted-foreground" />,
  in_progress: <CircleDashed className="size-4 text-warning" />,
  done: <CheckCircle2 className="size-4 text-success" />,
}

function ActionItemRow({
  item,
  onStatusChange,
}: {
  item: FinancialPlanActionItem
  onStatusChange: (status: ActionItemStatus) => void
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b py-3 last:border-b-0">
      <div className="flex items-start gap-3">
        {STATUS_ICON[item.status]}
        <div>
          <div className="text-sm font-medium">{item.title}</div>
          <div className="text-sm text-muted-foreground">{item.description}</div>
          <div className="mt-1 flex gap-2 text-xs text-muted-foreground">
            <span>{formatEnumLabel(item.category)}</span>
            {item.target_amount && <span>· Target: {formatCurrency(item.target_amount)}</span>}
          </div>
        </div>
      </div>
      <Select value={item.status} onValueChange={(value) => onStatusChange(value as ActionItemStatus)}>
        <SelectTrigger className="w-36">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((status) => (
            <SelectItem key={status} value={status}>
              {formatEnumLabel(status)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export function FinancialPlanTab({ clientId }: { clientId: number }) {
  const { data: plans, isLoading } = useFinancialPlans(clientId)
  const generatePlan = useGenerateFinancialPlan(clientId)
  const [selectedPlanId, setSelectedPlanId] = React.useState<number | null>(null)

  const sorted = React.useMemo(
    () => [...(plans ?? [])].sort((a, b) => b.generated_at.localeCompare(a.generated_at)),
    [plans]
  )
  const selectedPlan = sorted.find((plan) => plan.id === selectedPlanId) ?? sorted[0]
  const updateStatus = useUpdateActionItemStatus(clientId, selectedPlan?.id ?? -1)

  const sortedItems = React.useMemo(
    () => [...(selectedPlan?.action_items ?? [])].sort((a, b) => a.priority - b.priority),
    [selectedPlan]
  )

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Financial plan</CardTitle>
          <Button onClick={() => generatePlan.mutate()} disabled={generatePlan.isPending}>
            {generatePlan.isPending ? 'Generating…' : 'Generate new plan'}
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : sorted.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No plan generated yet. Generate one to get a prioritized action-item checklist.
            </p>
          ) : (
            <div className="flex flex-col gap-4">
              {sorted.length > 1 && (
                <Select
                  value={String(selectedPlan?.id)}
                  onValueChange={(value) => setSelectedPlanId(Number(value))}
                >
                  <SelectTrigger className="w-64">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sorted.map((plan) => (
                      <SelectItem key={plan.id} value={String(plan.id)}>
                        Generated {formatDateTime(plan.generated_at)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {selectedPlan?.narrative_summary && (
                <p className="rounded-md bg-muted p-3 text-sm">
                  {selectedPlan.narrative_summary}
                </p>
              )}

              <div>
                {sortedItems.map((item) => (
                  <ActionItemRow
                    key={item.id}
                    item={item}
                    onStatusChange={(status) => updateStatus.mutate({ itemId: item.id, status })}
                  />
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
