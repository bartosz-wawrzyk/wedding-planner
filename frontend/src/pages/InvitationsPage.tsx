import { useState, useEffect, useMemo, useRef } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useEventStore } from "../store/eventStore";
import PageTitle from "../components/common/PageTitle";
import { invitationsService } from "../features/invitations/invitations.service";
import type { Event } from "../features/events/event.types";
import type { Guest } from "../features/guests/guests.types";
import type { Invitation } from "../features/invitations/invitations.types";
import {
  GUEST_TYPE_LABELS,
  SIDE_LABELS,
  CONFIRMATION_LABELS,
} from "../features/guests/guests.types";
import styles from "./InvitationsPage.module.css";

const STATUS_LABELS: Record<string, string> = {
  NOT_SENT: "Nie wysłane",
  NOT_DELIVERED: "Nie doręczone",
  DELIVERED: "Doręczone",
};

interface BackendValidationError {
  response?: {
    data?: {
      detail?: Array<{ msg: string }> | string;
    };
  };
}

export default function InvitationsPage() {
  const navigate = useNavigate();
  const { activeEvent, setActiveEvent } = useEventStore();

  const [events, setEvents] = useState<Event[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [allGuests, setAllGuests] = useState<Guest[]>([]);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showEventSelector, setShowEventSelector] = useState(false);
  const [guestSearch, setGuestSearch] = useState("");
  const [selectedGuestIds, setSelectedGuestIds] = useState<string[]>([]);
  const [showGuestSelector, setShowGuestSelector] = useState(false);
  const [updatingStatusId, setUpdatingStatusId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [viewingInvitationId, setViewingInvitationId] = useState<string | null>(null);

  const [modalMode, setModalMode] = useState<string | "new" | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<{ group_name: string }>();

  useEffect(() => {
    if (successMsg) {
      const timer = setTimeout(() => setSuccessMsg(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMsg]);

  const handleApiError = (err: unknown, defaultMessage: string) => {
    const error = err as BackendValidationError;
    let message = defaultMessage;
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        message = error.response.data.detail.map((e) => e.msg).join(", ");
      } else if (typeof error.response.data.detail === "string") {
        message = error.response.data.detail;
      }
    }
    setServerError(message);
  };

  const fetchEvents = async () => {
    try {
      const response = await api.get<Event[]>("/events/");
      setEvents(response.data);
    } catch {
      setServerError("Nie udało się pobrać wydarzeń.");
    }
  };

  const fetchInvitations = async () => {
    if (!activeEvent?.id) return;
    try {
      setLoading(true);
      const data = await invitationsService.getInvitations(activeEvent.id);
      setInvitations(data);
    } catch {
      setServerError("Nie udało się pobrać zaproszeń.");
    } finally {
      setLoading(false);
    }
  };

  const fetchGuests = async () => {
    if (!activeEvent?.id) return;
    try {
      const response = await api.get<Guest[]>(`/events/${activeEvent.id}/guests`);
      setAllGuests(response.data);
    } catch {
      console.error("Nie udało się pobrać gości.");
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    if (activeEvent?.id) {
      fetchInvitations();
      fetchGuests();
    }
  }, [activeEvent?.id]);

  const filteredInvitations = useMemo(() => {
    if (statusFilter === "ALL") return invitations;
    return invitations.filter((inv) => inv.status === statusFilter);
  }, [invitations, statusFilter]);

  const totalPages = Math.ceil(filteredInvitations.length / pageSize);
  const paginatedInvitations = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredInvitations.slice(start, start + pageSize);
  }, [filteredInvitations, currentPage, pageSize]);

  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter]);

  const filteredGuests = useMemo(() => {
    const search = guestSearch.trim().toLowerCase();
    if (!search) return allGuests;
    return allGuests.filter((guest) =>
      guest.full_name.toLowerCase().includes(search)
    );
  }, [allGuests, guestSearch]);

  const assignedGuestIds = useMemo(() => {
    const ids = new Set<string>();
    invitations.forEach((inv) => {
      if (modalMode && modalMode !== "new" && inv.id === modalMode) return;
      inv.guests.forEach((guest) => ids.add(guest.id));
    });
    return ids;
  }, [invitations, modalMode]);

  const availableGuests = useMemo(() => {
    return filteredGuests.filter((g) => !assignedGuestIds.has(g.id));
  }, [filteredGuests, assignedGuestIds]);

  const selectedGuests = useMemo(() => {
    return allGuests.filter((g) => selectedGuestIds.includes(g.id));
  }, [allGuests, selectedGuestIds]);

  const toggleGuestSelection = (guestId: string) => {
    setSelectedGuestIds((prev) =>
      prev.includes(guestId) ? prev.filter((id) => id !== guestId) : [...prev, guestId]
    );
  };

  const addGuestBySearch = () => {
    const found = availableGuests.find(
      (g) => g.full_name.toLowerCase() === guestSearch.trim().toLowerCase()
    );
    if (found) {
      toggleGuestSelection(found.id);
      setGuestSearch("");
    }
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addGuestBySearch();
    }
  };

  const openModal = (mode: string | "new") => {
    setModalMode(mode);
    setServerError(null);
    setSuccessMsg(null);
    if (mode === "new") {
      reset();
      setSelectedGuestIds([]);
      setGuestSearch("");
    }
  };

  const closeModal = () => {
    setModalMode(null);
    reset();
    setSelectedGuestIds([]);
    setGuestSearch("");
    setShowGuestSelector(false);
    setServerError(null);
  };

  const startEdit = (invitation: Invitation) => {
    setValue("group_name", invitation.group_name);
    setSelectedGuestIds(invitation.guests.map((g) => g.id));
    openModal(invitation.id);
  };

  const onSubmit = async (data: { group_name: string }) => {
    if (!activeEvent?.id) {
      setServerError("Najpierw wybierz aktywne wydarzenie.");
      return;
    }
    if (selectedGuestIds.length === 0) {
      setServerError("Wybierz co najmniej jednego gościa.");
      return;
    }

    setServerError(null);
    setSuccessMsg(null);

    const payload = {
      group_name: data.group_name,
      guest_ids: selectedGuestIds,
    };

    try {
      if (modalMode && modalMode !== "new") {
        await invitationsService.updateInvitation(activeEvent.id, modalMode, payload);
        setSuccessMsg("Zaproszenie zaktualizowane!");
      } else {
        await invitationsService.createInvitation(activeEvent.id, payload);
        setSuccessMsg("Zaproszenie utworzone!");
      }

      closeModal();
      fetchInvitations();
    } catch (err) {
      handleApiError(err, "Wystąpił błąd podczas zapisywania.");
    }
  };

  const updateStatus = async (invitationId: string, status: "NOT_DELIVERED" | "DELIVERED") => {
    if (!activeEvent?.id) return;

    setServerError(null);
    setSuccessMsg(null);
    setUpdatingStatusId(invitationId);

    try {
      await invitationsService.updateStatus(activeEvent.id, invitationId, status);
      setSuccessMsg(`Status zmieniony na: ${STATUS_LABELS[status]}`);
      fetchInvitations();
    } catch (err) {
      handleApiError(err, "Nie udało się zaktualizować statusu.");
    } finally {
      setUpdatingStatusId(null);
    }
  };

  const handleDelete = async (invitationId: string) => {
    if (!activeEvent?.id) return;
    if (!window.confirm("Czy na pewno chcesz usunąć to zaproszenie? Goście NIE zostaną usunięci.")) return;

    setServerError(null);
    setSuccessMsg(null);

    try {
      await invitationsService.deleteInvitation(activeEvent.id, invitationId);
      setSuccessMsg("Zaproszenie usunięte.");

      if (modalMode === invitationId) closeModal();
      if (viewingInvitationId === invitationId) setViewingInvitationId(null);

      fetchInvitations();
    } catch (err) {
      handleApiError(err, "Nie udało się usunąć zaproszenia.");
    }
  };

  const viewDetails = (invitation: Invitation) => {
    setViewingInvitationId(viewingInvitationId === invitation.id ? null : invitation.id);
  };

  const handleSelectEvent = (event: Event) => {
    setActiveEvent({ id: event.id, name: event.name });
    setShowEventSelector(false);
    closeModal();
    setViewingInvitationId(null);
    setCurrentPage(1);
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case "NOT_DELIVERED":
        return styles.statusNotDelivered;
      case "DELIVERED":
        return styles.statusDelivered;
      default:
        return styles.statusNotSent;
    }
  };

  const statusCounts = useMemo(() => {
    return {
      ALL: invitations.length,
      NOT_DELIVERED: invitations.filter((inv) => inv.status === "NOT_DELIVERED").length,
      DELIVERED: invitations.filter((inv) => inv.status === "DELIVERED").length,
    };
  }, [invitations]);

  if (!activeEvent) {
    return (
      <>
        <PageTitle title="Zaproszenia" />
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>💌</div>
          <h2>Wybierz wydarzenie</h2>
          <p>Aby zarządzać zaproszeniami, najpierw wybierz aktywne wydarzenie.</p>

          {events.length > 0 ? (
            <div className={styles.eventGrid}>
              {events.map((event) => (
                <button
                  key={event.id}
                  className={styles.eventCard}
                  onClick={() => handleSelectEvent(event)}
                >
                  <h3>{event.name}</h3>
                  <p>
                    {new Date(event.date_time).toLocaleDateString("pl-PL", {
                      dateStyle: "long",
                    })}
                  </p>
                  <span className={styles.selectHint}>Kliknij, aby wybrać →</span>
                </button>
              ))}
            </div>
          ) : (
            <button className={styles.btn} onClick={() => navigate("/event")}>
              Przejdź do wydarzeń
            </button>
          )}
        </div>
      </>
    );
  }

  const totalGuestsInInvitations = invitations.reduce((sum, inv) => sum + inv.guests.length, 0);
  const unassignedGuestsCount = allGuests.length - totalGuestsInInvitations;

  return (
    <>
      <PageTitle title="Zaproszenia" />
      <div className={styles.eventHeader}>
        <div className={styles.eventInfo}>
          <span className={styles.eventIcon}>💌</span>
          <div>
            <strong>{activeEvent.name}</strong>
            <p className={styles.eventSubtitle}>
              {invitations.length} zaproszeń · {totalGuestsInInvitations} gości ·{" "}
              {unassignedGuestsCount} bez zaproszenia
            </p>
          </div>
        </div>
        <div className={styles.eventActions}>
          <button className={styles.btnSecondary} onClick={() => setShowEventSelector(!showEventSelector)}>
            Zmień wydarzenie
          </button>
          <button className={styles.btnSmallDanger} onClick={() => setActiveEvent(null)}>
            Wyczyść
          </button>
        </div>
      </div>

      {showEventSelector && (
        <div className={styles.eventSelector}>
          <h3>Wybierz inne wydarzenie:</h3>
          <div className={styles.eventGrid}>
            {events.map((event) => (
              <button
                key={event.id}
                className={`${styles.eventCard} ${event.id === activeEvent.id ? styles.eventCardActive : ""}`}
                onClick={() => handleSelectEvent(event)}
              >
                <h4>{event.name}</h4>
                <p>
                  {new Date(event.date_time).toLocaleDateString("pl-PL", {
                    dateStyle: "long",
                  })}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={styles.wrapper}>
        {/* Button to open a modal */}
        <button className={styles.btn} onClick={() => openModal("new")} style={{ marginBottom: "1rem" }}>
          + Nowe zaproszenie
        </button>

        {/* List of invitations with page numbers */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Zaproszenia ({filteredInvitations.length})</h2>
          <div className={styles.filterContainer}>
            {(["ALL", "NOT_DELIVERED", "DELIVERED"] as const).map((filter) => (
              <button
                key={filter}
                className={`${styles.filterBtn} ${statusFilter === filter ? styles.filterBtnActive : ""}`}
                onClick={() => setStatusFilter(filter)}
              >
                {filter === "ALL" ? "Wszystkie" : filter === "NOT_DELIVERED" ? "Nie doręczone" : "Doręczone"} ({statusCounts[filter as keyof typeof statusCounts] ?? invitations.length})
              </button>
            ))}
          </div>

          {loading && <p className={styles.infoMsg}>Ładowanie...</p>}

          {!loading && filteredInvitations.length === 0 && (
            <p className={styles.infoMsg}>Brak zaproszeń.</p>
          )}

          <div className={styles.invitationsList}>
            {paginatedInvitations.map((invitation) => (
              <div key={invitation.id} className={styles.invitationCard}>
                <div className={styles.invitationHeader} onClick={() => viewDetails(invitation)}>
                  <div className={styles.invitationInfo}>
                    <h3 className={styles.invitationName}>💌 {invitation.group_name}</h3>
                    <p className={styles.invitationMeta}>
                      {invitation.guests.length} gości · {new Date(invitation.created_at).toLocaleDateString("pl-PL")}
                    </p>
                  </div>
                  <div className={styles.invitationHeaderActions}>
                    <span className={`${styles.statusBadge} ${getStatusClass(invitation.status)}`}>
                      {STATUS_LABELS[invitation.status] || invitation.status}
                    </span>
                    <span className={styles.expandIcon}>
                      {viewingInvitationId === invitation.id ? "▲" : "▼"}
                    </span>
                  </div>
                </div>

                {viewingInvitationId === invitation.id && (
                  <div className={styles.invitationDetails}>
                    <div className={styles.guestsGrid}>
                      {invitation.guests.map((guest) => (
                        <div key={guest.id} className={styles.guestCard}>
                          <div className={styles.guestCardName}>{guest.full_name}</div>
                          <div className={styles.guestTags}>
                            <span className={styles.tag}>{GUEST_TYPE_LABELS[guest.guest_type]}</span>
                            <span className={`${styles.tag} ${guest.confirmation_status === "confirmed" ? styles.tagSuccess : guest.confirmation_status === "rejected" ? styles.tagDanger : styles.tagWarning}`}>
                              {CONFIRMATION_LABELS[guest.confirmation_status]}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className={styles.invitationActions}>
                  <button type="button" className={styles.btnSmall} onClick={() => startEdit(invitation)}>Edytuj</button>
                  <button type="button" className={styles.btnSmall} onClick={() => viewDetails(invitation)}>Szczegóły</button>
                  <button type="button" className={styles.btnSmallDanger} onClick={() => handleDelete(invitation.id)}>Usuń</button>

                  <div className={styles.statusActions}>
                    <button
                      type="button"
                      className={`${styles.btnStatus} ${styles.btnNotDelivered}`}
                      onClick={() => updateStatus(invitation.id, "NOT_DELIVERED")}
                      disabled={updatingStatusId === invitation.id || invitation.status === "NOT_DELIVERED"}
                    >
                      {updatingStatusId === invitation.id ? "..." : "✗ Nie doręczone"}
                    </button>
                    <button
                      type="button"
                      className={`${styles.btnStatus} ${styles.btnDelivered}`}
                      onClick={() => updateStatus(invitation.id, "DELIVERED")}
                      disabled={updatingStatusId === invitation.id || invitation.status === "DELIVERED"}
                    >
                      {updatingStatusId === invitation.id ? "..." : "✓ Doręczone"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
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

      {/* Modal */}
      {modalMode !== null && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>
                {modalMode === "new" ? "Nowe zaproszenie" : "Edytuj zaproszenie"}
              </h2>
              <button className={styles.modalCloseBtn} onClick={closeModal} aria-label="Zamknij">×</button>
            </div>
            <div className={styles.modalBody}>
              <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
                <div className={styles.field}>
                  <label htmlFor="group_name" className={styles.label}>Nazwa grupy / zaproszenia *</label>
                  <input
                    id="group_name"
                    type="text"
                    className={`${styles.input} ${errors.group_name ? styles.inputError : ""}`}
                    placeholder='np. "Rodzina Kowalskich"'
                    {...register("group_name", {
                      required: "Nazwa grupy jest wymagana.",
                      minLength: { value: 2, message: "Min. 2 znaki." },
                    })}
                  />
                  {errors.group_name && <span className={styles.errorMsg}>{errors.group_name.message}</span>}
                </div>

                <div className={styles.field}>
                  <label className={styles.label}>Goście ({selectedGuestIds.length} wybranych)</label>
                  {selectedGuests.length > 0 && (
                    <div className={styles.selectedGuests}>
                      {selectedGuests.map((guest) => (
                        <span key={guest.id} className={styles.selectedGuestTag}>
                          {guest.full_name}
                          <button type="button" className={styles.removeGuestBtn} onClick={() => toggleGuestSelection(guest.id)}>✕</button>
                        </span>
                      ))}
                    </div>
                  )}
                  <button
                    type="button"
                    className={styles.btnSecondary}
                    onClick={() => {
                      setShowGuestSelector(!showGuestSelector);
                      setTimeout(() => searchInputRef.current?.focus(), 100);
                    }}
                  >
                    {showGuestSelector ? "Schowaj listę gości" : "+ Dodaj gości"}
                  </button>
                </div>

                {showGuestSelector && (
                  <div className={styles.guestSelector}>
                    <div className={styles.guestSearchWrapper}>
                      <input
                        ref={searchInputRef}
                        type="text"
                        className={styles.input}
                        placeholder="🔍 Szukaj..."
                        value={guestSearch}
                        onChange={(e) => setGuestSearch(e.target.value)}
                        onKeyDown={handleSearchKeyDown}
                      />
                      {guestSearch.trim() && (
                        <button type="button" className={styles.btnSmall} onClick={addGuestBySearch}>Dodaj</button>
                      )}
                    </div>
                    <div className={styles.guestStats}>
                      <span>Dostępnych: {availableGuests.length}</span>
                      <span>Przypisanych gdzie indziej: {assignedGuestIds.size}</span>
                    </div>
                    <div className={styles.guestList}>
                      {availableGuests.length === 0 ? (
                        <p className={styles.infoMsg}>
                          {allGuests.length === 0 ? "Brak gości." : "Wszyscy goście przypisani."}
                        </p>
                      ) : (
                        availableGuests.map((guest) => (
                          <label key={guest.id} className={`${styles.guestOption} ${selectedGuestIds.includes(guest.id) ? styles.guestOptionSelected : ""}`}>
                            <input
                              type="checkbox"
                              checked={selectedGuestIds.includes(guest.id)}
                              onChange={() => toggleGuestSelection(guest.id)}
                              className={styles.checkbox}
                            />
                            <div className={styles.guestOptionInfo}>
                              <span className={styles.guestOptionName}>{guest.full_name}</span>
                              <span className={styles.guestOptionDetails}>
                                {GUEST_TYPE_LABELS[guest.guest_type]} · {SIDE_LABELS[guest.side]} · {CONFIRMATION_LABELS[guest.confirmation_status]}
                              </span>
                            </div>
                            {selectedGuestIds.includes(guest.id) && <span className={styles.checkIcon}>✓</span>}
                          </label>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {serverError && <p className={styles.serverError}>{serverError}</p>}
                {successMsg && <p className={styles.successMsg}>{successMsg}</p>}
              </form>
            </div>
            <div className={styles.modalFooter}>
              <button type="button" className={styles.btnSecondary} onClick={closeModal}>Anuluj</button>
              <button type="submit" className={styles.btn} disabled={isSubmitting} onClick={handleSubmit(onSubmit)}>
                {isSubmitting ? "Zapisywanie..." : modalMode === "new" ? "Utwórz zaproszenie" : "Zaktualizuj zaproszenie"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}