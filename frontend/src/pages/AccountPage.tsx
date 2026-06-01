import PageTitle from "../components/common/PageTitle";
import styles from "./PlaceholderPage.module.css";

export default function AccountPage() {
  return (
    <>
      <PageTitle title="Moje konto" />
      <div className={styles.wrapper}>
        <h1 className={styles.heading}>👤 Moje konto</h1>
        <p className={styles.sub}>Ustawienia konta i profilu — wkrótce dostępne.</p>
      </div>
    </>
  );
}