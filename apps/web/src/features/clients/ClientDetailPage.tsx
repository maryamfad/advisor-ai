import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

import { useClientById } from '@/api/clients'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OverviewTab } from '@/features/clients/OverviewTab'
import { HouseholdTab } from '@/features/household/HouseholdTab'
import { FinancesTab } from '@/features/finances/FinancesTab'
import { InsuranceTab } from '@/features/insurance/InsuranceTab'
import { FnaTab } from '@/features/fna/FnaTab'
import { AdviceTab } from '@/features/advice/AdviceTab'
import { RiskQuestionnaireTab } from '@/features/riskQuestionnaire/RiskQuestionnaireTab'
import { ComingSoonTab } from '@/features/clients/ComingSoonTab'

const TABS = [
  { value: 'overview', label: 'Overview' },
  { value: 'household', label: 'Household' },
  { value: 'finances', label: 'Finances' },
  { value: 'insurance', label: 'Insurance' },
  { value: 'fna', label: 'FNA' },
  { value: 'advice', label: 'Advice' },
  { value: 'risk', label: 'Risk Questionnaire' },
  { value: 'plan', label: 'Financial Plan' },
  { value: 'funds', label: 'Funds' },
  { value: 'assistant', label: 'Assistant' },
] as const

export function ClientDetailPage() {
  const { clientId } = useParams<{ clientId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const id = Number(clientId)

  const { data: client, isLoading, isError } = useClientById(id)

  const activeTab = searchParams.get('tab') ?? 'overview'

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }

  if (isError || !client) {
    return <p className="text-sm text-destructive">Couldn't load this client.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <Link
          to="/clients"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-4" />
          All clients
        </Link>
        <h1 className="text-2xl font-semibold">
          {client.first_name} {client.last_name}
        </h1>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) => setSearchParams({ tab: value })}
      >
        <TabsList>
          {TABS.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab client={client} />
        </TabsContent>
        <TabsContent value="household">
          <HouseholdTab clientId={id} />
        </TabsContent>
        <TabsContent value="finances">
          <FinancesTab clientId={id} />
        </TabsContent>
        <TabsContent value="insurance">
          <InsuranceTab clientId={id} />
        </TabsContent>
        <TabsContent value="fna">
          <FnaTab clientId={id} />
        </TabsContent>
        <TabsContent value="advice">
          <AdviceTab clientId={id} />
        </TabsContent>
        <TabsContent value="risk">
          <RiskQuestionnaireTab clientId={id} />
        </TabsContent>
        <TabsContent value="plan">
          <ComingSoonTab label="Financial plan" />
        </TabsContent>
        <TabsContent value="funds">
          <ComingSoonTab label="Funds" />
        </TabsContent>
        <TabsContent value="assistant">
          <ComingSoonTab label="AI assistant" />
        </TabsContent>
      </Tabs>
    </div>
  )
}
