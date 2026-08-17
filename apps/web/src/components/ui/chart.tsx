import * as React from 'react'
import * as RechartsPrimitive from 'recharts'

import { cn } from '@/lib/utils'

export type ChartConfig = Record<
  string,
  {
    label: React.ReactNode
    color?: string
  }
>

type ChartContextProps = {
  config: ChartConfig
}

const ChartContext = React.createContext<ChartContextProps | null>(null)

function useChart() {
  const context = React.useContext(ChartContext)
  if (!context) {
    throw new Error('useChart must be used within a <ChartContainer>')
  }
  return context
}

function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}: React.ComponentProps<'div'> & {
  config: ChartConfig
  children: React.ComponentProps<
    typeof RechartsPrimitive.ResponsiveContainer
  >['children']
}) {
  const uniqueId = React.useId()
  const chartId = `chart-${id ?? uniqueId.replace(/:/g, '')}`

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-slot="chart"
        data-chart={chartId}
        className={cn(
          "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-hidden [&_.recharts-sector]:outline-hidden [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-surface]:outline-hidden",
          className
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  )
}

function ChartStyle({ id, config }: { id: string; config: ChartConfig }) {
  const colorConfig = Object.entries(config).filter(([, cfg]) => cfg.color)

  if (!colorConfig.length) {
    return null
  }

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `[data-chart=${id}] {\n${colorConfig
          .map(([key, cfg]) => `  --color-${key}: ${cfg.color};`)
          .join('\n')}\n}`,
      }}
    />
  )
}

const ChartTooltip = RechartsPrimitive.Tooltip

type ChartTooltipPayloadItem = {
  dataKey?: string | number
  name?: string | number
  value?: string | number | Array<string | number>
  color?: string
  payload?: unknown
}

function ChartTooltipContent({
  active,
  payload,
  label,
  className,
  formatter,
  labelFormatter,
}: {
  active?: boolean
  payload?: ChartTooltipPayloadItem[]
  label?: string | number
  className?: string
  formatter?: (
    value: ChartTooltipPayloadItem['value'],
    name: ChartTooltipPayloadItem['name'],
    item: ChartTooltipPayloadItem,
    index: number,
    payload: unknown
  ) => React.ReactNode
  labelFormatter?: (label: string | number, payload: ChartTooltipPayloadItem[]) => React.ReactNode
}) {
  const { config } = useChart()

  if (!active || !payload?.length) {
    return null
  }

  return (
    <div
      className={cn(
        'grid min-w-[10rem] items-start gap-1.5 rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl',
        className
      )}
    >
      {label != null && (
        <div className="font-medium">
          {labelFormatter ? labelFormatter(label, payload) : label}
        </div>
      )}
      <div className="grid gap-1.5">
        {payload.map((item, index: number) => {
          const key = String(item.dataKey ?? item.name ?? 'value')
          const itemConfig = config[key]
          const color = item.color

          return (
            <div
              key={item.dataKey ?? index}
              className="flex w-full items-center gap-2"
            >
              <span
                className="size-2.5 shrink-0 rounded-[2px]"
                style={{ backgroundColor: color }}
              />
              <div className="flex flex-1 items-center justify-between gap-2 leading-none">
                <span className="text-muted-foreground">
                  {itemConfig?.label ?? item.name}
                </span>
                <span className="font-mono font-medium tabular-nums text-foreground">
                  {formatter
                    ? formatter(item.value, item.name, item, index, item.payload)
                    : item.value}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ChartLegendContent({ className }: { className?: string }) {
  const { config } = useChart()

  return (
    <div className={cn('flex flex-wrap items-center justify-center gap-4', className)}>
      {Object.entries(config).map(([key, cfg]) => (
        <div key={key} className="flex items-center gap-1.5">
          <span
            className="size-2.5 shrink-0 rounded-[2px]"
            style={{ backgroundColor: cfg.color }}
          />
          {cfg.label}
        </div>
      ))}
    </div>
  )
}

export { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegendContent, useChart }
