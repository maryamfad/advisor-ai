import * as React from 'react'
import { Line, LineChart, CartesianGrid, Legend, XAxis, YAxis } from 'recharts'
import { X } from 'lucide-react'

import {
  useTrackedFunds,
  useClientTrackedFunds,
  useSelectTrackedFundForClient,
  useUnselectTrackedFundForClient,
  useFundPerformance,
} from '@/api/trackedFunds'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegendContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { formatDate } from '@/lib/format'

const LINE_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
]

export function FundsTab({ clientId }: { clientId: number }) {
  const { data: catalog } = useTrackedFunds()
  const { data: selections, isLoading: loadingSelections } = useClientTrackedFunds(clientId)
  const selectFund = useSelectTrackedFundForClient(clientId)
  const unselectFund = useUnselectTrackedFundForClient(clientId)
  const { data: performance, isLoading: loadingPerformance } = useFundPerformance(clientId)
  const [pendingFundId, setPendingFundId] = React.useState<string>('')

  const selectedFundIds = new Set(selections?.map((s) => s.tracked_fund_id))
  const availableFunds = (catalog ?? []).filter((fund) => !selectedFundIds.has(fund.id))

  const chartConfig: ChartConfig = {}
  const chartData: Record<string, string | number>[] = []
  if (performance) {
    performance.symbols.forEach((symbol, index) => {
      chartConfig[symbol] = { label: symbol, color: LINE_COLORS[index % LINE_COLORS.length] }
    })
    performance.dates.forEach((date, dateIndex) => {
      const row: Record<string, string | number> = { date }
      performance.symbols.forEach((symbol) => {
        row[symbol] = Number(performance.series[symbol]?.[dateIndex] ?? 0)
      })
      chartData.push(row)
    })
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Funds tracked for this client</CardTitle>
          <div className="flex items-center gap-2">
            <Select value={pendingFundId} onValueChange={setPendingFundId}>
              <SelectTrigger className="w-56">
                <SelectValue placeholder="Select a fund to add" />
              </SelectTrigger>
              <SelectContent>
                {availableFunds.map((fund) => (
                  <SelectItem key={fund.id} value={String(fund.id)}>
                    {fund.symbol} -- {fund.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              size="sm"
              disabled={!pendingFundId || selectFund.isPending}
              onClick={() => {
                selectFund.mutate(Number(pendingFundId))
                setPendingFundId('')
              }}
            >
              Add
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loadingSelections ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : !selections || selections.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No funds selected yet. Add one from the advisor's catalog above.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {selections.map((selection) => (
                <Badge key={selection.id} variant="secondary" className="gap-1 py-1 pr-1">
                  {selection.tracked_fund.symbol}
                  <button
                    type="button"
                    onClick={() => unselectFund.mutate(selection.tracked_fund_id)}
                    className="ml-1 rounded-full hover:bg-background/50"
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Performance comparison (% return, last 90 days)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {performance?.warnings.map((warning) => (
            <Alert key={warning} variant="warning">
              <AlertDescription>{warning}</AlertDescription>
            </Alert>
          ))}

          {loadingPerformance ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : chartData.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No price data to chart yet -- add a fund above.
            </p>
          ) : (
            <ChartContainer config={chartConfig} className="h-80 w-full">
              <LineChart data={chartData}>
                <CartesianGrid vertical={false} />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value: string) => formatDate(value)}
                  tickLine={false}
                  axisLine={false}
                  minTickGap={32}
                />
                <YAxis
                  tickFormatter={(value: number) => `${value}%`}
                  tickLine={false}
                  axisLine={false}
                  width={48}
                />
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      labelFormatter={(value) => formatDate(String(value))}
                      formatter={(value) => `${value}%`}
                    />
                  }
                />
                {performance?.symbols.map((symbol, index) => (
                  <Line
                    key={symbol}
                    type="monotone"
                    dataKey={symbol}
                    stroke={LINE_COLORS[index % LINE_COLORS.length]}
                    dot={false}
                    strokeWidth={2}
                  />
                ))}
                <Legend content={<ChartLegendContent className="justify-start" />} />
              </LineChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
