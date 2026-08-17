const currencyFormatter = new Intl.NumberFormat('en-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 0,
})

const currencyFormatterPrecise = new Intl.NumberFormat('en-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 2,
})

const percentFormatter = new Intl.NumberFormat('en-CA', {
  style: 'percent',
  maximumFractionDigits: 1,
})

const dateFormatter = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

const dateTimeFormatter = new Intl.DateTimeFormat('en-CA', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

/** Every dollar amount the API returns is a Decimal serialized as a
 * string, so parsing is required before any Intl.NumberFormat call. */
function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined) return 0
  return typeof value === 'number' ? value : parseFloat(value)
}

export function formatCurrency(value: string | number | null | undefined): string {
  return currencyFormatter.format(toNumber(value))
}

export function formatCurrencyPrecise(
  value: string | number | null | undefined
): string {
  return currencyFormatterPrecise.format(toNumber(value))
}

/** `value` is a plain ratio (0.25), not a whole percent (25). */
export function formatPercent(value: string | number | null | undefined): string {
  return percentFormatter.format(toNumber(value))
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  return dateFormatter.format(new Date(value))
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  return dateTimeFormatter.format(new Date(value))
}

/** Converts SNAKE_CASE or snake_case enum values into "Title Case" for
 * display, e.g. "FIRST_TIME_HOME_BUYER" -> "First Time Home Buyer". */
export function formatEnumLabel(value: string | null | undefined): string {
  if (!value) return '—'
  return value
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
