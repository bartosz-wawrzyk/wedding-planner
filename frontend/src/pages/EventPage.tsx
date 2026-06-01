import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useEventStore } from "../store/eventStore";
import PageTitle from "../components/common/PageTitle";
import type { Event, EventCreate } from "../features/events/event.types";
import styles from "./EventPage.module.css";

export default function EventPage() {
  const navigate = useNavigate();
  const { activeEvent, setActiveEvent } = useEventStore();
  const [events, setEvents] = useState<Event[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [formVisible, setFormVisible] = useState(false);
  const [formHiding, setFormHiding] = useState(false);

  const successTimerRef = useRef<number | null>(null);
  const hideTimerRef = useRef<number | null>(null);
  const fadeTimerRef = useRef<number | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<EventCreate>();

  useEffect(() => {
    return () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current);
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
      if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    };
  }, []);

  const showTemporarySuccess = (message: string, delay = 9000) => {
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
    setSuccessMsg(message);
    successTimerRef.current = window.setTimeout(() => {
      setSuccessMsg(null);
      successTimerRef.current = null;
    }, delay);
  };

  const startHidingForm = () => {
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);

    hideTimerRef.current = window.setTimeout(() => {
      setFormHiding(true);
      fadeTimerRef.current = window.setTimeout(() => {
        setFormVisible(false);
        setFormHiding(false);
        hideTimerRef.current = null;
        fadeTimerRef.current = null;
      }, 9000);
    }, 9000);
  };

  const cancelHiding = () => {
    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    if (fadeTimerRef.current) clearTimeout(fadeTimerRef.current);
    setFormHiding(false);
  };

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await api.get<Event[]>("/events/");
      setEvents(response.data);

      if (response.data.length === 0) {
        setFormVisible(true);
        setActiveEvent(null);
      } else {
        setFormVisible(false);
      }
    } catch {
      setServerError("Nie udało się pobrać wydarzeń.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const onSubmit = async (data: EventCreate) => {
    setServerError(null);
    setSuccessMsg(null);
    cancelHiding();

    try {
      const payload = {
        ...data,
        date_time: new Date(data.date_time).toISOString(),
      };

      if (editingId) {
        await api.patch(`/events/${editingId}`, payload);
        showTemporarySuccess("Wydarzenie zaktualizowane!");
        setEditingId(null);
      } else {
        const response = await api.post<Event>("/events/", payload);
        showTemporarySuccess("Wydarzenie utworzone!");
        setActiveEvent({ id: response.data.id, name: response.data.name });
      }

      reset();
      fetchEvents();
      startHidingForm();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Wystąpił błąd podczas zapisywania.";
      setServerError(message);
    }
  };

  const startEdit = (event: Event) => {
    cancelHiding();
    setEditingId(event.id);
    setValue("name", event.name);
    setValue("date_time", event.date_time.slice(0, 16));
    setValue("ceremony_place", event.ceremony_place);
    setValue("ceremony_address", event.ceremony_address);
    setValue("reception_place", event.reception_place);
    setValue("reception_address", event.reception_address);
    setServerError(null);
    setSuccessMsg(null);
    setFormVisible(true);
  };

  const cancelEdit = () => {
    setEditingId(null);
    reset();
    setServerError(null);
    cancelHiding();
    if (events.length > 0) {
      setFormVisible(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Czy na pewno chcesz usunąć to wydarzenie?")) return;

    setServerError(null);
    setSuccessMsg(null);

    try {
      await api.delete(`/events/${id}`);
      showTemporarySuccess("Wydarzenie usunięte.", 3000);

      if (editingId === id) {
        cancelEdit();
      }

      if (activeEvent?.id === id) {
        setActiveEvent(null);
      }

      fetchEvents();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Nie udało się usunąć wydarzenia.";
      setServerError(message);
    }
  };

  const handleSelectEvent = (event: Event) => {
    setActiveEvent({ id: event.id, name: event.name });
    navigate("/guests");
  };

  return (
    <>
      <PageTitle title="Wydarzenia" />

      {activeEvent && (
        <div className={styles.activeBanner}>
          <span className={styles.activeIcon}>💍</span>
          <div>
            <strong>Aktywne wydarzenie:</strong> {activeEvent.name}
          </div>
          <button
            type="button"
            className={styles.btnSmallDanger}
            onClick={() => setActiveEvent(null)}
          >
            Wyczyść
          </button>
        </div>
      )}

      <div className={styles.wrapper}>
        {formVisible && (
          <div
            className={`${styles.formCard} ${formHiding ? styles.formCardHidden : ""}`}
          >
            <div className={styles.card}>
              <h2 className={styles.cardTitle}>
                {editingId ? "Edytuj wydarzenie" : "Dodaj wydarzenie"}
              </h2>

              <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
                <div className={styles.field}>
                  <label htmlFor="name" className={styles.label}>Nazwa wydarzenia</label>
                  <input
                    id="name"
                    type="text"
                    className={`${styles.input} ${errors.name ? styles.inputError : ""}`}
                    placeholder="np. Wesele Werki i Bartka"
                    {...register("name", { required: "Nazwa jest wymagana." })}
                  />
                  {errors.name && <span className={styles.errorMsg}>{errors.name.message}</span>}
                </div>

                <div className={styles.field}>
                  <label htmlFor="date_time" className={styles.label}>Data i godzina</label>
                  <input
                    id="date_time"
                    type="datetime-local"
                    className={`${styles.input} ${errors.date_time ? styles.inputError : ""}`}
                    {...register("date_time", { required: "Data jest wymagana." })}
                  />
                  {errors.date_time && <span className={styles.errorMsg}>{errors.date_time.message}</span>}
                </div>

                <div className={styles.row}>
                  <div className={styles.field}>
                    <label htmlFor="ceremony_place" className={styles.label}>Miejsce ceremonii</label>
                    <input id="ceremony_place" type="text" className={styles.input} placeholder="np. Kościół..." {...register("ceremony_place")} />
                  </div>
                  <div className={styles.field}>
                    <label htmlFor="ceremony_address" className={styles.label}>Adres ceremonii</label>
                    <input id="ceremony_address" type="text" className={styles.input} placeholder="np. Kraków" {...register("ceremony_address")} />
                  </div>
                </div>

                <div className={styles.row}>
                  <div className={styles.field}>
                    <label htmlFor="reception_place" className={styles.label}>Miejsce wesela</label>
                    <input id="reception_place" type="text" className={styles.input} placeholder="np. Sala Bankietowa" {...register("reception_place")} />
                  </div>
                  <div className={styles.field}>
                    <label htmlFor="reception_address" className={styles.label}>Adres wesela</label>
                    <input id="reception_address" type="text" className={styles.input} placeholder="np. Kraków" {...register("reception_address")} />
                  </div>
                </div>

                {serverError && <p className={styles.serverError}>{serverError}</p>}
                {successMsg && <p className={styles.successMsg}>{successMsg}</p>}

                <div className={styles.formActions}>
                  <button type="submit" className={styles.btn} disabled={isSubmitting}>
                    {isSubmitting ? "Zapisywanie..." : editingId ? "Zaktualizuj" : "Dodaj wydarzenie"}
                  </button>
                  {editingId && (
                    <button type="button" className={styles.btnSecondary} onClick={cancelEdit}>
                      Anuluj
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        )}

        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Twoje wydarzenia</h2>

          {!formVisible && events.length > 0 && (
            <button
              type="button"
              className={styles.btn}
              style={{ marginBottom: "1rem" }}
              onClick={() => {
                cancelHiding();
                setFormVisible(true);
              }}
            >
              Dodaj nowe wydarzenie
            </button>
          )}

          {loading && <p className={styles.infoMsg}>Ładowanie...</p>}
          {!loading && events.length === 0 && (
            <p className={styles.infoMsg}>Brak wydarzeń. Dodaj pierwsze!</p>
          )}

          <div className={styles.eventsList}>
            {events.map((event) => (
              <div
                key={event.id}
                className={`${styles.eventItem} ${
                  editingId === event.id ? styles.eventActive : ""
                } ${activeEvent?.id === event.id ? styles.eventSelected : ""}`}
              >
                <div className={styles.eventInfo}>
                  <h3 className={styles.eventName}>
                    {event.name}
                    {activeEvent?.id === event.id && (
                      <span className={styles.activeBadge}>Aktywne</span>
                    )}
                  </h3>
                  <p className={styles.eventDate}>
                    {new Date(event.date_time).toLocaleString("pl-PL", {
                      dateStyle: "long",
                      timeStyle: "short",
                    })}
                  </p>
                  <p className={styles.eventDetails}>
                    ⛪ {event.ceremony_place}, {event.ceremony_address} | 🥂{" "}
                    {event.reception_place}, {event.reception_address}
                  </p>
                </div>
                <div className={styles.eventActions}>
                  <button
                    type="button"
                    className={styles.btnSmallPrimary}
                    onClick={() => handleSelectEvent(event)}
                  >
                    Wybierz
                  </button>
                  <button
                    type="button"
                    className={styles.btnSmall}
                    onClick={() => startEdit(event)}
                  >
                    Edytuj
                  </button>
                  <button
                    type="button"
                    className={styles.btnSmallDanger}
                    onClick={() => handleDelete(event.id)}
                  >
                    Usuń
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}