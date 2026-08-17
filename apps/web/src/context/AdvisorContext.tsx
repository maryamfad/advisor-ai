import * as React from 'react'

const STORAGE_KEY = 'advisor-ai.advisor-id'

type AdvisorContextValue = {
  advisorId: number | null
  setAdvisorId: (id: number | null) => void
}

const AdvisorContext = React.createContext<AdvisorContextValue | null>(null)

function readStoredAdvisorId(): number | null {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : null
}

export function AdvisorProvider({ children }: { children: React.ReactNode }) {
  const [advisorId, setAdvisorIdState] = React.useState<number | null>(
    readStoredAdvisorId
  )

  const setAdvisorId = React.useCallback((id: number | null) => {
    setAdvisorIdState(id)
    if (id === null) {
      window.localStorage.removeItem(STORAGE_KEY)
    } else {
      window.localStorage.setItem(STORAGE_KEY, String(id))
    }
  }, [])

  const value = React.useMemo(
    () => ({ advisorId, setAdvisorId }),
    [advisorId, setAdvisorId]
  )

  return <AdvisorContext.Provider value={value}>{children}</AdvisorContext.Provider>
}

export function useAdvisor() {
  const context = React.useContext(AdvisorContext)
  if (!context) {
    throw new Error('useAdvisor must be used within an AdvisorProvider')
  }
  return context
}
