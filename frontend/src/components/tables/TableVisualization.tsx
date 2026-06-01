import type { TableShape, GuestAtTable } from "../../features/tables/tables.types";
import styles from "./TableVisualization.module.css";

interface TableVisualizationProps {
  shape: TableShape;
  capacity: number;
  guests: GuestAtTable[];
  compact?: boolean;
  onSeatClick?: (positionIndex: number, guest: GuestAtTable | null) => void;
}

export default function TableVisualization({
  shape,
  capacity,
  guests,
  compact = false,
  onSeatClick,
}: TableVisualizationProps) {
  const guestsByPosition = new Map<number, GuestAtTable>();
  
  guests.forEach((guest) => {
    if (guest.position_index !== null && guest.position_index !== undefined) {
      const zeroBasedIndex = guest.position_index - 1;
      guestsByPosition.set(zeroBasedIndex, guest);
    }
  });

  const renderRoundTable = () => {
    const radius = compact ? 40 : 46;
    const tableSize = compact ? "58%" : "48%";
    const seatSize = compact ? 30 : 34;

    const seats = Array.from({ length: capacity }, (_, i) => {
      const angle = (360 / capacity) * i - 90;
      const x = 50 + radius * Math.cos((angle * Math.PI) / 180);
      const y = 50 + radius * Math.sin((angle * Math.PI) / 180);
      const guest = guestsByPosition.get(i) || null;

      return (
        <div
          key={i}
          className={`${styles.roundSeat} ${
            guest ? styles.seatOccupied : styles.seatFree
          } ${onSeatClick ? styles.seatClickable : ""}`}
          style={{
            width: `${seatSize}px`,
            height: `${seatSize}px`,
            left: `${x}%`,
            top: `${y}%`,
          }}
          onClick={() => onSeatClick?.(i, guest)}
          title={guest ? guest.full_name : `Miejsce ${i + 1} - kliknij by dodać gościa`}
        >
          {guest ? (
            <span className={styles.seatName}>{guest.full_name}</span>
          ) : (
            <span className={styles.seatNumber}>{i + 1}</span>
          )}
        </div>
      );
    });

    return (
      <div className={styles.roundContainer}>
        <div
          className={styles.roundTable}
          style={{ width: tableSize, height: tableSize }}
        >
          <span className={styles.tableLabel}>{capacity} os.</span>
        </div>
        {seats}
      </div>
    );
  };

  const renderRectangularTable = () => {
    const leftCount = Math.ceil(capacity / 2);
    const rightCount = capacity - leftCount;

    const seatWidth = compact ? "90%" : "85%";
    const seatHeight = compact ? 32 : 38;

    return (
      <div className={styles.rectangularVerticalContainer}>
        {/* LEFT SIDE */}
        <div className={styles.rectSide}>
          {Array.from({ length: leftCount }, (_, i) => {
            const positionIndex = i;
            const guest = guestsByPosition.get(positionIndex) || null;

            return (
              <div
                key={`left-${i}`}
                className={`${styles.rectSeatVertical} ${
                  guest ? styles.seatOccupied : styles.seatFree
                } ${onSeatClick ? styles.seatClickable : ""}`}
                style={{
                  width: seatWidth,
                  minHeight: `${seatHeight}px`,
                }}
                onClick={() => onSeatClick?.(positionIndex, guest)}
                title={guest ? guest.full_name : `Miejsce ${positionIndex + 1} - kliknij by dodać gościa`}
              >
                {guest ? (
                  <span className={styles.seatName}>{guest.full_name}</span>
                ) : (
                  <span className={styles.seatNumber}>{positionIndex + 1}</span>
                )}
              </div>
            );
          })}
        </div>

        {/* TABLE */}
        <div className={styles.rectTableVertical}>
          <span className={styles.tableLabelVertical}>
            {capacity}
            <br />
            os.
          </span>
        </div>

        {/* RIGHT SIDE */}
        <div className={styles.rectSide}>
          {Array.from({ length: rightCount }, (_, i) => {
            const positionIndex = leftCount + i;
            const guest = guestsByPosition.get(positionIndex) || null;

            return (
              <div
                key={`right-${i}`}
                className={`${styles.rectSeatVertical} ${
                  guest ? styles.seatOccupied : styles.seatFree
                } ${onSeatClick ? styles.seatClickable : ""}`}
                style={{
                  width: seatWidth,
                  minHeight: `${seatHeight}px`,
                }}
                onClick={() => onSeatClick?.(positionIndex, guest)}
                title={guest ? guest.full_name : `Miejsce ${positionIndex + 1} - kliknij by dodać gościa`}
              >
                {guest ? (
                  <span className={styles.seatName}>{guest.full_name}</span>
                ) : (
                  <span className={styles.seatNumber}>{positionIndex + 1}</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return shape === "round" ? renderRoundTable() : renderRectangularTable();
}