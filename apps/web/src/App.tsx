import { Navigate, Route, Routes } from 'react-router-dom'

import { AdvisorAppLayout } from '@/layouts/AdvisorAppLayout'
import { PublicLayout } from '@/layouts/PublicLayout'
import { AdvisorSetupPage } from '@/features/advisors/AdvisorSetupPage'
import { ClientsListPage } from '@/features/clients/ClientsListPage'
import { ClientDetailPage } from '@/features/clients/ClientDetailPage'
import { TrackedFundsPage } from '@/features/trackedFunds/TrackedFundsPage'
import { RiskQuestionnairePublicPage } from '@/features/riskQuestionnaire/RiskQuestionnairePublicPage'

function App() {
  return (
    <Routes>
      <Route path="/advisors/setup" element={<AdvisorSetupPage />} />

      <Route element={<AdvisorAppLayout />}>
        <Route path="/" element={<Navigate to="/clients" replace />} />
        <Route path="/clients" element={<ClientsListPage />} />
        <Route path="/clients/:clientId" element={<ClientDetailPage />} />
        <Route path="/tracked-funds" element={<TrackedFundsPage />} />
      </Route>

      <Route element={<PublicLayout />}>
        <Route
          path="/risk-questionnaire/:token"
          element={<RiskQuestionnairePublicPage />}
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
