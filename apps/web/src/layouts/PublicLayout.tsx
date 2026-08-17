import { Outlet } from 'react-router-dom'

/** Wraps only unauthenticated, client-facing routes (e.g. the risk
 * questionnaire link) -- no sidebar, no advisor auth of any kind. */
export function PublicLayout() {
  return (
    <div className="min-h-svh bg-muted/30">
      <div className="mx-auto max-w-2xl px-4 py-10">
        <Outlet />
      </div>
    </div>
  )
}
