import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AccountsSection } from '@/features/finances/AccountsSection'
import { IncomeSourcesSection } from '@/features/finances/IncomeSourcesSection'
import { BudgetsSection } from '@/features/finances/BudgetsSection'
import { GoalsSection } from '@/features/finances/GoalsSection'
import { DebtsSection } from '@/features/finances/DebtsSection'

export function FinancesTab({ clientId }: { clientId: number }) {
  return (
    <Tabs defaultValue="accounts">
      <TabsList>
        <TabsTrigger value="accounts">Accounts</TabsTrigger>
        <TabsTrigger value="income">Income</TabsTrigger>
        <TabsTrigger value="budgets">Budgets</TabsTrigger>
        <TabsTrigger value="goals">Goals</TabsTrigger>
        <TabsTrigger value="debts">Debts</TabsTrigger>
      </TabsList>
      <TabsContent value="accounts">
        <AccountsSection clientId={clientId} />
      </TabsContent>
      <TabsContent value="income">
        <IncomeSourcesSection clientId={clientId} />
      </TabsContent>
      <TabsContent value="budgets">
        <BudgetsSection clientId={clientId} />
      </TabsContent>
      <TabsContent value="goals">
        <GoalsSection clientId={clientId} />
      </TabsContent>
      <TabsContent value="debts">
        <DebtsSection clientId={clientId} />
      </TabsContent>
    </Tabs>
  )
}
