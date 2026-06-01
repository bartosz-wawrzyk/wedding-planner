import { useState, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useEventStore } from "../store/eventStore";
import PageTitle from "../components/common/PageTitle";
import type { Event } from "../features/events/event.types";
import type {
  Guest,
  GuestCreate,
  GuestType,
  Side,
  ConfirmationStatus,
} from "../features/guests/guests.types";
import {
  GUEST_TYPE_LABELS,
  SIDE_LABELS,
  CONFIRMATION_LABELS,
} from "../features/guests/guests.types";
import styles from "./GuestsPage.module.css";

interface EventStats {
  total_guests: number;
  guests_confirmed: number;
  guests_pending: number;
  guests_rejected: number;
  adults_total: number;
  children_total: number;
  bride_guests_total: number;
  groom_guests_total: number;
  adults_confirmed: number;
  children_confirmed: number;
  bride_adults_confirmed: number;
  bride_children_confirmed: number;
  groom_adults_confirmed: number;
  groom_children_confirmed: number;
  adults_pending: number;
  children_pending: number;
  bride_adults_pending: number;
  bride_children_pending: number;
  groom_adults_pending: number;
  groom_children_pending: number;
  invitations_total: number;
  invitations_bride: number;
  invitations_groom: number;
  accommodation_confirmed: number;
  accommodation_pending: number;
}

interface Filters {
  side: Side | "";
  guest_type: GuestType | "";
  confirmation_status: ConfirmationStatus | "";
  has_accommodation: boolean | null;
  has_day_after: boolean | null;
  has_invitation: boolean | null;
  has_table: boolean | null;
  search: string;
}

const DEFAULT_FILTERS: Filters = {
  side: "",
  guest_type: "",
  confirmation_status: "",
  has_accommodation: null,
  has_day_after: null,
  has_invitation: null,
  has_table: null,
  search: "",
};

export default function GuestsPage() {
  const navigate = useNavigate();
  const { activeEvent, setActiveEvent } = useEventStore();
  const [events, setEvents] = useState<Event[]>([]);
  const [guests, setGuests] = useState<Guest[]>([]);
  const [eventStats, setEventStats] = useState<EventStats | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showEventSelector, setShowEventSelector] = useState(false);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [showAllStats, setShowAllStats] = useState(false);
  const [panelGuestId, setPanelGuestId] = useState<string | "new" | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<GuestCreate>({
    defaultValues: {
      guest_type: "adult",
      side: "groom",
      confirmation_status: "pending",
      has_accommodation: false,
      has_day_after: false,
      dietary_requirements: "",
      contact_info: "",
    },
  });

  const fetchEvents = async () => {
    try {
      const res = await api.get<Event[]>("/events/");
      setEvents(res.data);
    } catch {
      setServerError("Nie udało się pobrać wydarzeń.");
    }
  };

  const fetchGuests = async () => {
    if (!activeEvent?.id) return;
    try {
      setLoading(true);
      const res = await api.get<Guest[]>(`/events/${activeEvent.id}/guests`);
      setGuests(res.data);
    } catch {
      setServerError("Nie udało się pobrać listy gości.");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!activeEvent?.id) return;
    try {
      const res = await api.get<EventStats>(`/events/${activeEvent.id}/stats`);
      setEventStats(res.data);
    } catch {
    }
  };

  useEffect(() => { fetchEvents(); }, []);
  useEffect(() => {
    if (activeEvent?.id) {
      fetchGuests().then(() => fetchStats());
    }
  }, [activeEvent?.id]);

  const filteredGuests = useMemo(() => {
    return guests.filter((guest) => {
      if (filters.side && guest.side !== filters.side) return false;
      if (filters.guest_type && guest.guest_type !== filters.guest_type) return false;
      if (filters.confirmation_status && guest.confirmation_status !== filters.confirmation_status) return false;
      if (filters.has_accommodation !== null && guest.has_accommodation !== filters.has_accommodation) return false;
      if (filters.has_day_after !== null && guest.has_day_after !== filters.has_day_after) return false;
      if (filters.has_invitation !== null) {
        const hasInv = !!guest.invitation_id;
        if (hasInv !== filters.has_invitation) return false;
      }
      if (filters.has_table !== null) {
        const hasTable = !!guest.table_id;
        if (hasTable !== filters.has_table) return false;
      }
      if (filters.search && !guest.full_name.toLowerCase().includes(filters.search.toLowerCase())) return false;
      return true;
    });
  }, [guests, filters]);

  const totalPages = Math.ceil(filteredGuests.length / pageSize);
  const paginatedGuests = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredGuests.slice(start, start + pageSize);
  }, [filteredGuests, currentPage, pageSize]);

  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  const openPanel = (guestId: string | "new") => {
    setPanelGuestId(guestId);
    setServerError(null);
    setSuccessMsg(null);
    if (guestId === "new") reset();
  };

  const closePanel = () => {
    setPanelGuestId(null);
    reset();
  };

  const startEdit = (guest: Guest) => {
    setValue("full_name", guest.full_name);
    setValue("guest_type", guest.guest_type);
    setValue("side", guest.side);
    setValue("confirmation_status", guest.confirmation_status);
    setValue("has_accommodation", guest.has_accommodation);
    setValue("has_day_after", guest.has_day_after);
    setValue("dietary_requirements", guest.dietary_requirements);
    setValue("contact_info", guest.contact_info);
    openPanel(guest.id);
  };

  const onSubmit = async (data: GuestCreate) => {
    if (!activeEvent?.id) {
      setServerError("Najpierw wybierz aktywne wydarzenie.");
      return;
    }
    setServerError(null);
    setSuccessMsg(null);
    try {
      if (panelGuestId !== null && panelGuestId !== "new") {
        await api.patch(`/events/${activeEvent.id}/guests/${panelGuestId}`, data);
        setSuccessMsg("Dane gościa zaktualizowane!");
      } else {
        await api.post(`/events/${activeEvent.id}/guests`, data);
        setSuccessMsg("Gość dodany pomyślnie!");
      }
      closePanel();
      await fetchGuests();
      await fetchStats();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Wystąpił błąd podczas zapisywania.";
      setServerError(msg);
    }
  };

  const handleDelete = async (guestId: string) => {
    if (!activeEvent?.id) return;
    if (!window.confirm("Czy na pewno chcesz usunąć tego gościa?")) return;
    setServerError(null);
    setSuccessMsg(null);
    try {
      await api.delete(`/events/${activeEvent.id}/guests/${guestId}`);
      setSuccessMsg("Gość usunięty.");
      if (panelGuestId === guestId) closePanel();
      await fetchGuests();
      await fetchStats();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Nie udało się usunąć gościa.";
      setServerError(msg);
    }
  };

  const handleSelectEvent = (event: Event) => {
    setActiveEvent({ id: event.id, name: event.name });
    setShowEventSelector(false);
    setFilters(DEFAULT_FILTERS);
    closePanel();
    setShowAllStats(false);
    setCurrentPage(1);
  };

  const setFilter = (key: keyof Filters, value: string | boolean | null) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setCurrentPage(1);
  };

  const activeFiltersCount = Object.values(filters).filter(v => v !== null && v !== "").length;

  /* ---------- eksport CSV ---------- */
  const exportToCSV = () => {
    if (filteredGuests.length === 0) return;
    const header = "Imię i nazwisko,Typ,Strona,Status,Nocleg,Poprawiny,Zaproszenie,Stół,Wymagania dietetyczne,Kontakt";
    const rows = filteredGuests.map(g =>
      [
        g.full_name,
        GUEST_TYPE_LABELS[g.guest_type],
        SIDE_LABELS[g.side],
        CONFIRMATION_LABELS[g.confirmation_status],
        g.has_accommodation ? "Tak" : "Nie",
        g.has_day_after ? "Tak" : "Nie",
        g.invitation_id ? "Tak" : "Nie",
        g.table_id ? "Tak" : "Nie",
        g.dietary_requirements || "",
        g.contact_info || "",
      ].join(",")
    );
    const csvContent = [header, ...rows].join("\n");
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `goscie_${activeEvent?.name ?? "wydarzenie"}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!activeEvent) {
    return (
      <>
        <PageTitle title="Goście" />
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>💒</div>
          <h2>Wybierz wydarzenie</h2>
          <p>Aby zarządzać gośćmi, najpierw wybierz aktywne wydarzenie.</p>
          {events.length > 0 ? (
            <div className={styles.eventGrid}>
              {events.map(event => (
                <button key={event.id} className={styles.eventCard} onClick={() => handleSelectEvent(event)}>
                  <h3>{event.name}</h3>
                  <p>{new Date(event.date_time).toLocaleDateString("pl-PL", { dateStyle: "long" })}</p>
                  <span className={styles.selectHint}>Kliknij, aby wybrać →</span>
                </button>
              ))}
            </div>
          ) : (
            <button className={styles.btn} onClick={() => navigate("/event")}>Przejdź do wydarzeń</button>
          )}
        </div>
      </>
    );
  }

  return (
    <>
      <PageTitle title="Goście" />

      <div className={styles.eventHeader}>
        <div className={styles.eventInfo}>
          <span className={styles.eventIcon}>👥</span>
          <div>
            <strong>{activeEvent.name}</strong>
            <p className={styles.eventSubtitle}>
              Goście: {filteredGuests.length} / {guests.length}
              {activeFiltersCount > 0 && ` (filtruje: ${activeFiltersCount})`}
            </p>
          </div>
        </div>
        <div className={styles.eventActions}>
          <button className={styles.btnSecondary} onClick={() => setShowEventSelector(!showEventSelector)}>
            Zmień wydarzenie
          </button>
          <button className={styles.btnSmallDanger} onClick={() => setActiveEvent(null)}>Wyczyść</button>
        </div>
      </div>

      {showEventSelector && (
        <div className={styles.eventSelector}>
          <h3>Wybierz inne wydarzenie:</h3>
          <div className={styles.eventGrid}>
            {events.map(event => (
              <button key={event.id} className={`${styles.eventCard} ${event.id === activeEvent.id ? styles.eventCardActive : ""}`}
                onClick={() => handleSelectEvent(event)}>
                <h4>{event.name}</h4>
                <p>{new Date(event.date_time).toLocaleDateString("pl-PL", { dateStyle: "long" })}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {eventStats && (
        <div className={styles.statsContainer}>
          <div className={styles.stats}>
            <div className={styles.statItem}><span className={styles.statValue}>{eventStats.total_guests}</span><span className={styles.statLabel}>Wszyscy goście</span></div>
            <div className={styles.statItem}><span className={styles.statValue}>{eventStats.guests_confirmed}</span><span className={styles.statLabel}>Potwierdzeni</span></div>
            <div className={styles.statItem}><span className={styles.statValue}>{eventStats.guests_pending}</span><span className={styles.statLabel}>Oczekujący</span></div>
            <div className={styles.statItem}><span className={styles.statValue}>{eventStats.guests_rejected}</span><span className={styles.statLabel}>Odrzuceni</span></div>
            <button type="button" className={styles.showStatsBtn} onClick={() => setShowAllStats(!showAllStats)}>
              {showAllStats ? "▲ Ukryj szczegóły" : "▼ Pokaż szczegóły"}
            </button>
          </div>

          {showAllStats && (
            <div className={styles.detailedStats}>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.adults_total ?? 0}</span><span className={styles.statLabel}>Dorośli łącznie</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.children_total ?? 0}</span><span className={styles.statLabel}>Dzieci łącznie</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.bride_guests_total ?? 0}</span><span className={styles.statLabel}>Goście p. młodej</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.groom_guests_total ?? 0}</span><span className={styles.statLabel}>Goście p. młodego</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.adults_confirmed ?? 0}</span><span className={styles.statLabel}>Dorośli potwierdzeni</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.children_confirmed ?? 0}</span><span className={styles.statLabel}>Dzieci potwierdzone</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.bride_adults_confirmed ?? 0}</span><span className={styles.statLabel}>Dorośli potw. (p. młoda)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.bride_children_confirmed ?? 0}</span><span className={styles.statLabel}>Dzieci potw. (p. młoda)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.groom_adults_confirmed ?? 0}</span><span className={styles.statLabel}>Dorośli potw. (p. młody)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.groom_children_confirmed ?? 0}</span><span className={styles.statLabel}>Dzieci potw. (p. młody)</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.adults_pending ?? 0}</span><span className={styles.statLabel}>Dorośli oczekujący</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.children_pending ?? 0}</span><span className={styles.statLabel}>Dzieci oczekujące</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.bride_adults_pending ?? 0}</span><span className={styles.statLabel}>Dorośli oczek. (p. młoda)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.bride_children_pending ?? 0}</span><span className={styles.statLabel}>Dzieci oczek. (p. młoda)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.groom_adults_pending ?? 0}</span><span className={styles.statLabel}>Dorośli oczek. (p. młody)</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.groom_children_pending ?? 0}</span><span className={styles.statLabel}>Dzieci oczek. (p. młody)</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.invitations_total ?? 0}</span><span className={styles.statLabel}>Zaproszenia łącznie</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.invitations_bride ?? 0}</span><span className={styles.statLabel}>Zaproszenia p. młodej</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.invitations_groom ?? 0}</span><span className={styles.statLabel}>Zaproszenia p. młodego</span></div>
              
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.accommodation_confirmed ?? 0}</span><span className={styles.statLabel}>Noclegi potwierdzone</span></div>
              <div className={styles.statItem}><span className={styles.statValue}>{eventStats.accommodation_pending ?? 0}</span><span className={styles.statLabel}>Noclegi oczekujące</span></div>
            </div>
          )}
        </div>
      )}

      <div className={styles.wrapper}>
        {!panelGuestId && (
          <button className={styles.addGuestBtn} onClick={() => openPanel("new")}>+ Dodaj gościa</button>
        )}

        <div className={styles.card}>
          <div className={styles.filterHeader}>
            <h2 className={styles.cardTitle}>Lista gości ({filteredGuests.length})</h2>
            <div className={styles.filterActions}>
              {activeFiltersCount > 0 && (
                <button className={styles.btnClearFilters} onClick={clearFilters}>Wyczyść filtry ({activeFiltersCount})</button>
              )}
              <button className={styles.btnSmall} onClick={exportToCSV} disabled={filteredGuests.length === 0}>
                📥 CSV
              </button>
            </div>
          </div>

          <div className={styles.filtersBar}>
            <div className={styles.searchBox}>
              <input type="text" className={styles.searchInput} placeholder="🔍 Szukaj po imieniu i nazwisku..."
                value={filters.search} onChange={e => setFilter("search", e.target.value)} />
            </div>
            <div className={styles.filterSelects}>
              <div className={styles.filterSelectGroup}>
                <label className={styles.filterSelectLabel}>Strona</label>
                <select className={styles.filterSelect} value={filters.side} onChange={e => setFilter("side", e.target.value as Side | "")}>
                  <option value="">Wszyscy</option>
                  {Object.entries(SIDE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div className={styles.filterSelectGroup}>
                <label className={styles.filterSelectLabel}>Status</label>
                <select className={styles.filterSelect} value={filters.confirmation_status} onChange={e => setFilter("confirmation_status", e.target.value as ConfirmationStatus | "")}>
                  <option value="">Wszyscy</option>
                  {Object.entries(CONFIRMATION_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div className={styles.filterSelectGroup}>
                <label className={styles.filterSelectLabel}>Typ</label>
                <select className={styles.filterSelect} value={filters.guest_type} onChange={e => setFilter("guest_type", e.target.value as GuestType | "")}>
                  <option value="">Wszyscy</option>
                  {Object.entries(GUEST_TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
            </div>
            <div className={styles.filterToggles}>
              <button className={`${styles.filterToggleBtn} ${filters.has_accommodation === true ? styles.filterToggleActive : ""}`}
                onClick={() => setFilter("has_accommodation", filters.has_accommodation === true ? null : true)}>🏨 Nocleg</button>
              <button className={`${styles.filterToggleBtn} ${filters.has_day_after === true ? styles.filterToggleActive : ""}`}
                onClick={() => setFilter("has_day_after", filters.has_day_after === true ? null : true)}>🌅 Poprawiny</button>
              <button className={`${styles.filterToggleBtn} ${filters.has_invitation === true ? styles.filterToggleActive : ""}`}
                onClick={() => setFilter("has_invitation", filters.has_invitation === true ? null : true)}>📨 Zaproszenie</button>
              <button className={`${styles.filterToggleBtn} ${filters.has_table === true ? styles.filterToggleActive : ""}`}
                onClick={() => setFilter("has_table", filters.has_table === true ? null : true)}>🪑 Stół</button>
            </div>
          </div>

          {loading && <p className={styles.infoMsg}>Ładowanie...</p>}
          {!loading && filteredGuests.length === 0 && (
            <p className={styles.infoMsg}>{guests.length === 0 ? "Brak gości. Dodaj pierwszego gościa!" : "Brak gości spełniających kryteria."}</p>
          )}

          <div className={styles.guestsList}>
            {paginatedGuests.map(guest => (
              <div key={guest.id} className={`${styles.guestItem} ${panelGuestId === guest.id ? styles.guestActive : ""}`}>
                <div className={styles.guestInfo}>
                  <h3 className={styles.guestName}>{guest.full_name}</h3>
                  <div className={styles.guestTags}>
                    <span className={styles.tag}>{GUEST_TYPE_LABELS[guest.guest_type]}</span>
                    <span className={styles.tag}>{SIDE_LABELS[guest.side]}</span>
                    <span className={`${styles.tag} ${
                      guest.confirmation_status === "confirmed" ? styles.tagSuccess :
                      guest.confirmation_status === "rejected" ? styles.tagDanger : styles.tagWarning}`}>
                      {CONFIRMATION_LABELS[guest.confirmation_status]}
                    </span>
                    {guest.has_accommodation && <span className={styles.tag}>🏨 Nocleg</span>}
                    {guest.has_day_after && <span className={styles.tag}>🌅 Poprawiny</span>}
                  </div>
                  <div className={styles.guestAssignmentInfo}>
                    <span className={`${styles.assignmentTag} ${guest.invitation_id ? styles.assignmentYes : styles.assignmentNo}`}>
                      {guest.invitation_id ? "📨 Ma zaproszenie" : "📨 Brak zaproszenia"}
                    </span>
                    <span className={`${styles.assignmentTag} ${guest.table_id ? styles.assignmentYes : styles.assignmentNo}`}>
                      {guest.table_id ? "🪑 Przy stole" : "🪑 Bez stołu"}
                    </span>
                  </div>
                  {guest.dietary_requirements && <p className={styles.guestDetail}>🍽️ {guest.dietary_requirements}</p>}
                  {guest.contact_info && <p className={styles.guestDetail}>📞 {guest.contact_info}</p>}
                </div>
                <div className={styles.guestActions}>
                  <button className={styles.btnSmall} onClick={() => startEdit(guest)}>Edytuj</button>
                  <button className={styles.btnSmallDanger} onClick={() => handleDelete(guest.id)}>Usuń</button>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button className={styles.btnSmall} disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)}>
                ← Poprzednia
              </button>
              <span className={styles.paginationInfo}>Strona {currentPage} z {totalPages}</span>
              <button className={styles.btnSmall} disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)}>
                Następna →
              </button>
              <select className={styles.filterSelect} value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setCurrentPage(1); }}>
                <option value={10}>10 / strona</option>
                <option value={20}>20 / strona</option>
                <option value={50}>50 / strona</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {panelGuestId !== null && (
        <div className={styles.modalOverlay} onClick={closePanel}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>{panelGuestId === "new" ? "Dodaj gościa" : "Edytuj gościa"}</h2>
              <button className={styles.modalCloseBtn} onClick={closePanel} aria-label="Zamknij">×</button>
            </div>
            <div className={styles.modalBody}>
              <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
                <div className={styles.field}>
                  <label htmlFor="full_name" className={styles.label}>Imię i nazwisko *</label>
                  <input id="full_name" type="text" className={`${styles.input} ${errors.full_name ? styles.inputError : ""}`}
                    placeholder="np. Jan Kowalski" {...register("full_name", { required: "Imię i nazwisko jest wymagane.", minLength: { value: 3, message: "Min. 3 znaki." } })} />
                  {errors.full_name && <span className={styles.errorMsg}>{errors.full_name.message}</span>}
                </div>
                <div className={styles.row}>
                  <div className={styles.field}>
                    <label htmlFor="guest_type" className={styles.label}>Typ gościa</label>
                    <select id="guest_type" className={styles.input} {...register("guest_type")}>
                      {Object.entries(GUEST_TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                  <div className={styles.field}>
                    <label htmlFor="side" className={styles.label}>Strona</label>
                    <select id="side" className={styles.input} {...register("side")}>
                      {Object.entries(SIDE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                </div>
                <div className={styles.field}>
                  <label htmlFor="confirmation_status" className={styles.label}>Status</label>
                  <select id="confirmation_status" className={styles.input} {...register("confirmation_status")}>
                    {Object.entries(CONFIRMATION_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <div className={styles.checkboxGroup}>
                  <label className={styles.checkboxLabel}><input type="checkbox" {...register("has_accommodation")} className={styles.checkbox} /> <span>Zakwaterowanie</span></label>
                  <label className={styles.checkboxLabel}><input type="checkbox" {...register("has_day_after")} className={styles.checkbox} /> <span>Poprawiny</span></label>
                </div>
                <div className={styles.field}>
                  <label htmlFor="dietary_requirements" className={styles.label}>Wymagania dietetyczne</label>
                  <input id="dietary_requirements" type="text" className={styles.input} placeholder="np. wegetariańska, bezglutenowa" {...register("dietary_requirements")} />
                </div>
                <div className={styles.field}>
                  <label htmlFor="contact_info" className={styles.label}>Kontakt</label>
                  <input id="contact_info" type="text" className={styles.input} placeholder="np. telefon, email" {...register("contact_info")} />
                </div>
                {serverError && <p className={styles.serverError}>{serverError}</p>}
                {successMsg && <p className={styles.successMsg}>{successMsg}</p>}
              </form>
            </div>
            <div className={styles.modalFooter}>
              <button type="button" className={styles.btnSecondary} onClick={closePanel}>Anuluj</button>
              <button type="submit" className={styles.btn} disabled={isSubmitting}
                onClick={handleSubmit(onSubmit)}>
                {isSubmitting ? "Zapisywanie..." : panelGuestId === "new" ? "Dodaj gościa" : "Zaktualizuj"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}