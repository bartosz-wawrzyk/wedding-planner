import { Link, Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import PageTitle from "../components/common/PageTitle";
import styles from "./LandingPage.module.css";

export default function LandingPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className={styles.page}>
      <PageTitle title="WeddingPlanner – zaplanuj wymarzony ślub" />
      <div className={styles.hero}>
        <div className={styles.card}>
          <div className={styles.logoWrapper}>
            <span className={styles.logoIcon}>💍</span>
            <h1 className={styles.logoText}>WeddingPlanner</h1>
          </div>

          <h2 className={styles.heading}>Zaplanuj swój wymarzony ślub bez stresu</h2>
          <p className={styles.subtitle}>
            Zarządzaj gośćmi, stołami, zaproszeniami i budżetem – wszystko w jednym miejscu.
          </p>

          <div className={styles.actions}>
            <Link to="/login" className={styles.btnPrimary}>
              Zaloguj się
            </Link>
            <Link to="/register" className={styles.btnSecondary}>
              Zarejestruj się
            </Link>
          </div>

          <section className={styles.features}>
            <h3 className={styles.featuresTitle}>Co znajdziesz w WeddingPlanner?</h3>
            <div className={styles.grid}>
              <div className={styles.featureCard}>
                <span className={styles.featureIcon}>👥</span>
                <h4 className={styles.featureName}>Lista gości</h4>
                <p className={styles.featureDesc}>
                  Twórz pełną listę gości z możliwością eksportu do CSV. Zaznaczaj status
                  zaproszenia, zakwaterowanie, diety i dane kontaktowe.
                </p>
              </div>

              <div className={styles.featureCard}>
                <span className={styles.featureIcon}>💰</span>
                <h4 className={styles.featureName}>Finanse</h4>
                <p className={styles.featureDesc}>
                  Pełna kontrola nad budżetem weselnym. Śledź przychody i wydatki,
                  analizuj koszty i trzymaj wszystko pod kontrolą.
                </p>
              </div>

              <div className={styles.featureCard}>
                <span className={styles.featureIcon}>🍽️</span>
                <h4 className={styles.featureName}>Planer stołów</h4>
                <p className={styles.featureDesc}>
                  Rozmieść gości przy stołach, pobierz układ w formacie PDF. W prosty
                  sposób zdecyduj, kto gdzie siedzi.
                </p>
              </div>

              <div className={styles.featureCard}>
                <span className={styles.featureIcon}>💌</span>
                <h4 className={styles.featureName}>Zaproszenia</h4>
                <p className={styles.featureDesc}>
                  Twórz i personalizuj zaproszenia ślubne. Zarządzaj ich wysyłką i
                  śledź odpowiedzi gości.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}