import { Link } from "react-router-dom";
import PageTitle from "../components/common/PageTitle";
import styles from "./DashboardPage.module.css";

const SECTIONS = [
  {
    to: "/event",
    icon: "💒",
    title: "Wydarzenie",
    desc: "Ustal datę, miejsce i harmonogram dnia ślubu.",
  },
  {
    to: "/guests",
    icon: "👥",
    title: "Goście",
    desc: "Twórz listę gości, zaznaczaj statusy, diety i eksportuj do CSV.",
  },
  {
    to: "/tables",
    icon: "🍽️",
    title: "Stoły",
    desc: "Zaplanuj rozsadzenie gości i pobierz układ w PDF.",
  },
  {
    to: "/invitations",
    icon: "💌",
    title: "Zaproszenia",
    desc: "Projektuj i śledź zaproszenia oraz odpowiedzi gości.",
  },
  {
    to: "/finances",
    icon: "💰",
    title: "Finanse",
    desc: "Kontroluj budżet weselny – przychody, wydatki, bilans.",
  },
];

export default function DashboardPage() {
  return (
    <>
      <PageTitle title="Strona Główna" />

      <div className={styles.wrapper}>
        <div className={styles.hero}>
          <h1 className={styles.heading}>Witaj w Wedding Planner 💍</h1>
          <p className={styles.sub}>
            Wybierz sekcję, aby rozpocząć zarządzanie swoim weselem.
          </p>
        </div>

        <div className={styles.grid}>
          {SECTIONS.map((section) => (
            <Link to={section.to} key={section.to} className={styles.card}>
              <span className={styles.cardIcon}>{section.icon}</span>
              <h2 className={styles.cardTitle}>{section.title}</h2>
              <p className={styles.cardDesc}>{section.desc}</p>
            </Link>
          ))}

          <Link to="/account" className={`${styles.card} ${styles.cardAccount}`}>
            <span className={styles.cardIcon}>👤</span>
            <h2 className={styles.cardTitle}>Moje konto</h2>
            <p className={styles.cardDesc}>
              Zarządzaj profilem i ustawieniami konta.
            </p>
          </Link>
        </div>
      </div>
    </>
  );
}