import { useState, useEffect, useMemo, useRef } from "react";
import type { Guest } from "../../features/guests/guests.types";
import type { GuestAtTable, TableShape } from "../../features/tables/tables.types";
import styles from "./GuestAssignmentModal.module.css";

interface GuestAssignmentModalProps {
  positionIndex: number;
  currentGuest: GuestAtTable | null;
  unassignedGuests: Guest[];
  assignedGuestIds: Set<string>;
  tableShape: TableShape;
  onAssign: (guestId: string) => void;
  onRemove: (guestId: string) => void;
  onClose: () => void;
}

export default function GuestAssignmentModal({
  positionIndex,
  currentGuest,
  unassignedGuests,
  assignedGuestIds,
  tableShape,
  onAssign,
  onRemove,
  onClose,
}: GuestAssignmentModalProps) {
  const [search, setSearch] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTimeout(() => searchInputRef.current?.focus(), 100);
  }, []);

  const availableGuests = useMemo(() => {
    const searchLower = search.toLowerCase().trim();
    return unassignedGuests.filter((guest) => {
      if (assignedGuestIds.has(guest.id)) {
        return false;
      }
      if (searchLower && !guest.full_name.toLowerCase().includes(searchLower)) {
        return false;
      }
      return true;
    });
  }, [unassignedGuests, search, assignedGuestIds]);

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && availableGuests.length === 1 && search.trim()) {
      e.preventDefault();
      onAssign(availableGuests[0].id);
    }
  };

  const getSideLabel = (guest: Guest) => {
    switch (guest.side) {
      case "groom": return "🤵 Pan Młody";
      case "bride": return "👰 Panna Młoda";
      default: return guest.side;
    }
  };

  const getStatusIcon = (guest: Guest) => {
    switch (guest.confirmation_status) {
      case "confirmed": return "✅";
      case "pending": return "⏳";
      case "rejected": return "❌";
      default: return "";
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Heading */}
        <div className={styles.modalHeader}>
          <h3>
            Miejsce #{positionIndex + 1}
            <span className={styles.positionHint}>
              {tableShape === "rectangular" && (
                positionIndex < Math.ceil(20 / 2) ? " (lewa strona)" : " (prawa strona)"
              )}
            </span>
          </h3>
          <button className={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Current guest */}
        {currentGuest ? (
          <div className={styles.currentGuest}>
            <div className={styles.currentGuestInfo}>
              <div className={styles.currentGuestAvatar}>
                {currentGuest.full_name.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className={styles.currentGuestName}>{currentGuest.full_name}</div>
                <div className={styles.currentGuestDetails}>
                  {currentGuest.guest_type === "adult" ? "Dorosły" : "Dziecko"}
                  {" · "}
                  {currentGuest.side === "groom" ? "Pan Młody" : "Panna Młoda"}
                  {" · "}
                  {currentGuest.confirmation_status === "confirmed" ? "Potwierdzony" : 
                   currentGuest.confirmation_status === "pending" ? "Oczekuje" : "Odrzucony"}
                </div>
              </div>
            </div>
            <button
              className={styles.removeBtn}
              onClick={() => onRemove(currentGuest.id)}
            >
              Usuń z miejsca
            </button>
          </div>
        ) : (
          <div className={styles.emptySeat}>
            <p>Miejsce wolne</p>
            <p className={styles.emptyHint}>Wyszukaj gościa poniżej aby przypisać</p>
          </div>
        )}

        {/* Search */}
        <div className={styles.searchWrapper}>
          <input
            ref={searchInputRef}
            type="text"
            className={styles.searchInput}
            placeholder="🔍 Szukaj po imieniu i nazwisku..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
        </div>

        {/* Guests list */}
        <div className={styles.guestsList}>
          {availableGuests.length === 0 ? (
            <p className={styles.noResults}>
              {search ? "Brak pasujących gości" : "Brak dostępnych nieprzypisanych gości"}
            </p>
          ) : (
            <>
              <p className={styles.resultsCount}>
                Nieprzypisanych gości: {availableGuests.length}
              </p>
              {availableGuests.slice(0, 50).map((guest) => (
                  <button
                    key={guest.id}
                    className={styles.guestItem}
                    onClick={() => {
                      onAssign(guest.id);
                      onClose();
                    }}
                  >
                  <div className={styles.guestAvatar}>
                    {guest.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div className={styles.guestInfo}>
                    <div className={styles.guestName}>{guest.full_name}</div>
                    <div className={styles.guestMeta}>
                      {guest.guest_type === "adult" ? "👤" : "👶"} {getSideLabel(guest)} {getStatusIcon(guest)}
                    </div>
                  </div>
                </button>
              ))}
              {availableGuests.length > 50 && (
                <p className={styles.moreHint}>
                  ...i {availableGuests.length - 50} więcej (zawęź wyszukiwanie)
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}