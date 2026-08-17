/** Backend enum value lists, kept here (rather than re-declared per
 * component) since TransactionDialog and BudgetsSection both need the
 * same TransactionCategory options. */
export const TRANSACTION_CATEGORIES = [
  'income',
  'housing',
  'utilities',
  'groceries',
  'dining',
  'transportation',
  'healthcare',
  'insurance',
  'entertainment',
  'savings_transfer',
  'debt_payment',
  'childcare',
  'subscriptions',
  'charitable_giving',
  'clothing',
  'personal_care',
  'alimony_child_support',
  'other',
] as const
