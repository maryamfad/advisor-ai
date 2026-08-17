export function ComingSoonTab({ label }: { label: string }) {
  return (
    <div className="flex h-40 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
      {label} coming soon.
    </div>
  )
}
