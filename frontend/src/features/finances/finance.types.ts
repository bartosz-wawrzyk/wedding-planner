export type ExpenseCategory = 'FOOD' | 'ALCOHOL' | 'SERVICE' | 'ATTIRE' | 'ACCOMMODATION' | 'OTHER';
export type CalculationStrategy = 'FIXED' | 'PER_ADULT' | 'PER_CHILD' | 'PER_GUEST' | 'PER_INVITATION' | 'CUSTOM_MULTIPLIER';

export interface Payment {
  id: string;
  expense_id: string;
  amount: string;
  paid_by: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Expense {
  id: string;
  name: string;
  category: ExpenseCategory;
  is_included_in_wedding_total: boolean;
  calculation_strategy: CalculationStrategy;
  unit_price: string;
  custom_multiplier: string;
  payments: Payment[];
  calculated_total_cost: string;
  total_paid: string;
  remaining_balance: string;
}

export interface ExpensePayload {
  name: string;
  category: ExpenseCategory;
  is_included_in_wedding_total: boolean;
  calculation_strategy: CalculationStrategy;
  unit_price: number;
  custom_multiplier: number;
}

export interface PaymentPayload {
  expense_id: string;
  amount: number;
  paid_by: string;
  description: string;
}

export interface PaymentUpdatePayload {
  amount: number;
  paid_by: string;
  description: string;
}

export interface FinanceSummaryTotals {
  wedding_costs_total: string;
  couple_costs_total: string;
  fixed_costs_wedding: string;
  fixed_costs_couple: string;
  total_paid: string;
  total_remaining: string;
  by_category: Record<ExpenseCategory, string>;
}

export interface FinanceSummary {
  confirmed: FinanceSummaryTotals;
  pending: FinanceSummaryTotals;
  actual_total: FinanceSummaryTotals;
  breakdown: Array<{
    id: string;
    name: string;
    category: ExpenseCategory;
    strategy: CalculationStrategy;
    unit_price: string;
    calculated_cost: string;
    is_included_in_wedding: boolean;
  }>;
}

export const CATEGORY_LABELS: Record<ExpenseCategory, string> = {
  FOOD: 'Jedzenie',
  ALCOHOL: 'Alkohol',
  SERVICE: 'Usługi',
  ATTIRE: 'Ubiór',
  ACCOMMODATION: 'Zakwaterowanie',
  OTHER: 'Inne',
};

export const STRATEGY_LABELS: Record<CalculationStrategy, string> = {
  FIXED: 'Kwota stała',
  PER_ADULT: 'Za dorosłego',
  PER_CHILD: 'Za dziecko',
  PER_GUEST: 'Za gościa',
  PER_INVITATION: 'Za zaproszenie',
  CUSTOM_MULTIPLIER: 'Własny mnożnik',
};