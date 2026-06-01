import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import api from "../api/axios";
import { useEventStore } from "../store/eventStore";
import PageTitle from "../components/common/PageTitle";
import TableVisualization from "../components/tables/TableVisualization";
import GuestAssignmentModal from "../components/tables/GuestAssignmentModal";
import type { Event } from "../features/events/event.types";
import type { Guest } from "../features/guests/guests.types";
import type {
  Table,
  TableCreate,
  TableWithGuests,
  GuestAtTable,
  SeatingPosition,
} from "../features/tables/tables.types";
import { SHAPE_LABELS } from "../features/tables/tables.types";
import styles from "./TablesPage.module.css";

const getErrorMessage = (error: unknown): string => {
  if (!error) return "";
  if (typeof error === "string") return error;
  if (error && typeof error === "object") {
    const err = error as any;
    if (err.response?.data?.detail) {
      const detail = err.response.data.detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        return detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
      }
      if (typeof detail === "object") return JSON.stringify(detail);
    }
    if (err.message) return String(err.message);
  }
  return "Wystąpił nieznany błąd";
};

export default function TablesPage() {
  const navigate = useNavigate();
  const { activeEvent, setActiveEvent } = useEventStore();

  const [events, setEvents] = useState<Event[]>([]);
  const [tables, setTables] = useState<Table[]>([]);
  const [selectedTable, setSelectedTable] = useState<TableWithGuests | null>(null);
  const [tableGuests, setTableGuests] = useState<GuestAtTable[]>([]);
  const [editingTableId, setEditingTableId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingTableGuests, setLoadingTableGuests] = useState(false);
  const [showEventSelector, setShowEventSelector] = useState(false);
  const [unassignedGuests, setUnassignedGuests] = useState<Guest[]>([]);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalPositionIndex, setModalPositionIndex] = useState<number>(0);
  const [modalCurrentGuest, setModalCurrentGuest] = useState<GuestAtTable | null>(null);

  const tableRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { isSubmitting },
  } = useForm<TableCreate>({
    defaultValues: { number: 1, name: "", shape: "rectangular", capacity: 10 },
  });

  const watchedShape = watch("shape");
  const watchedCapacity = watch("capacity");

  const fetchEvents = async () => {
    try {
      const response = await api.get<Event[]>("/events/");
      setEvents(response.data);
    } catch {
      setServerError("Nie udało się pobrać wydarzeń.");
    }
  };

  const fetchTables = async () => {
    if (!activeEvent?.id) return;
    try {
      setLoading(true);
      const response = await api.get<Table[]>(`/events/${activeEvent.id}/tables/`);
      setTables(response.data);
    } catch {
      setServerError("Nie udało się pobrać stołów.");
    } finally {
      setLoading(false);
    }
  };

  const fetchUnassignedGuests = async () => {
    if (!activeEvent?.id) return;
    try {
      const response = await api.get<Guest[]>(
        `/events/${activeEvent.id}/tables/guests/unassigned`
      );
      setUnassignedGuests(response.data);
    } catch (err: any) {
      setServerError("Nie udało się pobrać nieprzypisanych gości.");
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    if (activeEvent?.id) {
      fetchTables();
      fetchUnassignedGuests();
    }
  }, [activeEvent?.id]);

  const loadTableDetails = async (tableId: string) => {
    if (!activeEvent?.id) return;

    try {
      setLoadingTableGuests(true);

      const tableResponse = await api.get<Table>(
        `/events/${activeEvent.id}/tables/${tableId}`
      );

      const guestsResponse = await api.get<GuestAtTable[]>(
        `/events/${activeEvent.id}/tables/${tableId}/guests`
      );

      const tableWithGuests: TableWithGuests = {
        ...tableResponse.data,
        guests: guestsResponse.data,
      };

      setSelectedTable(tableWithGuests);
      setTableGuests(guestsResponse.data);
    } catch (err) {
      console.error("Error loading table:", err);
      setServerError(getErrorMessage(err));
    } finally {
      setLoadingTableGuests(false);
    }

    setTimeout(() => {
      tableRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  };

  const saveSeating = async (seating: SeatingPosition[]) => {
    if (!activeEvent?.id || !selectedTable?.id) return;

    const cleanSeating = seating
      .filter((s) => s.guest_id && s.position_index !== undefined)
      .map((s) => ({
        guest_id: s.guest_id,
        position_index: Number(s.position_index),
      }));

    await api.put(
      `/events/${activeEvent.id}/tables/${selectedTable.id}/seating`,
      cleanSeating
    );
  };

  const assignGuestToPosition = useCallback(
    async (guestId: string) => {
      if (!activeEvent?.id || !selectedTable?.id) return;

      setServerError(null);

      try {
        const newSeating: SeatingPosition[] = [];

        tableGuests.forEach((g) => {
          if (
            g.position_index !== null &&
            g.position_index !== undefined &&
            g.position_index !== modalPositionIndex + 1 &&
            g.id !== guestId
          ) {
            newSeating.push({
              guest_id: g.id,
              position_index: g.position_index,
            });
          }
        });

        newSeating.push({
          guest_id: guestId,
          position_index: modalPositionIndex + 1,
        });

        await saveSeating(newSeating);
        setSuccessMsg(`Gość przypisany do miejsca #${modalPositionIndex + 1}!`);
        setModalOpen(false);
        await loadTableDetails(selectedTable.id);
        await fetchUnassignedGuests();
      } catch (err: unknown) {
        console.error("Error assigning guest:", err);
        setServerError(getErrorMessage(err));
      }
    },
    [activeEvent?.id, selectedTable?.id, modalPositionIndex, tableGuests]
  );

  const removeGuestFromPosition = useCallback(
    async (guestId: string) => {
      if (!activeEvent?.id || !selectedTable?.id) return;

      setServerError(null);

      try {
        await api.delete(
          `/events/${activeEvent.id}/tables/${selectedTable.id}/guests/${guestId}`
        );

        const newSeating: SeatingPosition[] = [];
        tableGuests.forEach((g) => {
          if (
            g.id !== guestId &&
            g.position_index !== null &&
            g.position_index !== undefined
          ) {
            newSeating.push({
              guest_id: g.id,
              position_index: g.position_index,
            });
          }
        });

        if (newSeating.length > 0) {
          await saveSeating(newSeating);
        }

        setSuccessMsg("Gość usunięty z miejsca.");
        setModalOpen(false);
        await loadTableDetails(selectedTable.id);
        await fetchUnassignedGuests();
      } catch (err: unknown) {
        console.error("Error removing guest:", err);
        setServerError(getErrorMessage(err));
      }
    },
    [activeEvent?.id, selectedTable?.id, tableGuests]
  );

  const onSubmitTable = async (data: TableCreate) => {
    if (!activeEvent?.id) {
      setServerError("Najpierw wybierz aktywne wydarzenie.");
      return;
    }

    setServerError(null);
    setSuccessMsg(null);

    try {
      if (editingTableId) {
        await api.patch(`/events/${activeEvent.id}/tables/${editingTableId}`, data);
        setSuccessMsg("Stół zaktualizowany!");
        setEditingTableId(null);
      } else {
        await api.post(`/events/${activeEvent.id}/tables`, data);
        setSuccessMsg("Stół utworzony!");
      }

      reset();
      setShowForm(false);
      fetchTables();
    } catch (err: unknown) {
      setServerError(getErrorMessage(err));
    }
  };

  const handleDeleteTable = async (tableId: string) => {
    if (!activeEvent?.id) return;
    if (!window.confirm("Czy na pewno chcesz usunąć ten stół? Goście zostaną odpięci."))
      return;

    setServerError(null);
    setSuccessMsg(null);

    try {
      await api.delete(`/events/${activeEvent.id}/tables/${tableId}`);
      setSuccessMsg("Stół usunięty.");

      if (selectedTable?.id === tableId) {
        setSelectedTable(null);
        setTableGuests([]);
      }

      fetchTables();
    } catch (err: unknown) {
      setServerError(getErrorMessage(err));
    }
  };

  const exportToPDF = async () => {
    if (!selectedTable) return;

    setSuccessMsg("Generowanie PDF...");

    try {
      const element = document.getElementById("table-visualization");
      if (!element) {
        setServerError("Nie znaleziono wizualizacji stołu.");
        return;
      }

      const exportContainer = document.createElement("div");
      exportContainer.style.position = "absolute";
      exportContainer.style.left = "-9999px";
      exportContainer.style.top = "0";
      exportContainer.style.width = "1200px";
      exportContainer.style.backgroundColor = "#ffffff";
      exportContainer.style.padding = "40px";
      exportContainer.style.fontFamily = "Arial, sans-serif";

      const header = document.createElement("div");
      header.style.textAlign = "center";
      header.style.marginBottom = "30px";
      header.innerHTML = `
        <h1 style="font-size: 28px; margin: 0; color: #000; font-weight: 700;">
          Stół nr ${selectedTable.number}
        </h1>
      `;
      exportContainer.appendChild(header);

      const visualizationClone = element.cloneNode(true) as HTMLElement;
      visualizationClone.style.transform = "scale(1.2)";
      visualizationClone.style.transformOrigin = "top center";
      exportContainer.appendChild(visualizationClone);

      const guestsList = document.createElement("div");
      guestsList.style.marginTop = "30px";
      guestsList.style.padding = "20px";
      guestsList.style.borderTop = "2px solid #000";

      const guestsWithPositions = tableGuests
        .filter((g) => g.position_index !== null && g.position_index !== undefined)
        .sort((a, b) => (a.position_index || 0) - (b.position_index || 0));

      if (guestsWithPositions.length > 0) {
        guestsList.innerHTML = `
          <table style="width: 100%; border-collapse: collapse; font-size: 18px;">
            <thead>
              <tr style="background: #f3f4f6;">
                <th style="border: 1px solid #000; padding: 10px; text-align: left; font-size: 18px;">Miejsce</th>
                <th style="border: 1px solid #000; padding: 10px; text-align: left; font-size: 18px;">Imię i nazwisko</th>
                <th style="border: 1px solid #000; padding: 10px; text-align: left; font-size: 18px;">Strona</th>
              </tr>
            </thead>
            <tbody>
              ${guestsWithPositions
                .map(
                  (g) => `
                <tr>
                  <td style="border: 1px solid #000; padding: 10px; font-size: 20px; font-weight: bold;">${g.position_index}</td>
                  <td style="border: 1px solid #000; padding: 10px; font-size: 22px; font-weight: bold;">${g.full_name}</td>
                  <td style="border: 1px solid #000; padding: 10px; font-size: 18px;">${g.side === "groom" ? "Pan Młody" : "Panna Młoda"}</td>
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        `;
      }

      exportContainer.appendChild(guestsList);

      document.body.appendChild(exportContainer);

      const canvas = await html2canvas(exportContainer, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: true,
        logging: false,
      });

      document.body.removeChild(exportContainer);

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("portrait", "mm", "a4");
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      let heightLeft = imgHeight;
      let position = 10;

      pdf.addImage(imgData, "PNG", 10, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight + 10;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 10, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      const fileName = `stol-${selectedTable.number}.pdf`;
      pdf.save(fileName);

      setSuccessMsg("PDF wygenerowany pomyślnie!");
    } catch (err) {
      console.error("Export error:", err);
      setServerError("Nie udało się wyeksportować PDF.");
    }
  };

  const handleSeatClick = (positionIndex: number, guest: GuestAtTable | null) => {
    setModalPositionIndex(positionIndex);
    setModalCurrentGuest(guest);
    setModalOpen(true);
  };

  const startEditTable = (table: Table) => {
    setEditingTableId(table.id);
    setValue("number", table.number);
    setValue("name", table.name);
    setValue("shape", table.shape);
    setValue("capacity", table.capacity);
    setShowForm(true);
    setServerError(null);
    setSuccessMsg(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const cancelEdit = () => {
    setEditingTableId(null);
    setShowForm(false);
    reset();
    setServerError(null);
  };

  const handleSelectEvent = (event: Event) => {
    setActiveEvent({ id: event.id, name: event.name });
    setShowEventSelector(false);
    setSelectedTable(null);
    setTableGuests([]);
    setShowForm(false);
    cancelEdit();
  };

  const getNextTableNumber = () => {
    if (tables.length === 0) return 1;
    return Math.max(...tables.map((t) => t.number)) + 1;
  };

  const openNewTableForm = () => {
    setEditingTableId(null);
    reset({
      number: getNextTableNumber(),
      name: "",
      shape: "rectangular",
      capacity: 10,
    });
    setShowForm(true);
    setServerError(null);
    setSuccessMsg(null);
  };

  const assignedGuestIds = useMemo(() => {
    const ids = new Set<string>();
    tableGuests.forEach((g) => ids.add(g.id));
    return ids;
  }, [tableGuests]);

  const occupiedSeats = tableGuests.filter(
    (g) => g.position_index !== null && g.position_index !== undefined
  ).length;

  if (!activeEvent) {
    return (
      <>
        <PageTitle title="Stoły" />
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🍽️</div>
          <h2>Wybierz wydarzenie</h2>
          <p>Aby zarządzać stołami, najpierw wybierz aktywne wydarzenie.</p>
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

  return (
    <>
      <PageTitle title="Stoły" />

      {/* Heading */}
      <div className={styles.eventHeader}>
        <div className={styles.eventInfo}>
          <span className={styles.eventIcon}>🍽️</span>
          <div>
            <strong>{activeEvent.name}</strong>
            <p className={styles.eventSubtitle}>{tables.length} stołów</p>
          </div>
        </div>
        <div className={styles.eventActions}>
          <button
            className={styles.btnSecondary}
            onClick={() => setShowEventSelector(!showEventSelector)}
          >
            Zmień wydarzenie
          </button>
          <button className={styles.btnSmallDanger} onClick={() => setActiveEvent(null)}>
            Wyczyść
          </button>
        </div>
      </div>

      {/* Event Selector */}
      {showEventSelector && (
        <div className={styles.eventSelector}>
          <h3>Wybierz inne wydarzenie:</h3>
          <div className={styles.eventGrid}>
            {events.map((event) => (
              <button
                key={event.id}
                className={`${styles.eventCard} ${
                  event.id === activeEvent.id ? styles.eventCardActive : ""
                }`}
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

      {serverError && <div className={styles.alertError}>{serverError}</div>}
      {successMsg && <div className={styles.alertSuccess}>{successMsg}</div>}

      <div className={styles.wrapper}>
        {/* SIDEBAR */}
        <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>
            <h2 className={styles.sidebarTitle}>Stoły ({tables.length})</h2>
            <button className={styles.btnAddTable} onClick={openNewTableForm}>
              + Dodaj stół
            </button>
          </div>

          {/* Form */}
          {showForm && (
            <div className={styles.tableForm}>
              <h3>{editingTableId ? "Edytuj stół" : "Nowy stół"}</h3>
              <form onSubmit={handleSubmit(onSubmitTable)} className={styles.form}>
                <div className={styles.row}>
                  <div className={styles.fieldSmall}>
                    <label className={styles.label}>Numer</label>
                    <input
                      type="number"
                      className={styles.input}
                      min={1}
                      {...register("number", { required: true, valueAsNumber: true })}
                    />
                  </div>
                  <div className={styles.fieldSmall}>
                    <label className={styles.label}>Miejsc</label>
                    <input
                      type="number"
                      className={styles.input}
                      min={1}
                      max={100}
                      {...register("capacity", { required: true, valueAsNumber: true })}
                    />
                  </div>
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>Nazwa stołu</label>
                  <input
                    type="text"
                    className={styles.input}
                    placeholder='np. "Stół główny"'
                    {...register("name")}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>Kształt</label>
                  <select className={styles.input} {...register("shape")}>
                    {Object.entries(SHAPE_LABELS).map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div className={styles.formActions}>
                  <button type="submit" className={styles.btn} disabled={isSubmitting}>
                    {isSubmitting
                      ? "Zapisywanie..."
                      : editingTableId
                        ? "Zaktualizuj"
                        : "Dodaj"}
                  </button>
                  <button
                    type="button"
                    className={styles.btnSecondary}
                    onClick={cancelEdit}
                  >
                    Anuluj
                  </button>
                </div>
              </form>
              <div className={styles.previewTitle}>
                Podgląd: {SHAPE_LABELS[watchedShape]}, {watchedCapacity} miejsc
              </div>
              <TableVisualization
                shape={watchedShape}
                capacity={watchedCapacity}
                guests={[]}
                compact
              />
            </div>
          )}

          {loading && <p className={styles.infoMsg}>Ładowanie...</p>}

          {/* List of tables */}
          <div className={styles.tablesList}>
            {tables.map((table) => (
              <div
                key={table.id}
                className={`${styles.tableItem} ${
                  selectedTable?.id === table.id ? styles.tableItemActive : ""
                }`}
              >
                <button
                  className={styles.tableItemMain}
                  onClick={() => loadTableDetails(table.id)}
                >
                  <div className={styles.tableItemInfo}>
                    <span className={styles.tableNumber}>
                      {table.shape === "round" ? "🟠" : "🟫"} Stół {table.number}
                    </span>
                    {table.name && (
                      <span className={styles.tableName}>- {table.name}</span>
                    )}
                    <span className={styles.tableCapacity}>
                      ({table.capacity} miejsc)
                    </span>
                  </div>
                  <span className={styles.tableShape}>
                    {SHAPE_LABELS[table.shape]}
                  </span>
                </button>
                <div className={styles.tableItemActions}>
                  <button
                    className={styles.btnTiny}
                    onClick={(e) => {
                      e.stopPropagation();
                      startEditTable(table);
                    }}
                  >
                    ✏️
                  </button>
                  <button
                    className={styles.btnTinyDanger}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteTable(table.id);
                    }}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* MAIN - Visualization */}
        <div className={styles.mainArea} ref={tableRef}>
          {selectedTable ? (
            <>
              <div className={styles.tableDetailHeader}>
                <div className={styles.tableDetailHeaderTop}>
                  <div>
                    <h2>
                      {selectedTable.shape === "round" ? "🟠" : "🟫"} Stół{" "}
                      {selectedTable.number}
                      {selectedTable.name && ` - ${selectedTable.name}`}
                    </h2>
                    <p>
                      {SHAPE_LABELS[selectedTable.shape]} · {selectedTable.capacity}{" "}
                      miejsc · {occupiedSeats} zajętych
                    </p>
                  </div>
                  <button className={styles.btnExport} onClick={exportToPDF}>
                    📄 Eksportuj PDF
                  </button>
                </div>
                <p className={styles.clickHint}>
                  💡 Kliknij w wybrane miejsce, aby przypisać lub zmienić gościa
                </p>
              </div>

              <div className={styles.visualizationContainer} id="table-visualization">
                {loadingTableGuests ? (
                  <p className={styles.infoMsg}>Ładowanie...</p>
                ) : (
                  <TableVisualization
                    shape={selectedTable.shape}
                    capacity={selectedTable.capacity}
                    guests={tableGuests}
                    onSeatClick={handleSeatClick}
                  />
                )}
              </div>

              <div className={styles.legend} id="table-legend">
                <span className={styles.legendItem}>
                  <span className={styles.legendSeat}></span> Wolne
                </span>
                <span className={styles.legendItem}>
                  <span
                    className={`${styles.legendSeat} ${styles.legendOccupied}`}
                  ></span>{" "}
                  Zajęte
                </span>
              </div>
            </>
          ) : (
            <div className={styles.noTableSelected}>
              <div className={styles.noTableIcon}>🍽️</div>
              <h3>Wybierz stół z listy</h3>
              <p>
                Kliknij na stół po lewej stronie, aby zobaczyć jego wizualizację i
                zarządzać rozmieszczeniem gości.
              </p>
              {tables.length === 0 && (
                <button className={styles.btn} onClick={openNewTableForm}>
                  + Dodaj pierwszy stół
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* MODAL */}
      {modalOpen && selectedTable && (
        <GuestAssignmentModal
          positionIndex={modalPositionIndex}
          currentGuest={modalCurrentGuest}
          unassignedGuests={unassignedGuests}
          assignedGuestIds={assignedGuestIds}
          tableShape={selectedTable.shape}
          onAssign={assignGuestToPosition}
          onRemove={removeGuestFromPosition}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}