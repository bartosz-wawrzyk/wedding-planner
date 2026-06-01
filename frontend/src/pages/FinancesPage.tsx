import { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import api from '../api/axios';
import { useEventStore } from '../store/eventStore';
import PageTitle from '../components/common/PageTitle';
import type { Event } from '../features/events/event.types';
import {
  type Expense,
  type ExpensePayload,
  type FinanceSummary,
  type ExpenseCategory,
  type FinanceSummaryTotals,
  CATEGORY_LABELS,
  STRATEGY_LABELS
} from '../features/finances/finance.types';
import styles from './FinancesPage.module.css';

export default function FinancesPage() {
  const { activeEvent, setActiveEvent } = useEventStore();
  const [events, setEvents] = useState<Event[]>([]);
  const [showEventSelector, setShowEventSelector] = useState(false);
  
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<ExpenseCategory | 'ALL'>('ALL');
  
  const [activeSummaryTab, setActiveSummaryTab] = useState<'actual_total' | 'confirmed' | 'pending'>('actual_total');
  
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  
  const [editingExpenseId, setEditingExpenseId] = useState<string | null>(null);

  const expenseFormRef = useRef<HTMLDivElement>(null);

  const expenseForm = useForm<ExpensePayload>({
    defaultValues: {
      name: '',
      category: 'OTHER',
      is_included_in_wedding_total: true,
      calculation_strategy: 'FIXED',
      unit_price: 0,
      custom_multiplier: 0,
    },
  });

  const watchStrategy = expenseForm.watch('calculation_strategy');

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    if (activeEvent?.id) {
      loadFinanceData();
    }
  }, [activeEvent?.id]);

  const fetchEvents = async () => {
    try {
      const response = await api.get<Event[]>('/events');
      setEvents(response.data);
    } catch {
      setServerError('Nie udało się pobrać wydarzeń.');
    }
  };

  const loadFinanceData = async () => {
    if (!activeEvent?.id) return;
    try {
      setServerError(null);
      const summaryRes = await api.get<FinanceSummary>(`/events/${activeEvent.id}/finance/summary`);
      setSummary(summaryRes.data);

      const mappedExpenses: Expense[] = summaryRes.data.breakdown.map(item => ({
        id: item.id,
        name: item.name,
        category: item.category,
        is_included_in_wedding_total: item.is_included_in_wedding,
        calculation_strategy: item.strategy,
        unit_price: item.unit_price,
        custom_multiplier: "0",
        payments: [], 
        calculated_total_cost: item.calculated_cost,
        total_paid: "0", 
        remaining_balance: item.calculated_cost
      }));
      setExpenses(mappedExpenses);
    } catch (err: any) {
      setServerError('Błąd podczas ładowania danych finansowych z API.');
    }
  };

  const handleExpenseSubmit = async (data: ExpensePayload) => {
    if (!activeEvent?.id) return;
    try {
      if (editingExpenseId) {
        await api.patch(`/events/${activeEvent.id}/finance/expenses/${editingExpenseId}`, data);
        setSuccessMsg('Wydatek zaktualizowany.');
      } else {
        await api.post(`/events/${activeEvent.id}/finance/expenses`, data);
        setSuccessMsg('Nowy wydatek dodany.');
      }
      resetExpenseForm();
      await loadFinanceData();
    } catch (err: any) {
      setServerError(err.response?.data?.detail || 'Błąd zapisu wydatku.');
    }
  };

  const resetExpenseForm = () => {
    setEditingExpenseId(null);
    expenseForm.reset({
      name: '', category: 'OTHER', is_included_in_wedding_total: true,
      calculation_strategy: 'FIXED', unit_price: 0, custom_multiplier: 0,
    });
  };

  const startEditExpense = (expense: Expense) => {
    setEditingExpenseId(expense.id);
    expenseForm.setValue('name', expense.name);
    expenseForm.setValue('category', expense.category);
    expenseForm.setValue('is_included_in_wedding_total', expense.is_included_in_wedding_total);
    expenseForm.setValue('calculation_strategy', expense.calculation_strategy);
    expenseForm.setValue('unit_price', parseFloat(expense.unit_price) || 0);
    expenseFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const deleteExpense = async (id: string) => {
    if (!activeEvent?.id || !window.confirm('Usunąć ten wydatek?')) return;
    try {
      await api.delete(`/events/${activeEvent.id}/finance/expenses/${id}`);
      setSuccessMsg('Wydatek usunięty.');
      await loadFinanceData();
    } catch {
      setServerError('Błąd usuwania wydatku.');
    }
  };

  const filteredExpenses = selectedCategoryFilter === 'ALL' 
    ? expenses 
    : expenses.filter(e => e.category === selectedCategoryFilter);

  const renderSummaryMetrics = (totals: FinanceSummaryTotals, title: string) => {
    const isNegative = parseFloat(totals.total_remaining) < 0;
    
    return (
      <div className={styles.metricsContainer}>
        {/* Overall High-Level Metrics */}
        <div className={styles.metricsGrid}>
          <div className={styles.metricBlock}>
            <span className={styles.metricLabel}>Suma Zapłacona</span>
            <span className={`${styles.metricValue} ${styles.valPaid}`}>{totals.total_paid} zł</span>
          </div>
          <div className={styles.metricBlock}>
            <span className={styles.metricLabel}>Pozostało do spłaty</span>
            <span className={`${styles.metricValue} ${isNegative ? styles.valDanger : styles.valSuccess}`}>
              {totals.total_remaining} zł
            </span>
          </div>
        </div>

        {/* Financial Responsibility: The Wedding vs. the Bride and Groom */}
        <div className={styles.splitGrid}>
          <div className={styles.splitCard}>
            <h4>Koszty Wesela (Ogólne)</h4>
            <div className={styles.splitRow}>
              <span>Koszty razem:</span>
              <strong>{totals.wedding_costs_total} zł</strong>
            </div>
            <div className={styles.splitRow}>
              <span>W tym koszty stałe:</span>
              <span className={styles.textMuted}>{totals.fixed_costs_wedding} zł</span>
            </div>
          </div>

          <div className={styles.splitCard}>
            <h4>Koszty Pary Młodej</h4>
            <div className={styles.splitRow}>
              <span>Koszty razem:</span>
              <strong>{totals.couple_costs_total} zł</strong>
            </div>
            <div className={styles.splitRow}>
              <span>W tym koszty stałe:</span>
              <span className={styles.textMuted}>{totals.fixed_costs_couple} zł</span>
            </div>
          </div>
        </div>

        {/* Dynamic categorization by selected guest status */}
        <div className={styles.categoryBreakdown}>
          <h4>Podział według kategorii ({title})</h4>
          <div className={styles.categoryGrid}>
            {Object.entries(totals.by_category).map(([categoryKey, amount]) => (
              <div key={categoryKey} className={styles.categoryChip}>
                <span className={styles.categoryChipName}>
                  {CATEGORY_LABELS[categoryKey as ExpenseCategory] || categoryKey}
                </span>
                <span className={styles.categoryChipAmount}>{amount} zł</span>
              </div>
            ))}
            {Object.keys(totals.by_category).length === 0 && (
              <p className={styles.textMuted}>Brak zarejestrowanych wydatków w tej grupie.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (!activeEvent) {
    return (
      <div className={styles.emptyState}>
        <h2>Brak wybranego wydarzenia</h2>
        <p>Wybierz wydarzenie, aby wyświetlić zestawienia finansowe.</p>
        <div className={styles.eventGrid}>
          {events.map(e => (
            <button key={e.id} className={styles.eventCard} onClick={() => setActiveEvent({ id: e.id, name: e.name })}>
              <h3>{e.name}</h3>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <PageTitle title="Zaawansowany Raport i Budżet" />

      <div className={styles.eventHeader}>
        <div className={styles.eventInfo}>
          <span className={styles.eventIcon}>💰</span>
          <div>
            <strong>{activeEvent.name}</strong>
            <p className={styles.eventSubtitle}>Moduł budżetowy powiązany ze statusami gości</p>
          </div>
        </div>
        <button className={styles.btnSecondary} onClick={() => setShowEventSelector(!showEventSelector)}>
          Zmień wydarzenie
        </button>
      </div>

      {showEventSelector && (
        <div className={styles.eventSelector}>
          <div className={styles.eventGrid}>
            {events.map(e => (
              <button key={e.id} className={styles.eventCard} onClick={() => { setActiveEvent({ id: e.id, name: e.name }); setShowEventSelector(false); }}>
                {e.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {serverError && <div className={styles.serverError}>{serverError}</div>}
      {successMsg && <div className={styles.successMsg}>{successMsg}</div>}

      {summary && (
        <div className={styles.card}>
          <div className={styles.dashboardTabsHeader}>
            <button 
              className={`${styles.tabBtn} ${activeSummaryTab === 'actual_total' ? styles.tabBtnActive : ''}`} 
              onClick={() => setActiveSummaryTab('actual_total')}
            >
              Prognoza całkowita (Wszyscy goście)
            </button>
            <button 
              className={`${styles.tabBtn} ${activeSummaryTab === 'confirmed' ? styles.tabBtnActive : ''}`} 
              onClick={() => setActiveSummaryTab('confirmed')}
            >
              Koszty potwierdzone (Potwierdzeni)
            </button>
            <button 
              className={`${styles.tabBtn} ${activeSummaryTab === 'pending' ? styles.tabBtnActive : ''}`} 
              onClick={() => setActiveSummaryTab('pending')}
            >
              Koszty oczekujące (Oczekujący)
            </button>
          </div>

          <div className={styles.tabContent}>
            {activeSummaryTab === 'actual_total' && renderSummaryMetrics(summary.actual_total, 'Wszyscy goście')}
            {activeSummaryTab === 'confirmed' && renderSummaryMetrics(summary.confirmed, 'Potwierdzeni')}
            {activeSummaryTab === 'pending' && renderSummaryMetrics(summary.pending, 'Oczekujący')}
          </div>
        </div>
      )}

      {/* Expense Form */}
      <div className={styles.card} ref={expenseFormRef}>
        <h2 className={styles.cardTitle}>{editingExpenseId ? 'Edycja Wydatku' : 'Nowy Wydatek'}</h2>
        <form onSubmit={expenseForm.handleSubmit(handleExpenseSubmit)} className={styles.form}>
          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>Nazwa pozycji *</label>
              <input type="text" className={styles.input} {...expenseForm.register('name', { required: true })} />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Kategoria kosztu *</label>
              <select className={styles.input} {...expenseForm.register('category')}>
                {Object.entries(CATEGORY_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label}>Strategia naliczania *</label>
              <select className={styles.input} {...expenseForm.register('calculation_strategy')}>
                {Object.entries(STRATEGY_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>{label}</option>
                ))}
              </select>
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Cena jednostkowa (zł) *</label>
              <input type="number" step="0.01" className={styles.input} {...expenseForm.register('unit_price', { valueAsNumber: true, required: true })} />
            </div>
            {watchStrategy === 'CUSTOM_MULTIPLIER' && (
              <div className={styles.field}>
                <label className={styles.label}>Mnożnik niestandardowy</label>
                <input type="number" step="0.01" className={styles.input} {...expenseForm.register('custom_multiplier', { valueAsNumber: true })} />
              </div>
            )}
          </div>

          <div className={styles.field} style={{ flexDirection: 'row', alignItems: 'center', gap: '0.6rem' }}>
            <input type="checkbox" id="is_included_in_wedding_total" {...expenseForm.register('is_included_in_wedding_total')} />
            <label htmlFor="is_included_in_wedding_total" className={styles.label} style={{ marginBottom: 0, cursor: 'pointer' }}>
              Wlicz do kosztów ogólnych wesela (odznaczenie oznacza koszt własny Pary Młodej)
            </label>
          </div>

          <div className={styles.formActions}>
            <button type="submit" className={styles.btn}>{editingExpenseId ? 'Zapisz zmiany' : 'Dodaj wydatek'}</button>
            {editingExpenseId && <button type="button" className={styles.btnSecondary} onClick={resetExpenseForm}>Anuluj</button>}
          </div>
        </form>
      </div>

      {/* List and filter by category */}
      <div className={styles.card}>
        <div className={styles.filterContainer}>
          <button className={`${styles.filterBtn} ${selectedCategoryFilter === 'ALL' ? styles.filterBtnActive : ''}`} onClick={() => setSelectedCategoryFilter('ALL')}>
            Wszystkie kategorie
          </button>
          {Object.entries(CATEGORY_LABELS).map(([val, label]) => (
            <button key={val} className={`${styles.filterBtn} ${selectedCategoryFilter === val ? styles.filterBtnActive : ''}`} onClick={() => setSelectedCategoryFilter(val as ExpenseCategory)}>
              {label}
            </button>
          ))}
        </div>

        <div className={styles.itemsList}>
          {filteredExpenses.map(expense => (
            <div key={expense.id} className={styles.itemCard}>
              <div className={styles.itemHeader}>
                <div className={styles.itemInfo}>
                  <h3 className={styles.itemName}>{expense.name}</h3>
                  <p className={styles.itemMeta}>
                    Kategoria: <strong>{CATEGORY_LABELS[expense.category]}</strong> · Reguła: {STRATEGY_LABELS[expense.calculation_strategy]}
                  </p>
                  <div className={styles.badgeRow}>
                    <span className={`${styles.badge} ${expense.is_included_in_wedding_total ? styles.badgeWedding : styles.badgeCouple}`}>
                      {expense.is_included_in_wedding_total ? 'Koszt Wesela' : 'Koszt Pary Młodej'}
                    </span>
                  </div>
                  <p className={styles.itemDetails}>
                    Koszt wyliczony: <strong>{expense.calculated_total_cost} zł</strong>
                  </p>
                </div>
                <div className={styles.itemActions}>
                  <button className={styles.btnSmall} onClick={() => startEditExpense(expense)}>Edytuj</button>
                  <button className={styles.btnSmallDanger} onClick={() => deleteExpense(expense.id)}>Usuń</button>
                </div>
              </div>
            </div>
          ))}
          {filteredExpenses.length === 0 && (
            <p className={styles.textMuted} style={{ textAlign: 'center', padding: '2rem 0' }}>Brak pozycji spełniających kryteria.</p>
          )}
        </div>
      </div>
    </div>
  );
}