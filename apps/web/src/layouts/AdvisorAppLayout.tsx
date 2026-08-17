import { Navigate, NavLink, Outlet } from 'react-router-dom'
import { LineChart, Users } from 'lucide-react'

import { useAdvisor } from '@/context/AdvisorContext'
import { useAdvisorById } from '@/api/advisors'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/clients', label: 'Clients', icon: Users },
  { to: '/tracked-funds', label: 'Tracked Funds', icon: LineChart },
]

export function AdvisorAppLayout() {
  const { advisorId, setAdvisorId } = useAdvisor()
  const { data: advisor } = useAdvisorById(advisorId)

  if (advisorId === null) {
    return <Navigate to="/advisors/setup" replace />
  }

  return (
    <div className="grid min-h-svh grid-cols-[16rem_1fr]">
      <aside className="flex flex-col gap-6 border-r bg-muted/20 p-4">
        <div className="px-2 text-lg font-semibold">AdvisorAI</div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-foreground/80 transition-colors hover:bg-accent hover:text-accent-foreground',
                  isActive && 'bg-accent text-accent-foreground'
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex flex-col">
        <header className="flex items-center justify-between border-b px-6 py-3">
          <div className="text-sm text-muted-foreground">
            {advisor ? (
              <>
                Signed in as{' '}
                <span className="font-medium text-foreground">
                  {advisor.first_name} {advisor.last_name}
                </span>
              </>
            ) : (
              'Loading advisor…'
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={() => setAdvisorId(null)}>
            Switch advisor
          </Button>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
